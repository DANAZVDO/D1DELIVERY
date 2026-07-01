# D1 Delivery

Plataforma de cardápio digital com checkout PIX para delivery. Feito para pequenos restaurantes e lanchonetes.

## Stack

- **Backend:** Django 5 + Python 3.11+
- **Frontend:** Bootstrap 5 + JavaScript vanilla
- **Banco:** SQLite (desenvolvimento) / PostgreSQL (produção)
- **Pagamento:** PIX (QR Code dinâmico com payload BR Code)

## Como rodar localmente

### 1. Clone o repositório

```bash
git clone https://github.com/DANAZVDO/D1DELIVERY.git
cd D1DELIVERY
```

### 2. Crie um ambiente virtual

```bash
python -m venv venv
venv\Scripts\activate    # Windows
source venv/bin/activate  # Linux/Mac
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Execute as migrações

```bash
python manage.py migrate
```

### 5. Popule o banco com dados iniciais

```bash
python manage.py seed
```

Isso cria o restaurante "Estação dos Pastéis" com cardápio completo (26 itens) e 5 bairros de entrega.

### 6. Crie o superusuário (admin)

```bash
python manage.py createsuperuser
```

### 7. Rode o servidor

```bash
python manage.py runserver
```

Acesse: **http://127.0.0.1:8000/**

## Acessos do sistema

| Tela | URL | Quem usa |
|------|-----|----------|
| Landing page | `/` | Público |
| Cardápio do restaurante | `/r/estacao-dos-pasteis/` | Clientes |
| Painel do lojista | `/painel/` | Dono do restaurante |
| Admin Django | `/admin/` | Administrador da plataforma |
| Minha conta | `/minha-conta/` | Cliente (histórico de pedidos) |
| Cadastro | `/conta/cadastro/` | Novo cliente |

### Credenciais padrão (após rodar `seed`)

| Acesso | Usuário | Senha |
|--------|---------|-------|
| Painel lojista | `pastelaria` | `mudar123` |
| Admin Django | Criado via `createsuperuser` | Definido por você |

## Estrutura do projeto

```
D1DELIVERY/
├── core/              # Configurações Django
├── menu/              # App principal
│   ├── models.py      # Models (Restaurant, Order, MenuItem, DeliveryZone, etc)
│   ├── views.py       # Views (cardápio, carrinho, checkout, dashboard)
│   ├── pix.py         # Geração de QR Code PIX (padrão BR Code)
│   ├── management/    # Comandos customizados (seed)
│   └── templates/     # Templates HTML
│       ├── menu/          # Cardápio público, carrinho, checkout
│       ├── dashboard/     # Painel do lojista
│       └── customer/      # Área do cliente
├── static/            # CSS, JS
├── templates/         # Templates globais (base, landing)
└── media/             # Uploads (logos, fotos, comprovantes)
```

## Funcionalidades

- Cardápio digital com categorias, fotos e preços
- Carrinho de compras com sessão
- Checkout com QR Code PIX dinâmico
- Upload de comprovante PIX
- Acompanhamento de pedido em tempo real
- Painel do lojista com gestão de pedidos e cardápio
- Taxa de entrega por bairro (DeliveryZone)
- Conta de cliente com histórico de pedidos
- Comissão da plataforma (5%) com extrato
- Planos: Trial (grátis 14 dias), Básico (R$ 195/mês), Pro (R$ 395/mês)

## Deploy

### Render (gratuito)

1. Crie conta em [render.com](https://render.com)
2. New Web Service → conecte o repositório
3. Build Command: `pip install -r requirements.txt && python manage.py migrate && python manage.py seed`
4. Start Command: `gunicorn core.wsgi:application`

### Railway (gratuito)

1. Crie conta em [railway.app](https://railway.app)
2. New Project → Deploy from GitHub repo
3. Railway detecta automaticamente o projeto Django

## Licença

Projeto proprietário. Todos os direitos reservados.
