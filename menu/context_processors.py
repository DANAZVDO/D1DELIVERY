from decimal import Decimal


def cart_context(request):
    cart = {}
    restaurant_slug = ""
    if hasattr(request, "session"):
        cart = request.session.get("cart", {})
        restaurant_slug = request.session.get("restaurant_slug", "")

    total_items = 0
    cart_items = []
    total_price = Decimal("0")

    if restaurant_slug and cart:
        cart_items = list(cart.values())
        total_items = sum(item.get("quantity", 0) for item in cart_items)
        for item in cart_items:
            try:
                price = Decimal(str(item.get("price", "0")))
                qty = int(item.get("quantity", 0))
                total_price += price * qty
            except (ValueError, TypeError):
                pass

    return {
        "cart_total_items": total_items,
        "cart_total_price": total_price,
        "cart_items": cart_items,
    }
