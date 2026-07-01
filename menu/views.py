import json
import base64
from decimal import Decimal
from io import BytesIO

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Sum, Count
from django.core.files.base import ContentFile
from django.core.serializers.json import DjangoJSONEncoder

from .models import Restaurant, Category, MenuItem, Order, OrderItem, Commission, CustomerProfile, DeliveryZone
from .forms import CheckoutForm
from .pix import generate_pix


def landing_page(request):
    return render(request, "menu/landing.html")


def get_cart(request):
    cart = request.session.get("cart", {})
    restaurant_slug = request.session.get("restaurant_slug", "")
    return cart, restaurant_slug


def save_cart(request, cart, restaurant_slug):
    request.session["cart"] = cart
    request.session["restaurant_slug"] = restaurant_slug
    request.session.modified = True


def menu_view(request, slug):
    restaurant = get_object_or_404(Restaurant, slug=slug, is_active=True)
    categories = restaurant.categories.prefetch_related("items").all()

    cart, cart_slug = get_cart(request)

    if cart_slug and cart_slug != slug:
        cart = {}
        cart_slug = slug
        save_cart(request, cart, cart_slug)

    if not cart_slug:
        save_cart(request, cart, slug)

    cart_total = 0
    cart_count = 0
    cart_items_list = {}
    if cart and cart_slug == slug:
        cart_items_list = cart
        cart_total = sum(
            Decimal(str(item.get("price", 0))) * item.get("quantity", 0)
            for item in cart.values()
        )
        cart_count = sum(item.get("quantity", 0) for item in cart.values())

    context = {
        "restaurant": restaurant,
        "categories": categories,
        "cart": cart_items_list,
        "cart_total": cart_total,
        "cart_count": cart_count,
        "is_open": restaurant.is_open,
    }
    return render(request, "menu/menu.html", context)


@require_POST
def cart_add(request, slug, item_id):
    restaurant = get_object_or_404(Restaurant, slug=slug, is_active=True)
    item = get_object_or_404(MenuItem, id=item_id, category__restaurant=restaurant, is_available=True)

    cart, cart_slug = get_cart(request)

    if cart_slug != slug:
        cart = {}
        cart_slug = slug

    item_key = str(item_id)
    if item_key in cart:
        cart[item_key]["quantity"] += 1
    else:
        image_url = item.image.url if item.image else ""
        cart[item_key] = {
            "id": item.id,
            "name": item.name,
            "price": str(item.price),
            "quantity": 1,
            "image_url": image_url,
        }

    save_cart(request, cart, slug)

    total = sum(
        Decimal(v.get("price", 0)) * v.get("quantity", 0)
        for v in cart.values()
    )
    count = sum(v.get("quantity", 0) for v in cart.values())

    return JsonResponse({
        "success": True,
        "cart_total": str(total),
        "cart_count": count,
        "item_name": item.name,
    })


@require_POST
def cart_remove(request, slug, item_id):
    cart, cart_slug = get_cart(request)
    item_key = str(item_id)

    if cart_slug == slug and item_key in cart:
        del cart[item_key]
        save_cart(request, cart, slug)

    total = sum(
        Decimal(v.get("price", 0)) * v.get("quantity", 0)
        for v in cart.values()
    )
    count = sum(v.get("quantity", 0) for v in cart.values())

    return JsonResponse({
        "success": True,
        "cart_total": str(total),
        "cart_count": count,
    })


@require_POST
def cart_update(request, slug, item_id):
    cart, cart_slug = get_cart(request)
    item_key = str(item_id)

    if cart_slug != slug or item_key not in cart:
        return JsonResponse({"success": False, "error": "Item não encontrado"}, status=404)

    try:
        data = json.loads(request.body)
        quantity = int(data.get("quantity", 1))
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"success": False, "error": "Quantidade inválida"}, status=400)

    if quantity <= 0:
        del cart[item_key]
    else:
        cart[item_key]["quantity"] = min(quantity, 20)

    save_cart(request, cart, slug)

    total = sum(
        Decimal(v.get("price", 0)) * v.get("quantity", 0)
        for v in cart.values()
    )
    count = sum(v.get("quantity", 0) for v in cart.values())

    return JsonResponse({
        "success": True,
        "cart_total": str(total),
        "cart_count": count,
    })


