from django.contrib import admin
from django.db.models import Sum
from django.utils import timezone
from .models import Restaurant, Category, MenuItem, Order, OrderItem, Commission, CustomerProfile, DeliveryZone


class CategoryInline(admin.TabularInline):
    model = Category
    extra = 0


class MenuItemInline(admin.TabularInline):
    model = MenuItem
    extra = 0


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ["name", "price", "quantity"]


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "plan", "setup_fee", "is_active", "commission_balance", "order_count", "created_at"]
    search_fields = ["name", "slug", "phone"]
    prepopulated_fields = {"slug": ["name"]}
    list_filter = ["plan", "is_active"]
    readonly_fields = ["commission_balance", "created_at", "updated_at"]
    fieldsets = (
        ("Dados do Restaurante", {
            "fields": ("user", "name", "slug", "logo", "phone", "address", "delivery_info", "is_active", "is_open")
        }),
        ("Plano e Cobrança", {
            "fields": ("plan", "trial_start", "plan_start", "setup_fee", "commission_rate", "commission_balance")
        }),
        ("Pagamento PIX", {
            "fields": ("pix_key", "pix_key_type", "merchant_name", "merchant_city")
        }),
        ("Entrega", {
            "fields": ("delivery_fee", "min_order")
        }),
        ("Datas", {
            "fields": ("created_at", "updated_at")
        }),
    )
    inlines = [CategoryInline]

    def order_count(self, obj):
        return obj.orders.count()
    order_count.short_description = "Pedidos"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "restaurant", "item_count", "order"]
    list_filter = ["restaurant"]
    inlines = [MenuItemInline]

    def item_count(self, obj):
        return obj.items.count()
    item_count.short_description = "Itens"


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "restaurant_name", "price", "is_available"]
    list_filter = ["category__restaurant", "category", "is_available"]
    search_fields = ["name"]

    def restaurant_name(self, obj):
        return obj.category.restaurant.name
    restaurant_name.short_description = "Restaurante"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["id", "restaurant", "customer_name", "total", "status", "commission_amount", "created_at"]
    list_filter = ["restaurant", "status", "commission_paid", "created_at"]
    search_fields = ["customer_name", "customer_phone", "id"]
    readonly_fields = ["total", "commission_amount", "created_at", "updated_at"]
    inlines = [OrderItemInline]
    date_hierarchy = "created_at"
    fieldsets = (
        ("Pedido", {
            "fields": ("restaurant", "customer_profile", "customer_name", "customer_phone", "status")
        }),
        ("Entrega", {
            "fields": ("delivery_type", "customer_neighborhood", "customer_address", "customer_complement", "customer_notes")
        }),
        ("Valores", {
            "fields": ("subtotal", "delivery_fee", "total", "commission_amount", "commission_paid")
        }),
        ("PIX", {
            "fields": ("pix_code", "pix_proof")
        }),
        ("Datas", {
            "fields": ("created_at", "updated_at")
        }),
    )


@admin.register(Commission)
class CommissionAdmin(admin.ModelAdmin):
    list_display = ["restaurant", "order_link", "amount", "paid", "created_at"]
    list_filter = ["restaurant", "paid"]
    date_hierarchy = "created_at"

    def order_link(self, obj):
        return f"Pedido #{obj.order.id}"
    order_link.short_description = "Pedido"


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "phone", "address", "total_orders", "created_at"]
    search_fields = ["user__username", "user__first_name", "phone"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(DeliveryZone)
class DeliveryZoneAdmin(admin.ModelAdmin):
    list_display = ["name", "restaurant", "fee", "min_order", "is_active", "order"]
    list_filter = ["restaurant", "is_active"]
    search_fields = ["name"]
    list_editable = ["is_active", "order"]


admin.site.site_header = "D1 Delivery — Administração"
admin.site.site_title = "D1 Delivery Admin"
admin.site.index_title = "Painel de Controle"
