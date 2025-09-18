# ТЕХНИЧЕСКОЕ ЗАДАНИЕ (ТЗ) - ИНТЕГРАЦИЯ ODOO С TELEGRAM BOT

## 📋 **АРХИТЕКТУРА СИСТЕМЫ:**

### 1️⃣ **Структура на Railway:**
```
┌─────────────────────────────────────────────────────────────┐
│                    RAILWAY PROJECT                         │
│                  "amusing-gratitude"                        │
└─────────────────────────────────────────────────────────────┘

🟡 TELEGRAM BOT STACK (WebBot) - ✅ РАБОТАЕТ:
├── WebBot (✅ Active) - Telegram бот
├── Postgres (✅ Active) - БД для бота
└── Redis (✅ Active) - Кэш для бота

🔵 ODOO STACK - ⏳ ДЕПЛОИТСЯ:
├── Odoo (⏳ Deploying) - Odoo система
└── Postgres-9ayk (✅ Active) - БД для Odoo
```

## 🚀 **РЕШЕНИЕ ПОДКЛЮЧЕНИЯ:**

### 1️⃣ **Конфигурация WebBot (уже работает):**
```python
# Переменные окружения для WebBot
DATABASE_URL = "postgresql://postgres:password@postgres-production.up.railway.app:5432/bot_db"
REDIS_URL = "redis://redis-production.up.railway.app:6379"
ODOO_URL = "https://odoo-production-8a4f.up.railway.app"
ODOO_DB = "odoo_db"
ODOO_USERNAME = "admin"
ODOO_PASSWORD = "5131225sd"
```

### 2️⃣ **Конфигурация Odoo (нужно дождаться деплоя):**
```ini
# odoo.conf
db_host = postgres-9ayk-production.up.railway.app
db_port = 5432
db_user = postgres
db_password = AZfHgswCy~sDLHYaq_OljEGiuTLGYRYa
db_name = odoo_db
addons_path = /usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons
admin_passwd = masterpass2024
without_demo = True
workers = 2
```

### 3️⃣ **Dockerfile для Odoo:**
```dockerfile
FROM odoo:17.0
USER root
COPY odoo-addons/ /mnt/extra-addons/
COPY odoo.conf /etc/odoo/
RUN chown -R odoo:odoo /mnt/extra-addons/
RUN chown odoo:odoo /etc/odoo/odoo.conf
USER odoo
EXPOSE 8069
```

## 📊 **СХЕМА ДАННЫХ:**

### **Bot Database (Postgres):**
```sql
-- Пользователи бота
CREATE TABLE bot_users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE,
    username VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    phone VARCHAR(20),
    odoo_user_id INTEGER, -- Связь с Odoo
    created_at TIMESTAMP DEFAULT NOW()
);

-- Карты лояльности (кэш из Odoo)
CREATE TABLE loyalty_cards (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES bot_users(id),
    card_number VARCHAR(50) UNIQUE,
    balance DECIMAL(10,2) DEFAULT 0,
    odoo_card_id INTEGER, -- Связь с Odoo
    created_at TIMESTAMP DEFAULT NOW()
);

-- Транзакции бота
CREATE TABLE bot_transactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES bot_users(id),
    amount DECIMAL(10,2),
    type VARCHAR(20), -- 'earn', 'spend', 'bonus'
    description TEXT,
    odoo_transaction_id INTEGER, -- Связь с Odoo
    created_at TIMESTAMP DEFAULT NOW()
);
```

### **Odoo Database (Postgres-9ayk):**
```sql
-- Пользователи Odoo (res.partner)
CREATE TABLE res_partner (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(20),
    bot_telegram_id BIGINT, -- Связь с ботом
    created_at TIMESTAMP DEFAULT NOW()
);

-- Карты лояльности Odoo
CREATE TABLE loyalty_cards (
    id SERIAL PRIMARY KEY,
    partner_id INTEGER REFERENCES res_partner(id),
    card_number VARCHAR(50) UNIQUE,
    balance DECIMAL(10,2) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Транзакции Odoo
CREATE TABLE loyalty_transactions (
    id SERIAL PRIMARY KEY,
    card_id INTEGER REFERENCES loyalty_cards(id),
    amount DECIMAL(10,2),
    type VARCHAR(20), -- 'earn', 'spend', 'bonus'
    description TEXT,
    bot_transaction_id INTEGER, -- Связь с ботом
    created_at TIMESTAMP DEFAULT NOW()
);
```