def cart_view(request, slug):
    restaurant = get_object_or_404(Restaurant, slug=slug, is_active=True)
    cart, cart_slug = get_cart(request)

    items_with_meta = []
    cart_total = Decimal("0")
    cart_count = 0

    if cart_slug == slug and cart:
        cart_count = sum(v.get("quantity", 0) for v in cart.values())
        for item_key, item_data in cart.items():
            try:
                menu_item = MenuItem.objects.get(id=int(item_key), category__restaurant=restaurant)
                item_total = menu_item.price * item_data["quantity"]
                cart_total += item_total
                items_with_meta.append({
                    "cart_key": item_key,
                    "item": menu_item,
                    "quantity": item_data["quantity"],
                    "total": item_total,
                })
            except MenuItem.DoesNotExist:
                continue

    return render(request, "menu/cart.html", {
        "restaurant": restaurant,
        "cart_items": items_with_meta,
        "cart_total": cart_total,
        "cart_count": cart_count,
    })


def checkout_view(request, slug):
    restaurant = get_object_or_404(Restaurant, slug=slug, is_active=True)
    cart, cart_slug = get_cart(request)

    cart_items = []
    cart_total = Decimal("0")

    if cart_slug != slug or not cart:
        return redirect("menu", slug=slug)

    for item_key, item_data in cart.items():
        try:
            menu_item = MenuItem.objects.get(id=int(item_key), category__restaurant=restaurant)
            item_total = menu_item.price * item_data["quantity"]
            cart_total += item_total
            cart_items.append({
                "cart_key": item_key,
                "menu_item": menu_item,
                "quantity": item_data["quantity"],
                "total": item_total,
            })
        except MenuItem.DoesNotExist:
            continue

    if not cart_items:
        return redirect("menu", slug=slug)

    zones = restaurant.delivery_zones.filter(is_active=True).order_by("order", "name")
    has_zones = zones.exists()

    if request.method == "POST":
        form = CheckoutForm(request.POST)

        neighborhood_choices = [(z.name, f"{z.name} — R$ {z.fee:.2f}" if z.fee > 0 else f"{z.name} — Grátis") for z in zones]
        form.fields["customer_neighborhood"].choices = [("", "Selecione seu bairro")] + neighborhood_choices
        form.fields["customer_neighborhood"].required = bool(has_zones)

        if form.is_valid():
            order = form.save(commit=False)
            order.restaurant = restaurant
            order.subtotal = cart_total

            # Calculate delivery fee from zone
            if order.delivery_type == "pickup":
                order.delivery_fee = Decimal("0")
            elif order.customer_neighborhood and has_zones:
                zone = zones.filter(name=order.customer_neighborhood).first()
                order.delivery_fee = zone.fee if zone else restaurant.delivery_fee
            else:
                order.delivery_fee = restaurant.delivery_fee

            order.total = order.subtotal + order.delivery_fee

            if request.user.is_authenticated and hasattr(request.user, "customer_profile"):
                order.customer_profile = request.user.customer_profile

            order.save()

            for ci in cart_items:
                OrderItem.objects.create(
                    order=order,
                    menu_item=ci["menu_item"],
                    name=ci["menu_item"].name,
                    price=ci["menu_item"].price,
                    quantity=ci["quantity"],
                )

            pix_data = generate_pix(
                key=restaurant.pix_key or "11999999999",
                merchant_name=restaurant.merchant_name or restaurant.name,
                merchant_city=restaurant.merchant_city,
                amount=float(order.total),
            )
            order.pix_code = pix_data["payload"]
            qr_buffer = pix_data["qr_image"]
            order.save()

            Commission.objects.create(
                restaurant=restaurant,
                order=order,
                amount=order.calculate_commission(),
            )

            restaurant.commission_balance = (
                restaurant.commission_balance + order.commission_amount
            )
            restaurant.save(update_fields=["commission_balance"])

            request.session["cart"] = {}
            request.session.modified = True

            return redirect("order_detail", slug=slug, order_id=order.id)
    else:
        initial = {"delivery_type": "delivery" if restaurant.delivery_fee > 0 else "pickup"}
        if request.user.is_authenticated and hasattr(request.user, "customer_profile"):
            profile = request.user.customer_profile
            initial.update({
                "customer_name": request.user.first_name or request.user.username,
                "customer_phone": profile.phone,
                "customer_address": profile.address,
                "customer_complement": profile.complement,
                "customer_neighborhood": profile.neighborhood,
            })
        form = CheckoutForm(initial=initial)

        neighborhood_choices = [(z.name, f"{z.name} — R$ {z.fee:.2f}" if z.fee > 0 else f"{z.name} — Grátis") for z in zones]
        form.fields["customer_neighborhood"].choices = [("", "Selecione seu bairro")] + neighborhood_choices

    return render(request, "menu/checkout.html", {
        "restaurant": restaurant,
        "form": form,
        "cart_items": cart_items,
        "cart_total": cart_total,
        "delivery_fee": restaurant.delivery_fee,
        "zones": zones,
        "has_zones": has_zones,
    })


