from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Restaurant(models.Model):
    PLAN_TRIAL = "trial"
    PLAN_BASIC = "basic"
    PLAN_PRO = "pro"
    PLAN_CHOICES = [
        (PLAN_TRIAL, "Trial 14 dias"),
        (PLAN_BASIC, "Básico - R$ 195/mês"),
        (PLAN_PRO, "Pro - R$ 395/mês"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="restaurant")
    name = models.CharField("Nome do restaurante", max_length=200)
    slug = models.SlugField("Link do cardápio", max_length=100, unique=True)
    logo = models.ImageField("Logo", upload_to="restaurants/", blank=True, null=True)
    phone = models.CharField("WhatsApp", max_length=20, blank=True)
    pix_key = models.CharField("Chave PIX", max_length=200, blank=True)
    pix_key_type = models.CharField(
        "Tipo de chave PIX",
        max_length=20,
        choices=[
            ("phone", "Telefone"),
            ("email", "E-mail"),
            ("cpf", "CPF"),
            ("cnpj", "CNPJ"),
            ("random", "Chave Aleatória"),
        ],
        default="phone",
    )
    merchant_name = models.CharField("Nome no PIX", max_length=25, blank=True)
    merchant_city = models.CharField("Cidade no PIX", max_length=15, default="Arroio do Sal")

    delivery_fee = models.DecimalField("Taxa de entrega", max_digits=6, decimal_places=2, default=5.00)
    min_order = models.DecimalField("Pedido mínimo", max_digits=6, decimal_places=2, default=15.00)
    setup_fee = models.DecimalField("Taxa de configuração", max_digits=6, decimal_places=2, default=100.00)
    is_open = models.BooleanField("Aberto", default=True)
    opening_time = models.TimeField("Abre às", default="18:00")
    closing_time = models.TimeField("Fecha às", default="23:00")
    address = models.CharField("Endereço", max_length=300, blank=True)
    delivery_info = models.TextField("Informações de entrega", blank=True)

    plan = models.CharField("Plano", max_length=10, choices=PLAN_CHOICES, default=PLAN_TRIAL)
    trial_start = models.DateField("Início do trial", default=timezone.now)
    plan_start = models.DateField("Início do plano", null=True, blank=True)
    is_active = models.BooleanField("Ativo", default=True)

    commission_rate = models.DecimalField("Comissão (%)", max_digits=5, decimal_places=2, default=5.00)
    commission_balance = models.DecimalField(
        "Comissão acumulada a pagar", max_digits=10, decimal_places=2, default=0.00
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Restaurante"
        verbose_name_plural = "Restaurantes"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def get_menu_url(self):
        from django.urls import reverse
        return reverse("menu", kwargs={"slug": self.slug})

    def is_trial_active(self):
        if self.plan != self.PLAN_TRIAL:
            return False
        return (timezone.now().date() - self.trial_start).days < 14

    def trial_days_left(self):
        if self.plan != self.PLAN_TRIAL:
            return 0
        days = 14 - (timezone.now().date() - self.trial_start).days
        return max(days, 0)


class Category(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name="categories")
    name = models.CharField("Nome da categoria", max_length=100)
    order = models.PositiveIntegerField("Ordem", default=0)
    icon = models.CharField("Ícone (emoji)", max_length=10, blank=True)

    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"
        ordering = ["order", "name"]

    def __str__(self):
        return f"{self.name} - {self.restaurant.name}"


class MenuItem(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="items")
    name = models.CharField("Nome do item", max_length=200)
    description = models.TextField("Descrição", blank=True)
    price = models.DecimalField("Preço", max_digits=8, decimal_places=2)
    image = models.ImageField("Foto", upload_to="menu_items/", blank=True, null=True)
    is_available = models.BooleanField("Disponível", default=True)
    order = models.PositiveIntegerField("Ordem", default=0)

    class Meta:
        verbose_name = "Item do cardápio"
        verbose_name_plural = "Itens do cardápio"
        ordering = ["order", "name"]

    def __str__(self):
        return f"{self.name} - R$ {self.price}"


class Order(models.Model):
    STATUS_CHOICES = [
        ("pending", "Aguardando Pagamento"),
        ("confirmed", "Pagamento Confirmado"),
        ("preparing", "Preparando"),
        ("out_for_delivery", "Saiu para Entrega"),
        ("delivered", "Entregue"),
        ("cancelled", "Cancelado"),
    ]

    DELIVERY_CHOICES = [
        ("delivery", "Delivery"),
        ("pickup", "Retirada"),
    ]

    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name="orders")

    customer_name = models.CharField("Nome do cliente", max_length=200)
    customer_phone = models.CharField("Telefone", max_length=20)
    customer_address = models.CharField("Endereço", max_length=300, blank=True)
    customer_complement = models.CharField("Complemento", max_length=200, blank=True)
    customer_profile = models.ForeignKey(
        "CustomerProfile", on_delete=models.SET_NULL, null=True, blank=True, related_name="orders",
        verbose_name="Cliente cadastrado"
    )
    delivery_type = models.CharField("Tipo", max_length=10, choices=DELIVERY_CHOICES, default="delivery")
    customer_neighborhood = models.CharField("Bairro", max_length=100, blank=True)
    customer_notes = models.TextField("Observações", blank=True)

    subtotal = models.DecimalField("Subtotal", max_digits=8, decimal_places=2)
    delivery_fee = models.DecimalField("Taxa de entrega", max_digits=6, decimal_places=2, default=0)
    total = models.DecimalField("Total", max_digits=8, decimal_places=2)

    status = models.CharField("Status", max_length=20, choices=STATUS_CHOICES, default="pending")

    pix_code = models.TextField("Código PIX copia e cola", blank=True)
    pix_proof = models.ImageField("Comprovante PIX", upload_to="comprovantes/", blank=True, null=True)

    commission_amount = models.DecimalField("Comissão (5%)", max_digits=8, decimal_places=2, default=0)
    commission_paid = models.BooleanField("Comissão paga", default=False)
    commission_paid_at = models.DateTimeField("Comissão paga em", null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Pedido #{self.id} - {self.customer_name} - {self.restaurant.name}"

    def calculate_commission(self):
        return round(float(self.total) * 0.05, 2)

    def save(self, *args, **kwargs):
        if not self.commission_amount and self.total:
            self.commission_amount = self.calculate_commission()
        super().save(*args, **kwargs)

    @property
    def order_number(self):
        return f"#{self.id:04d}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    menu_item = models.ForeignKey(MenuItem, on_delete=models.SET_NULL, null=True, related_name="order_items")
    name = models.CharField("Item", max_length=200)
    price = models.DecimalField("Preço unitário", max_digits=8, decimal_places=2)
    quantity = models.PositiveIntegerField("Quantidade", default=1)

    class Meta:
        verbose_name = "Item do pedido"
        verbose_name_plural = "Itens do pedido"

    def __str__(self):
        return f"{self.quantity}x {self.name}"

    @property
    def subtotal(self):
        return self.price * self.quantity


class Commission(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name="commissions")
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="commission_record")
    amount = models.DecimalField("Valor", max_digits=8, decimal_places=2)
    paid = models.BooleanField("Pago", default=False)
    paid_at = models.DateTimeField("Pago em", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Comissão"
        verbose_name_plural = "Comissões"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Comissão Pedido #{self.order.id} - R$ {self.amount}"


class CustomerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="customer_profile")
    phone = models.CharField("Telefone", max_length=20)
    address = models.CharField("Endereço principal", max_length=300, blank=True)
    complement = models.CharField("Complemento", max_length=200, blank=True)
    neighborhood = models.CharField("Bairro padrão", max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username}"

    @property
    def total_orders(self):
        return self.orders.count()


class DeliveryZone(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name="delivery_zones")
    name = models.CharField("Bairro / Região", max_length=100)
    fee = models.DecimalField("Taxa de entrega", max_digits=6, decimal_places=2, default=0)
    min_order = models.DecimalField("Pedido mínimo", max_digits=6, decimal_places=2, default=0)
    is_active = models.BooleanField("Ativo", default=True)
    order = models.PositiveIntegerField("Ordem", default=0)

    class Meta:
        verbose_name = "Zona de Entrega"
        verbose_name_plural = "Zonas de Entrega"
        ordering = ["order", "name"]

    def __str__(self):
        return f"{self.name} - R$ {self.fee} ({self.restaurant.name})"
