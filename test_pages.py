import os
os.environ["DJANGO_SETTINGS_MODULE"] = "core.settings"
import django
django.setup()

from django.test import RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.middleware import AuthenticationMiddleware
from django.contrib.messages.middleware import MessageMiddleware
from menu.models import Restaurant, Order
import menu.views as v

r = Restaurant.objects.first()
rf = RequestFactory()

def mock_request(path, method="get", post_data=None):
    if method == "post":
        req = rf.post(path, post_data or {})
    else:
        req = rf.get(path)

    mw = SessionMiddleware(lambda req: None)
    mw.process_request(req)
    req.session.save()

    auth = AuthenticationMiddleware(lambda req: None)
    auth.process_request(req)

    msg = MessageMiddleware(lambda req: None)
    msg.process_request(req)

    return req

pages = {
    "Landing (/)": lambda: v.landing_page(mock_request("/")),
    "Menu (r/slug/)": lambda: v.menu_view(mock_request(f"/r/{r.slug}/"), r.slug),
    "Cart (r/slug/cart/)": lambda: v.cart_view(mock_request(f"/r/{r.slug}/cart/"), r.slug),
    "Checkout (r/slug/checkout/)": lambda: v.checkout_view(mock_request(f"/r/{r.slug}/checkout/"), r.slug),
    "Login (painel/login/)": lambda: v.dashboard_login(mock_request("/painel/login/")),
}

print("Testando paginas publicas:")
all_ok = True
for name, fn in pages.items():
    try:
        resp = fn()
        print(f"  OK  {name} -> {resp.status_code}")
    except Exception as e:
        print(f"  ERRO {name} -> {type(e).__name__}: {e}")
        all_ok = False

if all_ok:
    print("\nTodas as paginas carregaram sem erro!")
else:
    print("\nALERTA: algumas paginas tem erro.")