def order_detail_view(request, slug, order_id):
    restaurant = get_object_or_404(Restaurant, slug=slug, is_active=True)
    order = get_object_or_404(Order, id=order_id, restaurant=restaurant)
    order_items = order.items.all()

    return render(request, "menu/order_detail.html", {
        "restaurant": restaurant,
        "order": order,
        "order_items": order_items,
    })


def order_pix_view(request, slug, order_id):
    restaurant = get_object_or_404(Restaurant, slug=slug, is_active=True)
    order = get_object_or_404(Order, id=order_id, restaurant=restaurant)

    if not order.pix_code:
        pix_data = generate_pix(
            key=restaurant.pix_key or "11999999999",
            merchant_name=restaurant.merchant_name or restaurant.name,
            merchant_city=restaurant.merchant_city,
            amount=float(order.total),
        )
        order.pix_code = pix_data["payload"]
        qr_buffer = pix_data["qr_image"]
        order.save()

    pix_data = generate_pix(
        key=restaurant.pix_key or "11999999999",
        merchant_name=restaurant.merchant_name or restaurant.name,
        merchant_city=restaurant.merchant_city,
        amount=float(order.total),
    )
    qr_base64 = base64.b64encode(pix_data["qr_image"].getvalue()).decode("utf-8")

    return render(request, "menu/order_pix.html", {
        "restaurant": restaurant,
        "order": order,
        "qr_base64": qr_base64,
        "pix_code": order.pix_code,
    })


@require_POST
def order_upload_proof(request, slug, order_id):
    restaurant = get_object_or_404(Restaurant, slug=slug, is_active=True)
    order = get_object_or_404(Order, id=order_id, restaurant=restaurant)

    if order.status != "pending":
        return JsonResponse({"success": False, "error": "Pedido já processado"}, status=400)

    uploaded_file = request.FILES.get("comprovante")
    if not uploaded_file:
        return JsonResponse({"success": False, "error": "Nenhum arquivo enviado"}, status=400)

    order.pix_proof = uploaded_file
    order.save(update_fields=["pix_proof", "updated_at"])

    return JsonResponse({"success": True})


def dashboard_login(request):
    if request.user.is_authenticated and hasattr(request.user, "restaurant"):
        return redirect("dashboard_home")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None and hasattr(user, "restaurant"):
            login(request, user)
            next_url = request.GET.get("next", "dashboard_home")
            return redirect(next_url)
        else:
            messages.error(request, "Usuário ou senha inválidos.")

    return render(request, "menu/dashboard/login.html")


def dashboard_logout(request):
    logout(request)
    return redirect("dashboard_login")


