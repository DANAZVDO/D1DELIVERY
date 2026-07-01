from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal

from menu.models import Restaurant, Category, MenuItem


class Command(BaseCommand):
    help = "Popula o banco com dados iniciais da Estação dos Pastéis"

    def handle(self, *args, **kwargs):
        self.stdout.write("Populando banco de dados...")

        user, created = User.objects.get_or_create(
            username="pastelaria",
            defaults={"email": "contato@estacaodospasteis.com.br"},
        )
        if created:
            user.set_password("mudar123")
            user.save()
            self.stdout.write("  Usuário criado: pastelaria / mudar123")

        restaurant, created = Restaurant.objects.get_or_create(
            slug="estacao-dos-pasteis",
            defaults={
                "user": user,
                "name": "Estação dos Pastéis",
                "phone": "(51) 99479-8139",
                "pix_key": "51994798139",
                "pix_key_type": "phone",
                "merchant_name": "Estacao dos Pasteis",
                "merchant_city": "Arroio do Sal",
                "delivery_fee": Decimal("5.00"),
                "min_order": Decimal("15.00"),
                "is_open": True,
                "address": "Av. Beira-Mar, Centro - Arroio do Sal/RS",
                "delivery_info": "Entregamos em toda Arroio do Sal. Pedido mínimo R$ 15,00. Tempo médio: 30-45 min.",
                "plan": "trial",
                "trial_start": timezone.now().date(),
            },
        )
        if created:
            self.stdout.write(f"  Restaurante criado: {restaurant.name} (/{restaurant.slug}/)")
        else:
            restaurant.user = user
            restaurant.save()
            self.stdout.write(f"  Restaurante atualizado: {restaurant.name}")

        pastel_cat, _ = Category.objects.get_or_create(
            restaurant=restaurant,
            name="Pastéis",
            defaults={"order": 1, "icon": "🥟"},
        )
        bebida_cat, _ = Category.objects.get_or_create(
            restaurant=restaurant,
            name="Bebidas",
            defaults={"order": 2, "icon": "🥤"},
        )
        porcao_cat, _ = Category.objects.get_or_create(
            restaurant=restaurant,
            name="Porções",
            defaults={"order": 3, "icon": "🍟"},
        )
        doce_cat, _ = Category.objects.get_or_create(
            restaurant=restaurant,
            name="Pastéis Doces",
            defaults={"order": 4, "icon": "🍫"},
        )

        pasteis = [
            ("Pastel de Carne", "Carne moída temperada, azeitona e ovo", "12.00"),
            ("Pastel de Queijo", "Mussarela derretida", "10.00"),
            ("Pastel de Frango c/ Catupiry", "Frango desfiado com catupiry cremoso", "13.00"),
            ("Pastel de Pizza", "Mussarela, tomate, orégano e azeitona", "12.00"),
            ("Pastel de Calabresa", "Calabresa fatiada com queijo e cebola", "13.00"),
            ("Pastel de Camarão", "Camarão refogado com requeijão", "18.00"),
            ("Pastel de Palmito", "Palmito fresco com mussarela", "14.00"),
            ("Pastel de Carne Seca", "Carne seca desfiada com abóbora", "15.00"),
            ("Pastel de Bacon c/ Queijo", "Bacon crocante com mussarela", "14.00"),
            ("Pastel Especial da Casa", "Carne, queijo, bacon, milho e catupiry", "17.00"),
        ]

        for name, desc, price in pasteis:
            MenuItem.objects.get_or_create(
                category=pastel_cat,
                name=name,
                defaults={"description": desc, "price": Decimal(price)},
            )
        self.stdout.write(f"  {len(pasteis)} pastéis criados")

        bebidas = [
            ("Refrigerante Lata 350ml", "Coca-Cola, Guaraná, Fanta ou Sprite", "7.00"),
            ("Suco Natural 500ml", "Laranja, limão, maracujá ou abacaxi", "9.00"),
            ("Água Mineral 500ml", "Com ou sem gás", "4.00"),
            ("Caldo de Cana 500ml", "Caldo de cana gelado com limão", "8.00"),
            ("Cerveja Lata 350ml", "Brahma, Skol ou Heineken", "8.00"),
            ("Água de Coco 330ml", "Água de coco gelada", "7.00"),
        ]

        for name, desc, price in bebidas:
            MenuItem.objects.get_or_create(
                category=bebida_cat,
                name=name,
                defaults={"description": desc, "price": Decimal(price)},
            )
        self.stdout.write(f"  {len(bebidas)} bebidas criadas")

        porcoes = [
            ("Batata Frita (P)", "Porção pequena de batata frita crocante", "16.00"),
            ("Batata Frita (G)", "Porção grande de batata frita crocante", "24.00"),
            ("Mandioca Frita (P)", "Porção pequena de mandioca frita", "15.00"),
            ("Mandioca Frita (G)", "Porção grande de mandioca frita", "22.00"),
            ("Calabresa Acebolada", "Calabresa fatiada com cebola grelhada", "25.00"),
            ("Bolinhos de Bacalhau (6 unid)", "Bolinhos de bacalhau crocantes", "20.00"),
        ]

        for name, desc, price in porcoes:
            MenuItem.objects.get_or_create(
                category=porcao_cat,
                name=name,
                defaults={"description": desc, "price": Decimal(price)},
            )
        self.stdout.write(f"  {len(porcoes)} porções criadas")

        doces = [
            ("Pastel de Chocolate c/ Banana", "Chocolate derretido com banana", "15.00"),
            ("Pastel de Romeu e Julieta", "Goiabada cremosa com queijo mussarela", "13.00"),
            ("Pastel de Doce de Leite", "Doce de leite cremoso", "12.00"),
            ("Pastel de Nutella c/ Morango", "Nutella com pedaços de morango", "17.00"),
        ]

        for name, desc, price in doces:
            MenuItem.objects.get_or_create(
                category=doce_cat,
                name=name,
                defaults={"description": desc, "price": Decimal(price)},
            )
        self.stdout.write(f"  {len(doces)} pastéis doces criados")

        self.stdout.write(self.style.SUCCESS("\nBanco populado com sucesso!"))
        self.stdout.write(f"\n  Cardápio: http://localhost:8000/r/{restaurant.slug}/")
        self.stdout.write(f"  Painel:   http://localhost:8000/painel/")
        self.stdout.write(f"  Usuário:  pastelaria")
        self.stdout.write(f"  Senha:    mudar123")