## 🔗 **API ENDPOINTS В ODOO:**

### **odoo-addons/karmabot_webapp/controllers/webapp_controller.py:**
```python
from odoo import http, fields
from odoo.http import request
import json

class WebAppController(http.Controller):
    
    @http.route('/api/bot/user', methods=['POST'], type='http', auth='none', csrf=False)
    def create_user(self, **kwargs):
        """Создание пользователя из бота"""
        try:
            data = request.jsonrequest
            partner = request.env['res.partner'].create({
                'name': data.get('name'),
                'email': data.get('email'),
                'phone': data.get('phone'),
                'bot_telegram_id': data.get('telegram_id')
            })
            return json.dumps({
                'success': True, 
                'user_id': partner.id,
                'message': 'Пользователь создан успешно'
            })
        except Exception as e:
            return json.dumps({
                'success': False,
                'error': str(e)
            })
    
    @http.route('/api/bot/card', methods=['POST'], type='http', auth='none', csrf=False)
    def create_card(self, **kwargs):
        """Создание карты лояльности"""
        try:
            data = request.jsonrequest
            card = request.env['loyalty.card'].create({
                'partner_id': data.get('user_id'),
                'card_number': data.get('card_number'),
                'balance': 0
            })
            return json.dumps({
                'success': True, 
                'card_id': card.id,
                'card_number': card.card_number,
                'message': 'Карта создана успешно'
            })
        except Exception as e:
            return json.dumps({
                'success': False,
                'error': str(e)
            })
    
    @http.route('/api/bot/transaction', methods=['POST'], type='http', auth='none', csrf=False)
    def create_transaction(self, **kwargs):
        """Создание транзакции"""
        try:
            data = request.jsonrequest
            transaction = request.env['loyalty.transaction'].create({
                'card_id': data.get('card_id'),
                'amount': data.get('amount'),
                'type': data.get('type'),
                'description': data.get('description'),
                'bot_transaction_id': data.get('bot_transaction_id')
            })
            return json.dumps({
                'success': True,
                'transaction_id': transaction.id,
                'new_balance': transaction.card_id.balance,
                'message': 'Транзакция создана успешно'
            })
        except Exception as e:
            return json.dumps({
                'success': False,
                'error': str(e)
            })
    
    @http.route('/api/bot/balance/<int:card_id>', methods=['GET'], type='http', auth='none', csrf=False)
    def get_balance(self, card_id, **kwargs):
        """Получение баланса карты"""
        try:
            card = request.env['loyalty.card'].browse(card_id)
            if not card.exists():
                return json.dumps({
                    'success': False,
                    'error': 'Карта не найдена'
                })
            return json.dumps({
                'success': True,
                'card_id': card.id,
                'balance': card.balance,
                'card_number': card.card_number
            })
        except Exception as e:
            return json.dumps({
                'success': False,
                'error': str(e)
            })
```

## 🔌 **ПОДКЛЮЧЕНИЕ ИЗ BOT:**

