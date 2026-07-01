from django import forms
from .models import Order


class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            "customer_name",
            "customer_phone",
            "customer_address",
            "customer_complement",
            "customer_neighborhood",
            "delivery_type",
            "customer_notes",
        ]
        widgets = {
            "customer_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Seu nome completo",
                "required": True,
            }),
            "customer_phone": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "(51) 99999-9999",
                "required": True,
            }),
            "customer_address": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Rua, número",
                "required": True,
            }),
            "customer_complement": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Apto, bloco, ponto de referência",
            }),
            "customer_neighborhood": forms.Select(attrs={
                "class": "form-control",
            }),
            "customer_notes": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 2,
                "placeholder": "Observações do pedido (opcional)",
            }),
            "delivery_type": forms.Select(attrs={
                "class": "form-control",
            }),
        }