@login_required
def dashboard_home(request):
    restaurant = request.user.restaurant
    if not restaurant.is_active:
        return render(request, "menu/dashboard/inactive.html", {"restaurant": restaurant})

    today = timezone.now().date()
    orders_today = Order.objects.filter(
        restaurant=restaurant, created_at__date=today
    )

    pending = orders_today.filter(status="pending").count()
    in_progress = orders_today.filter(
        status__in=["confirmed", "preparing", "out_for_delivery"]
    ).count()
    delivered = orders_today.filter(status="delivered").count()
    revenue_today = orders_today.filter(status="delivered").aggregate(
        total=Sum("total")
    )["total"] or Decimal("0")

    recent_orders = orders_today.order_by("-created_at")[:10]

    return render(request, "menu/dashboard/index.html", {
        "restaurant": restaurant,
        "pending": pending,
        "in_progress": in_progress,
        "delivered": delivered,
        "revenue_today": revenue_today,
        "recent_orders": recent_orders,
    })


@login_required
def dashboard_orders(request):
    restaurant = request.user.restaurant
    orders = Order.objects.filter(restaurant=restaurant).order_by("-created_at")

    status_filter = request.GET.get("status")
    if status_filter:
        orders = orders.filter(status=status_filter)

    return render(request, "menu/dashboard/orders.html", {
        "restaurant": restaurant,
        "orders": orders,
        "status_filter": status_filter,
        "status_choices": Order.STATUS_CHOICES,
    })


@login_required
def dashboard_order_detail(request, order_id):
    restaurant = request.user.restaurant
    order = get_object_or_404(Order, id=order_id, restaurant=restaurant)
    order_items = order.items.all()

    return render(request, "menu/dashboard/order_detail.html", {
        "restaurant": restaurant,
        "order": order,
        "order_items": order_items,
    })


@require_POST
@login_required
def dashboard_order_status(request, order_id):
    restaurant = request.user.restaurant
    order = get_object_or_404(Order, id=order_id, restaurant=restaurant)

    new_status = request.POST.get("status")
    if new_status not in dict(Order.STATUS_CHOICES):
        return JsonResponse({"success": False, "error": "Status inválido"}, status=400)

    order.status = new_status
    order.save(update_fields=["status", "updated_at"])

    return JsonResponse({"success": True, "status": order.get_status_display()})


@require_POST
@login_required
def dashboard_order_proof(request, order_id):
    restaurant = request.user.restaurant
    order = get_object_or_404(Order, id=order_id, restaurant=restaurant)

    action = request.POST.get("action")
    if action == "approve":
        if order.status == "pending":
            order.status = "confirmed"
            order.save(update_fields=["status", "updated_at"])
            return JsonResponse({"success": True, "message": "Pagamento confirmado"})
    elif action == "reject":
        if order.status == "pending":
            order.status = "cancelled"
            order.save(update_fields=["status", "updated_at"])
            return JsonResponse({"success": True, "message": "Pagamento rejeitado"})

    return JsonResponse({"success": False, "error": "Ação inválida"}, status=400)


@login_required
def dashboard_menu(request):
    restaurant = request.user.restaurant
    categories = restaurant.categories.prefetch_related("items").all()

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "add_category":
            name = request.POST.get("name")
            if name:
                Category.objects.create(restaurant=restaurant, name=name)
                messages.success(request, "Categoria adicionada.")
        elif action == "add_item":
            category_id = request.POST.get("category_id")
            name = request.POST.get("name")
            price = request.POST.get("price")
            category = get_object_or_404(Category, id=category_id, restaurant=restaurant)
            if name and price:
                MenuItem.objects.create(
                    category=category,
                    name=name,
                    price=Decimal(price),
                    description=request.POST.get("description", ""),
                )
                messages.success(request, "Item adicionado.")
        elif action == "edit_item":
            item_id = request.POST.get("item_id")
            item = get_object_or_404(MenuItem, id=item_id, category__restaurant=restaurant)
            item.name = request.POST.get("name", item.name)
            item.price = Decimal(request.POST.get("price", str(item.price)))
            item.description = request.POST.get("description", item.description)
            if request.FILES.get("image"):
                item.image = request.FILES["image"]
            item.save()
            messages.success(request, "Item atualizado.")
        elif action == "delete_item":
            item_id = request.POST.get("item_id")
            item = get_object_or_404(MenuItem, id=item_id, category__restaurant=restaurant)
            item.delete()
            messages.success(request, "Item removido.")
        return redirect("dashboard_menu")

    return render(request, "menu/dashboard/menu.html", {
        "restaurant": restaurant,
        "categories": categories,
    })


