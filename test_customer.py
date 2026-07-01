import os; os.environ["DJANGO_SETTINGS_MODULE"] = "core.settings"
import django; django.setup()
from django.test import RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.middleware import AuthenticationMiddleware
from django.contrib.messages.middleware import MessageMiddleware
from menu.views import customer_login, customer_register

rf = RequestFactory()
def mock(path):
    req = rf.get(path)
    SessionMiddleware(lambda r: None).process_request(req)
    req.session.save()
    AuthenticationMiddleware(lambda r: None).process_request(req)
    MessageMiddleware(lambda r: None).process_request(req)
    return req

print("Login:", customer_login(mock("/conta/login/")).status_code)
print("Register:", customer_register(mock("/conta/cadastro/")).status_code)
print("OK - customer pages work")