### **odoo_connector.py:**
```python
import xmlrpc.client
import os
import requests
import json

class OdooConnector:
    def __init__(self):
        self.url = os.getenv('ODOO_URL')
        self.db = os.getenv('ODOO_DB')
        self.username = os.getenv('ODOO_USERNAME')
        self.password = os.getenv('ODOO_PASSWORD')
        self.uid = None
        
        if self.url and self.password:
            self.common = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common')
            self.models = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/object')
    
    def authenticate(self):
        """Аутентификация в Odoo"""
        if not all([self.url, self.db, self.username, self.password]):
            return False
        try:
            self.uid = self.common.authenticate(self.db, self.username, self.password, {})
            return bool(self.uid)
        except Exception as e:
            print(f"Ошибка аутентификации: {e}")
            return False
    
    def create_user(self, user_data):
        """Создание пользователя в Odoo через API"""
        try:
            response = requests.post(
                f"{self.url}/api/bot/user",
                json=user_data,
                headers={'Content-Type': 'application/json'}
            )
            return response.json()
        except Exception as e:
            print(f"Ошибка создания пользователя: {e}")
            return {'success': False, 'error': str(e)}
    
    def create_card(self, card_data):
        """Создание карты лояльности в Odoo через API"""
        try:
            response = requests.post(
                f"{self.url}/api/bot/card",
                json=card_data,
                headers={'Content-Type': 'application/json'}
            )
            return response.json()
        except Exception as e:
            print(f"Ошибка создания карты: {e}")
            return {'success': False, 'error': str(e)}
    
    def create_transaction(self, transaction_data):
        """Создание транзакции в Odoo через API"""
        try:
            response = requests.post(
                f"{self.url}/api/bot/transaction",
                json=transaction_data,
                headers={'Content-Type': 'application/json'}
            )
            return response.json()
        except Exception as e:
            print(f"Ошибка создания транзакции: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_balance(self, card_id):
        """Получение баланса карты из Odoo через API"""
        try:
            response = requests.get(f"{self.url}/api/bot/balance/{card_id}")
            return response.json()
        except Exception as e:
            print(f"Ошибка получения баланса: {e}")
            return {'success': False, 'error': str(e)}
    
    def test_connection(self):
        """Тест подключения к Odoo"""
        try:
            response = requests.get(f"{self.url}/web/health")
            return response.status_code == 200
        except:
            return False
```

## 🔄 **ПОТОК ДАННЫХ:**

### **Регистрация пользователя:**
```
1. Пользователь нажимает /start в боте
2. Бот сохраняет в СВОЮ БД (Postgres)
3. Бот отправляет данные в Odoo API (/api/bot/user)
4. Odoo сохраняет в СВОЮ БД (Postgres-9ayk)
5. Odoo возвращает ID пользователя боту
6. Бот обновляет odoo_user_id в своей БД
7. Бот создает карту лояльности через Odoo API (/api/bot/card)
8. Бот отправляет карту пользователю
```

### **Начисление бонусов:**
```
1. Пользователь совершает покупку
2. Бот получает данные о покупке
3. Бот отправляет транзакцию в Odoo API (/api/bot/transaction)
4. Odoo начисляет бонусы в СВОЮ БД
5. Odoo возвращает новый баланс боту
6. Бот обновляет баланс в СВОЕЙ БД
7. Бот уведомляет пользователя
```

### **Проверка баланса:**
```
1. Пользователь запрашивает баланс
2. Бот получает баланс из Odoo API (/api/bot/balance/{card_id})
3. Бот обновляет кэш в своей БД
4. Бот отправляет баланс пользователю
```

## 🎯 **ПЛАН РЕАЛИЗАЦИИ:**

### **Этап 1: Дождаться деплоя Odoo**
- Проверить статус деплоя
- Убедиться что модули загружены
- Протестировать API endpoints

### **Этап 2: Настроить интеграцию**
- Добавить odoo_connector.py в бот
- Настроить переменные окружения
- Протестировать связь между системами

### **Этап 3: Тестирование**
- Протестировать создание пользователя
- Протестировать создание карты
- Протестировать транзакции
- Протестировать получение баланса

## 🔒 **БЕЗОПАСНОСТЬ:**
- HTTPS для всех соединений
- Валидация данных на всех уровнях
- Логирование всех операций
- Обработка ошибок

## 📊 **МОНИТОРИНГ:**
- Логи бота в Railway
- Логи Odoo в Railway
- Мониторинг БД через Railway Dashboard
- Алерты при ошибках

## 🚀 **КОМАНДЫ ДЛЯ ПРОВЕРКИ:**

### **Проверка статуса деплоя:**
```powershell
railway status
railway logs --service Odoo
```

### **Тестирование API:**
```powershell
# Проверить доступность Odoo
curl https://odoo-production-8a4f.up.railway.app/web/health

# Тест создания пользователя
curl -X POST https://odoo-production-8a4f.up.railway.app/api/bot/user \
  -H "Content-Type: application/json" \
  -d '{"name": "Test User", "telegram_id": 123456}'
```

### **Проверка переменных окружения:**
```powershell
railway variables
```

---

**Это полное техническое задание для интеграции Odoo с Telegram Bot! 🚀**