@login_required
def dashboard_menu_item(request, item_id):
    restaurant = request.user.restaurant
    item = get_object_or_404(MenuItem, id=item_id, category__restaurant=restaurant)

    if request.method == "POST":
        item.name = request.POST.get("name", item.name)
        item.price = Decimal(request.POST.get("price", str(item.price)))
        item.description = request.POST.get("description", item.description)
        item.category_id = int(request.POST.get("category_id", item.category_id))
        if request.FILES.get("image"):
            item.image = request.FILES["image"]
        item.save()
        messages.success(request, "Item atualizado.")
        return redirect("dashboard_menu")

    categories = restaurant.categories.all()
    return render(request, "menu/dashboard/menu_item_edit.html", {
        "restaurant": restaurant,
        "item": item,
        "categories": categories,
    })


@require_POST
@login_required
def dashboard_menu_item_toggle(request, item_id):
    restaurant = request.user.restaurant
    item = get_object_or_404(MenuItem, id=item_id, category__restaurant=restaurant)
    item.is_available = not item.is_available
    item.save(update_fields=["is_available"])
    return JsonResponse({"success": True, "is_available": item.is_available})


@login_required
def dashboard_settings(request):
    restaurant = request.user.restaurant

    if request.method == "POST":
        action = request.POST.get("action", "")

        if action == "add_zone":
            name = request.POST.get("zone_name", "").strip()
            fee = request.POST.get("zone_fee", "0")
            if name:
                DeliveryZone.objects.create(restaurant=restaurant, name=name, fee=Decimal(fee))
                messages.success(request, f"Bairro '{name}' adicionado.")
            return redirect("dashboard_settings")

        elif action == "delete_zone":
            zone_id = request.POST.get("zone_id")
            DeliveryZone.objects.filter(id=zone_id, restaurant=restaurant).delete()
            messages.success(request, "Bairro removido.")
            return redirect("dashboard_settings")

        restaurant.name = request.POST.get("name", restaurant.name)
        restaurant.pix_key = request.POST.get("pix_key", restaurant.pix_key)
        restaurant.pix_key_type = request.POST.get("pix_key_type", restaurant.pix_key_type)
        restaurant.merchant_name = request.POST.get("merchant_name", restaurant.merchant_name)[:25]
        restaurant.merchant_city = request.POST.get("merchant_city", restaurant.merchant_city)[:15]
        restaurant.delivery_fee = Decimal(request.POST.get("delivery_fee", str(restaurant.delivery_fee)))
        restaurant.min_order = Decimal(request.POST.get("min_order", str(restaurant.min_order)))
        restaurant.is_open = request.POST.get("is_open") == "on"
        restaurant.phone = request.POST.get("phone", restaurant.phone)
        restaurant.address = request.POST.get("address", restaurant.address)
        restaurant.delivery_info = request.POST.get("delivery_info", restaurant.delivery_info)

        if request.FILES.get("logo"):
            restaurant.logo = request.FILES["logo"]

        restaurant.save()
        messages.success(request, "Configurações atualizadas.")
        return redirect("dashboard_settings")

    zones = restaurant.delivery_zones.all()

    return render(request, "menu/dashboard/settings.html", {
        "restaurant": restaurant,
        "zones": zones,
    })


