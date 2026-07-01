import os
os.environ["DJANGO_SETTINGS_MODULE"] = "core.settings"
import django
django.setup()

from django.test import RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.middleware import AuthenticationMiddleware
from django.contrib.messages.middleware import MessageMiddleware
from menu.models import Restaurant, Order
from django.contrib.auth.models import User
import menu.views as v

r = Restaurant.objects.first()
rf = RequestFactory()

def mock_request(path, method="get", user=None):
    if method == "post":
        req = rf.post(path, {})
    else:
        req = rf.get(path)
    mw = SessionMiddleware(lambda req: None)
    mw.process_request(req); req.session.save()
    auth = AuthenticationMiddleware(lambda req: None)
    auth.process_request(req)
    msg = MessageMiddleware(lambda req: None)
    msg.process_request(req)
    if user:
        req.user = user
    return req

user = User.objects.get(username="pastelaria")

print("Testando paginas do dashboard:")
all_ok = True
tests = {
    "Home": lambda: v.dashboard_home(mock_request("/painel/", user=user)),
    "Orders": lambda: v.dashboard_orders(mock_request("/painel/pedidos/", user=user)),
    "Menu": lambda: v.dashboard_menu(mock_request("/painel/cardapio/", user=user)),
    "Settings": lambda: v.dashboard_settings(mock_request("/painel/configuracoes/", user=user)),
    "Billing": lambda: v.dashboard_billing(mock_request("/painel/faturamento/", user=user)),
}
for name, fn in tests.items():
    try:
        resp = fn()
        print(f"  OK  {name} -> {resp.status_code}")
    except Exception as e:
        print(f"  ERRO {name} -> {type(e).__name__}: {e}")
        all_ok = False

print(f"\n{'Todas OK!' if all_ok else 'Ha erros!'}")
