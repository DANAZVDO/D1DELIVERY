from django.urls import path
from . import views

urlpatterns = [
    path("r/<slug:slug>/", views.menu_view, name="menu"),
    path("r/<slug:slug>/cart/", views.cart_view, name="cart"),
    path("r/<slug:slug>/cart/add/<int:item_id>/", views.cart_add, name="cart_add"),
    path("r/<slug:slug>/cart/remove/<int:item_id>/", views.cart_remove, name="cart_remove"),
    path("r/<slug:slug>/cart/update/<int:item_id>/", views.cart_update, name="cart_update"),
    path("r/<slug:slug>/checkout/", views.checkout_view, name="checkout"),
    path("r/<slug:slug>/pedido/<int:order_id>/", views.order_detail_view, name="order_detail"),
    path("r/<slug:slug>/pedido/<int:order_id>/pix/", views.order_pix_view, name="order_pix"),
    path("r/<slug:slug>/pedido/<int:order_id>/upload-comprovante/", views.order_upload_proof, name="order_upload_proof"),

    path("painel/login/", views.dashboard_login, name="dashboard_login"),
    path("painel/logout/", views.dashboard_logout, name="dashboard_logout"),
    path("painel/", views.dashboard_home, name="dashboard_home"),
    path("painel/pedidos/", views.dashboard_orders, name="dashboard_orders"),
    path("painel/pedidos/<int:order_id>/", views.dashboard_order_detail, name="dashboard_order_detail"),
    path("painel/pedidos/<int:order_id>/status/", views.dashboard_order_status, name="dashboard_order_status"),
    path("painel/pedidos/<int:order_id>/comprovante/", views.dashboard_order_proof, name="dashboard_order_proof"),
    path("painel/cardapio/", views.dashboard_menu, name="dashboard_menu"),
    path("painel/cardapio/item/<int:item_id>/", views.dashboard_menu_item, name="dashboard_menu_item"),
    path("painel/cardapio/item/<int:item_id>/toggle/", views.dashboard_menu_item_toggle, name="dashboard_menu_item_toggle"),
    path("painel/configuracoes/", views.dashboard_settings, name="dashboard_settings"),
    path("painel/faturamento/", views.dashboard_billing, name="dashboard_billing"),

    path("conta/cadastro/", views.customer_register, name="customer_register"),
    path("conta/login/", views.customer_login, name="customer_login"),
    path("conta/sair/", views.customer_logout, name="customer_logout"),
    path("minha-conta/", views.customer_orders, name="customer_orders"),
    path("minha-conta/editar/", views.customer_profile_edit, name="customer_profile_edit"),
    path("minha-conta/pedir-novamente/<int:order_id>/", views.customer_reorder, name="customer_reorder"),

    path("", views.landing_page, name="landing"),
]