@login_required
def dashboard_billing(request):
    restaurant = request.user.restaurant
    commissions = Commission.objects.filter(restaurant=restaurant).order_by("-created_at")

    total_commission = commissions.aggregate(total=Sum("amount"))["total"] or Decimal("0")
    total_paid = commissions.filter(paid=True).aggregate(total=Sum("amount"))["total"] or Decimal("0")
    total_pending = commissions.filter(paid=False).aggregate(total=Sum("amount"))["total"] or Decimal("0")

    return render(request, "menu/dashboard/billing.html", {
        "restaurant": restaurant,
        "commissions": commissions,
        "total_commission": total_commission,
        "total_paid": total_paid,
        "total_pending": total_pending,
    })


def customer_register(request):
    if request.user.is_authenticated:
        return redirect("customer_orders")

    if request.method == "POST":
        username = request.POST.get("username", "").strip().lower()
        password = request.POST.get("password", "")
        password2 = request.POST.get("password2", "")
        name = request.POST.get("name", "").strip()
        phone = request.POST.get("phone", "").strip()
        address = request.POST.get("address", "").strip()
        complement = request.POST.get("complement", "").strip()
        neighborhood = request.POST.get("neighborhood", "").strip()

        error = None
        if not username or not password or not name or not phone:
            error = "Preencha todos os campos obrigatórios."
        elif password != password2:
            error = "As senhas não conferem."
        elif len(password) < 4:
            error = "A senha deve ter pelo menos 4 caracteres."
        elif User.objects.filter(username=username).exists():
            error = "Este usuário já existe."

        if error:
            messages.error(request, error)
        else:
            user = User.objects.create_user(username=username, password=password, first_name=name)
            CustomerProfile.objects.create(
                user=user, phone=phone, address=address, complement=complement,
                neighborhood=neighborhood
            )
            login(request, user)
            messages.success(request, "Conta criada com sucesso!")
            return redirect("customer_orders")

    return render(request, "menu/customer/register.html")


def customer_login(request):
    if request.user.is_authenticated:
        return redirect("customer_orders")

    if request.method == "POST":
        username = request.POST.get("username", "").strip().lower()
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)

        if user is not None and not hasattr(user, "restaurant"):
            login(request, user)
            next_url = request.GET.get("next", "customer_orders")
            return redirect(next_url)
        else:
            messages.error(request, "Usuário ou senha inválidos.")

    return render(request, "menu/customer/login.html")


def customer_logout(request):
    logout(request)
    return redirect("landing")


@login_required
def customer_orders(request):
    try:
        profile = request.user.customer_profile
    except CustomerProfile.DoesNotExist:
        return redirect("landing")

    orders = Order.objects.filter(customer_profile=profile).order_by("-created_at")

    return render(request, "menu/customer/orders.html", {
        "profile": profile,
        "orders": orders,
    })


@login_required
def customer_profile_edit(request):
    try:
        profile = request.user.customer_profile
    except CustomerProfile.DoesNotExist:
        return redirect("landing")

    if request.method == "POST":
        profile.phone = request.POST.get("phone", profile.phone)
        profile.address = request.POST.get("address", profile.address)
        profile.complement = request.POST.get("complement", profile.complement)
        profile.neighborhood = request.POST.get("neighborhood", profile.neighborhood)
        request.user.first_name = request.POST.get("name", request.user.first_name)
        request.user.save()
        profile.save()
        messages.success(request, "Dados atualizados!")
        return redirect("customer_orders")

    return render(request, "menu/customer/profile_edit.html", {
        "profile": profile,
    })


@login_required
def customer_reorder(request, order_id):
    try:
        profile = request.user.customer_profile
    except CustomerProfile.DoesNotExist:
        return redirect("landing")

    order = get_object_or_404(Order, id=order_id, customer_profile=profile)
    restaurant = order.restaurant

    cart = {}
    for item in order.items.all():
        if item.menu_item and item.menu_item.is_available:
            cart[str(item.menu_item.id)] = {
                "id": item.menu_item.id,
                "name": item.menu_item.name,
                "price": str(item.menu_item.price),
                "quantity": item.quantity,
                "image_url": item.menu_item.image.url if item.menu_item.image else "",
            }

    request.session["cart"] = cart
    request.session["restaurant_slug"] = restaurant.slug
    request.session.modified = True

    return redirect("cart", slug=restaurant.slug)
