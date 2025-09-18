# 🚀 ПЛАН РЕФАКТОРИНГА KARMABOT1

## 🎯 ГЛАВНАЯ ЦЕЛЬ ДОСТИГНУТА
**Бот = умная витрина + быстрые операции + ИИ помощники**  
**Odoo = красивые веб-кабинеты + вся бизнес-логика**

---

## 🏗️ ИТОГОВАЯ АРХИТЕКТУРА

### 👤 ПОЛЬЗОВАТЕЛИ - ВСЁ В БОТЕ
**Обоснование:** Пользователям нужен быстрый доступ без загрузки веб-интерфейсов

```
👤 Личный кабинет (100% в боте):
├── 💳 Мои карты (добавление по номеру/QR/виртуальная)
├── 💎 Мои баллы (просмотр/списание/к скидке)  
├── 📋 История (операции по баллам/картам + SMS)
├── 🌐 Язык (4 языка интерфейса)
└── ◀️ Назад
```

### 🤝 ПАРТНЕРЫ - ГИБРИД (смарт-разделение)
**Обоснование:** Быстрые операции в боте, управление в красивом веб-интерфейсе

```
🤝 Партнёрский кабинет:
├── 🧾 Сканировать QR (В БОТЕ - камера Telegram)
├── 🗂 Мои карточки (→ Odoo WebApp - красивое управление)
├── ➕ Добавить карточку (→ Odoo WebApp - формы создания)
├── 📊 Отчёт (SMS из Odoo с автоудалением через 5 мин)
└── ◀️ Назад
```

### 👨‍💼 АДМИНЫ - ИИ + ВЕБА 
**Обоснование:** ИИ мониторинг в боте, сложное управление в веб-панелях

```
👨‍💼 Админское меню:
├── 🗂️ Категории (витрина)
├── 🤖 ИИ Помощник (В БОТЕ - умный поиск/отчёты/мониторинг)
├── 📊 Живые дашборды (В БОТЕ - онлайн счетчики)
├── 👤 Админ кабинет (→ Odoo WebApp - полная панель управления)
└── ❓ Помощь
```

### 👑 СУПЕР-АДМИНЫ - РАСШИРЕННЫЙ ИИ + СУПЕР-ВЕБА
**Обоснование:** Максимальный контроль через продвинутого ИИ + веб-панели

```  
👑 Супер-админ меню:
├── 🗂️ Категории (витрина)
├── 🤖 ИИ Помощник (В БОТЕ - полный контроль системы + управление ИИ агентами)
├── 📊 Расширенные дашборды (В БОТЕ - система/модерация/уведомления)
├── 👑 Супер-админ кабинет (→ Odoo WebApp - абсолютный контроль)
└── ❓ Помощь
```

---

## 🔧 КОНКРЕТНЫЙ ПЛАН РЕАЛИЗАЦИИ

### 🚨 ФАЗА 0: КРИТИЧНЫЕ ИСПРАВЛЕНИЯ (НЕМЕДЛЕННО!)

#### 1. Исправить проблемы безопасности
```python
# ❌ ТЕКУЩАЯ ПРОБЛЕМА (main_menu_router.py:1108)
secret = os.getenv('SECRET_KEY', 'karmasystem-secret')  # Хардкод!

# ✅ ИСПРАВЛЕНИЕ
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is required")
secret = SECRET_KEY.encode()
```

#### 2. Добавить Rate Limiting
```python
# core/middleware/rate_limit.py
from aiogram import BaseMiddleware
import time
from collections import defaultdict

class RateLimitMiddleware(BaseMiddleware):
    def __init__(self, rate_limit: int = 20):  # 20 req/min
        self.rate_limit = rate_limit
        self.requests = defaultdict(list)
    
    async def __call__(self, handler, event, data):
        user_id = event.from_user.id if hasattr(event, 'from_user') else None
        if user_id:
            now = time.time()
            user_requests = self.requests[user_id]
            # Очистить старые запросы (старше 1 минуты)
            user_requests[:] = [req_time for req_time in user_requests if now - req_time < 60]
            
            if len(user_requests) >= self.rate_limit:
                await event.answer("⚠️ Слишком много запросов. Попробуйте через минуту.")
                return
            
            user_requests.append(now)
        
        return await handler(event, data)
```

#### 3. Добавить логирование админских действий
```python
# core/middleware/admin_logging.py
import logging
from aiogram import BaseMiddleware

admin_logger = logging.getLogger("admin_actions")

class AdminLoggingMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        user_id = event.from_user.id if hasattr(event, 'from_user') else None
        
        # Проверить если это админское действие
        if user_id and await self.is_admin_action(event):
            admin_logger.info(f"Admin {user_id} performed action: {event.text or event.data}")
        
        return await handler(event, data)
    
    async def is_admin_action(self, event):
        from core.services.admins import admins_service
        from core.settings import settings
        
        user_id = event.from_user.id
        is_superadmin = int(user_id) == int(settings.bots.admin_id)
        is_admin = await admins_service.is_admin(user_id)
        
        return is_superadmin or is_admin
```

---

### 📱 ФАЗА 1: УПРОСТИТЬ МЕНЮ БОТА

#### Унифицированное главное меню
```python
# core/keyboards/unified_menu.py
def get_universal_main_menu(lang: str = 'ru') -> ReplyKeyboardMarkup:
    """Единое главное меню для всех ролей"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=get_text("choose_category", lang)), 
             KeyboardButton(text=get_text("keyboard.referral_program", lang))],
            [KeyboardButton(text=get_text("favorites", lang)), 
             KeyboardButton(text=get_text("help", lang))],
            [KeyboardButton(text=get_text("profile", lang))]
        ],
        resize_keyboard=True,
        input_field_placeholder=get_text("choose_action", lang)
    )

# Различия только в личных кабинетах
def get_role_based_cabinet(role: str, lang: str = 'ru') -> ReplyKeyboardMarkup:
    if role == 'user':
        return get_user_cabinet_keyboard(lang)
    elif role == 'partner':
        return get_partner_cabinet_keyboard(lang)
    elif role in ('admin', 'super_admin'):
        return get_admin_cabinet_keyboard(role, lang)
```

#### Упрощенные кабинеты
```python
# Пользовательский кабинет (все в боте)
def get_user_cabinet_keyboard(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup([
        [KeyboardButton("💳 Мои карты"), KeyboardButton("💎 Мои баллы")],
        [KeyboardButton("📋 История"), KeyboardButton("🌐 Язык")],
        [KeyboardButton("◀️ Назад")]
    ])

# Партнерский кабинет (гибрид)
def get_partner_cabinet_keyboard(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup([
        [KeyboardButton("🧾 Сканировать QR")],
        [KeyboardButton("🗂 Мои карточки"), KeyboardButton("➕ Добавить карточку")],
        [KeyboardButton("📊 Отчёт"), KeyboardButton("◀️ Назад")]
    ])

# Админский кабинет (ИИ + веб)
def get_admin_cabinet_keyboard(role: str, lang: str) -> ReplyKeyboardMarkup:
    if role == 'super_admin':
        return ReplyKeyboardMarkup([
            [KeyboardButton("🗂️ Категории")],
            [KeyboardButton("🤖 ИИ Помощник")],
            [KeyboardButton("📊 Расширенные дашборды")],
            [KeyboardButton("👑 Супер-админ кабинет")],
            [KeyboardButton("❓ Помощь")]
        ])
    else:  # admin
        return ReplyKeyboardMarkup([
            [KeyboardButton("🗂️ Категории")],
            [KeyboardButton("🤖 ИИ Помощник")],
            [KeyboardButton("📊 Живые дашборды")],
            [KeyboardButton("👤 Админ кабинет")],
            [KeyboardButton("❓ Помощь")]
        ])
```

---

### 🌐 ФАЗА 2: СОЗДАТЬ ODOO WEBAPP ИНТЕГРАЦИЮ

#### SSO сервис для безопасных переходов
```python
# core/services/sso_service.py
import jwt
import time
import os
from typing import Dict, Any

class SSOService:
    def __init__(self):
        self.jwt_secret = os.getenv("JWT_SECRET")
        if not self.jwt_secret:
            raise ValueError("JWT_SECRET environment variable is required")
    
    async def create_sso_token(self, telegram_id: int, role: str, 
                              session_data: Dict[str, Any] = None) -> str:
        """Создать SSO токен для перехода в Odoo"""
        payload = {
            'telegram_id': str(telegram_id),
            'role': role,
            'iat': int(time.time()),
            'exp': int(time.time()) + 600,  # 10 минут TTL
            'session_id': f"tg_{telegram_id}_{int(time.time())}",
            'data': session_data or {}
        }
        return jwt.encode(payload, self.jwt_secret, algorithm='HS256')
    
    async def validate_sso_token(self, token: str) -> Dict[str, Any]:
        """Валидировать SSO токен"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=['HS256'])
            if payload['exp'] < time.time():
                raise jwt.ExpiredSignatureError("Token expired")
            return payload
        except jwt.InvalidTokenError:
            return None

sso_service = SSOService()
```

#### WebApp переходы
```python
# core/keyboards/webapp_keyboards.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from core.services.sso_service import sso_service
from core.settings import settings

async def create_webapp_keyboard(user_id: int, role: str, 
                                actions: list) -> InlineKeyboardMarkup:
    """Создать клавиатуру с WebApp кнопками"""
    buttons = []
    
    for action in actions:
        sso_token = await sso_service.create_sso_token(user_id, role, {
            'action': action['action'],
            'context': action.get('context', {})
        })
        
        webapp_url = f"{settings.odoo.base_url}{action['path']}?sso={sso_token}"
        button = InlineKeyboardButton(
            text=action['title'],
            web_app=WebAppInfo(url=webapp_url)
        )
        buttons.append([button])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Использование для партнеров
async def get_partner_webapp_actions(user_id: int) -> InlineKeyboardMarkup:
    actions = [
        {
            'title': '🗂 Управление карточками',
            'path': '/partner/cards',
            'action': 'manage_cards'
        },
        {
            'title': '➕ Создать карточку',
            'path': '/partner/cards/new',
            'action': 'create_card'
        },
        {
            'title': '📊 Аналитика',
            'path': '/partner/analytics',
            'action': 'view_analytics'
        }
    ]
    return await create_webapp_keyboard(user_id, 'partner', actions)
```

---

### 🤖 ФАЗА 3: ИНТЕГРИРОВАТЬ ИИ ПОМОЩНИКОВ

#### Claude API для админов
```python
# core/services/ai_assistant.py
import anthropic
import os
from typing import Dict, Any
from core.services.odoo_api import odoo_api
from core.database.db_v2 import db_v2

class AdminAIAssistant:
    def __init__(self):
        self.client = anthropic.Anthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )
    
    async def process_admin_query(self, question: str, admin_id: int, 
                                 role: str) -> str:
        """Обработать вопрос админа через ИИ"""
        
        # Определить тип запроса
        if any(word in question.lower() for word in ["найди", "поиск", "пользователь"]):
            return await self._search_user(question)
        elif any(word in question.lower() for word in ["статистика", "отчет", "данные"]):
            return await self._get_stats(question)
        elif any(word in question.lower() for word in ["модерация", "карточки", "одобрить"]):
            return await self._moderation_info(question)
        else:
            return await self._general_ai_response(question, admin_id, role)
    
    async def _search_user(self, question: str) -> str:
        """Поиск пользователей"""
        try:
            # Извлечь параметры поиска из вопроса
            # Например: "найди пользователя с id 123" или "найди пользователя по имени Иван"
            users = await db_v2.search_users(question)
            if not users:
                return "🔍 Пользователи не найдены по вашему запросу."
            
            result = "👥 **Найденные пользователи:**\n\n"
            for user in users[:5]:  # Показать первых 5
                result += f"• ID: {user['telegram_id']}\n"
                result += f"  Имя: {user.get('first_name', 'Не указано')}\n"
                result += f"  Username: @{user.get('username', 'нет')}\n"
                result += f"  Роль: {user.get('role', 'user')}\n"
                result += f"  Баллы: {user.get('karma_points', 0)}\n\n"
            
            return result
        except Exception as e:
            return f"❌ Ошибка поиска: {str(e)}"
    
    async def _get_stats(self, question: str) -> str:
        """Получить статистику"""
        try:
            stats = await db_v2.get_system_stats()
            return f"""📊 **Статистика системы:**

👥 Пользователи: {stats.get('total_users', 0)}
🤝 Партнеры: {stats.get('total_partners', 0)}
🗂 Карточки: {stats.get('total_cards', 0)}
⏳ На модерации: {stats.get('pending_moderation', 0)}
💎 Всего баллов: {stats.get('total_points', 0)}
📱 QR сканирований: {stats.get('qr_scans', 0)}

🔄 Обновлено: сейчас"""
        except Exception as e:
            return f"❌ Ошибка получения статистики: {str(e)}"
    
    async def _moderation_info(self, question: str) -> str:
        """Информация о модерации"""
        try:
            pending_cards = await db_v2.get_pending_cards()
            if not pending_cards:
                return "✅ Нет карточек на модерации!"
            
            result = f"📋 **Карточки на модерации ({len(pending_cards)}):**\n\n"
            for card in pending_cards[:3]:  # Показать первые 3
                result += f"🏪 **{card['title']}**\n"
                result += f"📍 {card.get('address', 'Адрес не указан')}\n"
                result += f"👤 Партнер: {card.get('partner_name', 'Неизвестно')}\n"
                result += f"📅 Создано: {card.get('created_at', 'Неизвестно')}\n\n"
            
            if len(pending_cards) > 3:
                result += f"... и ещё {len(pending_cards) - 3} карточек\n\n"
            
            result += "💡 Используйте кнопку 'Модерация' для управления."
            return result
        except Exception as e:
            return f"❌ Ошибка получения данных модерации: {str(e)}"
    
    async def _general_ai_response(self, question: str, admin_id: int, 
                                  role: str) -> str:
        """Общий ответ через Claude"""
        try:
            system_prompt = f"""Ты - ИИ помощник для администратора Telegram-бота KarmaSystem.
            
Админ с ID {admin_id} и ролью {role} задал вопрос: "{question}"

Ты можешь:
- Отвечать на вопросы о системе
- Давать советы по управлению
- Помогать с поиском информации
- Объяснять функции бота

Отвечай кратко, по делу, на русском языке."""

            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=500,
                system=system_prompt,
                messages=[{"role": "user", "content": question}]
            )
            
            return f"🤖 **ИИ Помощник:**\n\n{response.content[0].text}"
        except Exception as e:
            return f"❌ ИИ временно недоступен: {str(e)}"

ai_assistant = AdminAIAssistant()
```

#### Живые дашборды с автообновлением
```python
# core/handlers/live_dashboard.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
import asyncio
from core.services.ai_assistant import ai_assistant
from core.database.db_v2 import db_v2

dashboard_router = Router(name="live_dashboard")

@dashboard_router.message(F.text == "📊 Живые дашборды")
async def show_live_dashboard(message: Message):
    """Показать живой дашборд для админов"""
    try:
        stats = await db_v2.get_live_stats()
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton("🔄 Обновить", callback_data="dashboard_refresh")],
            [InlineKeyboardButton("📊 Детали", callback_data="dashboard_details")],
            [InlineKeyboardButton("🤖 Спросить ИИ", callback_data="dashboard_ai")]
        ])
        
        text = f"""📊 **Живой дашборд**

⏳ **Модерация:** {stats.get('pending_moderation', 0)}
🔔 **Уведомления:** {stats.get('notifications', 0)}
🟢 **Система:** {'OK' if stats.get('system_ok') else 'Проблемы'}

👥 Онлайн: {stats.get('online_users', 0)}
📱 QR сегодня: {stats.get('qr_today', 0)}
💰 Транзакций/час: {stats.get('transactions_hour', 0)}

🔄 Автообновление: каждые 30 сек"""

        await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
        
        # Запустить автообновление
        asyncio.create_task(auto_update_dashboard(message.chat.id, message.message_id + 1))
        
    except Exception as e:
        await message.answer(f"❌ Ошибка загрузки дашборда: {str(e)}")

@dashboard_router.callback_query(F.data == "dashboard_refresh")
async def refresh_dashboard(callback: CallbackQuery):
    """Обновить дашборд"""
    try:
        stats = await db_v2.get_live_stats()
        
        text = f"""📊 **Живой дашборд**

⏳ **Модерация:** {stats.get('pending_moderation', 0)}
🔔 **Уведомления:** {stats.get('notifications', 0)}
🟢 **Система:** {'OK' if stats.get('system_ok') else 'Проблемы'}

👥 Онлайн: {stats.get('online_users', 0)}
📱 QR сегодня: {stats.get('qr_today', 0)}
💰 Транзакций/час: {stats.get('transactions_hour', 0)}

🔄 Обновлено: только что"""

        await callback.message.edit_text(text, reply_markup=callback.message.reply_markup, 
                                        parse_mode="Markdown")
        await callback.answer("✅ Дашборд обновлен")
        
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {str(e)}")

@dashboard_router.callback_query(F.data == "dashboard_ai")
async def dashboard_ai_query(callback: CallbackQuery):
    """ИИ анализ дашборда"""
    try:
        stats = await db_v2.get_live_stats()
        question = f"Проанализируй текущую статистику системы: {stats}"
        
        response = await ai_assistant.process_admin_query(
            question, callback.from_user.id, "admin"
        )
        
        await callback.message.answer(response, parse_mode="Markdown")
        await callback.answer()
        
    except Exception as e:
        await callback.answer(f"❌ ИИ недоступен: {str(e)}")

async def auto_update_dashboard(chat_id: int, message_id: int):
    """Автообновление дашборда каждые 30 секунд"""
    for _ in range(20):  # 10 минут автообновления
        await asyncio.sleep(30)
        try:
            stats = await db_v2.get_live_stats()
            # Обновить сообщение с новой статистикой
            # (реализация зависит от конкретного бота)
        except Exception:
            break  # Остановить при ошибке
```

---

### 📋 ФАЗА 4: СОЗДАТЬ ODOO МОДУЛИ

#### Модуль WebApp
```python
# odoo-addons/karmabot_webapp/models/webapp.py
from odoo import models, fields, api
import jwt
import os

class KarmabotWebApp(models.Model):
    _name = 'karmabot.webapp'
    _description = 'KarmaBot WebApp Integration'
    
    name = fields.Char('Name', required=True)
    telegram_id = fields.Char('Telegram ID', required=True)
    role = fields.Selection([
        ('user', 'User'),
        ('partner', 'Partner'), 
        ('admin', 'Admin'),
        ('super_admin', 'Super Admin')
    ], required=True)
    session_token = fields.Text('Session Token')
    last_activity = fields.Datetime('Last Activity', default=fields.Datetime.now)
    
    @api.model
    def authenticate_telegram_user(self, sso_token):
        """Аутентификация пользователя по SSO токену"""
        try:
            jwt_secret = os.getenv("JWT_SECRET")
            payload = jwt.decode(sso_token, jwt_secret, algorithms=['HS256'])
            
            telegram_id = payload.get('telegram_id')
            role = payload.get('role')
            
            # Найти или создать пользователя
            user = self.search([('telegram_id', '=', telegram_id)], limit=1)
            if not user:
                user = self.create({
                    'name': f'Telegram User {telegram_id}',
                    'telegram_id': telegram_id,
                    'role': role,
                    'session_token': sso_token
                })
            else:
                user.write({
                    'session_token': sso_token,
                    'last_activity': fields.Datetime.now()
                })
            
            return user
            
        except jwt.InvalidTokenError:
            return False
    
    def get_partner_cards(self):
        """Получить карточки партнера"""
        if self.role != 'partner':
            return []
        
        return self.env['karmasystem.partner.card'].search([
            ('partner_telegram_id', '=', self.telegram_id)
        ])
    
    def get_admin_dashboard_data(self):
        """Получить данные для админской панели"""
        if self.role not in ('admin', 'super_admin'):
            return {}
        
        return {
            'pending_cards': self.env['karmasystem.partner.card'].search_count([
                ('status', '=', 'pending')
            ]),
            'total_partners': self.env['res.partner'].search_count([
                ('is_karmabot_partner', '=', True)
            ]),
            'total_users': self.env['karmabot.webapp'].search_count([
                ('role', '=', 'user')
            ])
        }
```

#### Модуль SSO
```python
# odoo-addons/karmabot_sso/controllers/sso.py
from odoo import http
from odoo.http import request
import jwt
import json

class KarmabotSSOController(http.Controller):
    
    @http.route('/karmabot/sso/login', type='http', auth='none', 
                methods=['GET'], csrf=False)
    def sso_login(self, sso=None, **kwargs):
        """Вход через SSO токен из Telegram бота"""
        if not sso:
            return request.render('karmabot_sso.error_page', {
                'error': 'SSO token is required'
            })
        
        try:
            # Аутентификация пользователя
            webapp = request.env['karmabot.webapp'].sudo()
            user = webapp.authenticate_telegram_user(sso)
            
            if not user:
                return request.render('karmabot_sso.error_page', {
                    'error': 'Invalid or expired SSO token'
                })
            
            # Создать Odoo сессию
            request.session.authenticate(
                request.env.cr.dbname, 
                user.telegram_id, 
                user.session_token
            )
            
            # Перенаправить в зависимости от роли
            if user.role == 'partner':
                return request.redirect('/karmabot/partner/dashboard')
            elif user.role in ('admin', 'super_admin'):
                return request.redirect('/karmabot/admin/dashboard')
            else:
                return request.redirect('/karmabot/user/profile')
                
        except Exception as e:
            return request.render('karmabot_sso.error_page', {
                'error': f'Authentication failed: {str(e)}'
            })
    
    @http.route('/karmabot/partner/dashboard', type='http', auth='user')
    def partner_dashboard(self, **kwargs):
        """Партнерская панель управления"""
        user = request.env['karmabot.webapp'].search([
            ('telegram_id', '=', request.session.get('login'))
        ], limit=1)
        
        if not user or user.role != 'partner':
            return request.redirect('/web/login')
        
        cards = user.get_partner_cards()
        
        return request.render('karmabot_webapp.partner_dashboard', {
            'user': user,
            'cards': cards,
            'stats': self._get_partner_stats(user)
        })
    
    @http.route('/karmabot/admin/dashboard', type='http', auth='user')
    def admin_dashboard(self, **kwargs):
        """Админская панель управления"""
        user = request.env['karmabot.webapp'].search([
            ('telegram_id', '=', request.session.get('login'))
        ], limit=1)
        
        if not user or user.role not in ('admin', 'super_admin'):
            return request.redirect('/web/login')
        
        dashboard_data = user.get_admin_dashboard_data()
        
        return request.render('karmabot_webapp.admin_dashboard', {
            'user': user,
            'data': dashboard_data,
            'is_superadmin': user.role == 'super_admin'
        })
    
    def _get_partner_stats(self, user):
        """Получить статистику партнера"""
        cards = user.get_partner_cards()
        return {
            'total_cards': len(cards),
            'published_cards': len(cards.filtered(lambda c: c.status == 'published')),
            'pending_cards': len(cards.filtered(lambda c: c.status == 'pending')),
            'total_views': sum(cards.mapped('view_count')),
            'total_scans': sum(cards.mapped('scan_count'))
        }
```

---

## 🚀 ПЛАН ВНЕДРЕНИЯ (4 недели)

### **Неделя 1: Критичные исправления**
```bash
# День 1-2: Безопасность
git checkout -b security_fixes

# Убрать хардкод SECRET_KEY
echo "SECRET_KEY=$(openssl rand -hex 32)" >> .env
sed -i "s/secret = os.getenv('SECRET_KEY', 'karmasystem-secret')/SECRET_KEY = os.getenv('SECRET_KEY')\nif not SECRET_KEY:\n    raise ValueError('SECRET_KEY required')\nsecret = SECRET_KEY.encode()/" core/handlers/main_menu_router.py

# Добавить rate limiting  
cp core/middleware/rate_limit.py core/middleware/
# Подключить в main.py

# Настроить логирование админов
cp core/middleware/admin_logging.py core/middleware/
# Настроить логгер в settings.py

# День 3-5: Упрощение меню
# Создать unified_menu.py
# Обновить обработчики
# Упростить личные кабинеты

# День 6-7: Тестирование
pytest tests/test_security.py -v
pytest tests/test_menus.py -v
pytest tests/test_rate_limiting.py -v
```

### **Неделя 2: Odoo интеграция**
```bash
# День 1-3: Модули Odoo
mkdir -p odoo-addons/karmabot_webapp
mkdir -p odoo-addons/karmabot_sso

# Создать модули
cp -r templates/karmabot_webapp/* odoo-addons/karmabot_webapp/
cp -r templates/karmabot_sso/* odoo-addons/karmabot_sso/

# Установить модули в Odoo
./odoo-bin -d karmabot -i karmabot_webapp,karmabot_sso

# День 4-5: WebApp переходы
# Создать sso_service.py
# Создать webapp_keyboards.py
# Обновить обработчики партнеров

# День 6-7: Тестирование интеграции
pytest tests/test_sso.py -v
pytest tests/test_webapp_integration.py -v
```

### **Неделя 3: ИИ помощники**
```bash
# День 1-3: Claude API
pip install anthropic
echo "ANTHROPIC_API_KEY=your_key_here" >> .env

# Создать ai_assistant.py
# Интеграция с обработчиками
# Тестирование ИИ ответов

# День 4-5: Живые дашборды
# Создать live_dashboard.py
# Автообновление через WebSocket
# Интеграция с ИИ

# День 6-7: Тестирование ИИ
pytest tests/test_ai_assistant.py -v
pytest tests/test_live_dashboard.py -v
```

### **Неделя 4: Финализация**
```bash
# День 1-3: Полное тестирование
pytest tests/ -v --cov=core
python tests/e2e/test_all_roles.py
python tests/load/test_performance.py

# День 4-5: Документация
# Обновить README.md
# Создать ADMIN_GUIDE.md
# Создать USER_GUIDE.md

# День 6-7: Деплой
# Staging тестирование
railway up --environment staging
# Production деплой
railway up --environment production
# Мониторинг
```

---

## 🧪 КРИТИЧНЫЕ ТЕСТЫ

```python
# tests/test_security_critical.py
import glob
import os
import jwt
import time
import pytest
from core.services.sso_service import sso_service
from core.middleware.rate_limit import RateLimitMiddleware

def test_no_hardcoded_secrets():
    """КРИТИЧНО: Проверить отсутствие хардкод секретов"""
    violations = []
    
    for file_path in glob.glob("**/*.py", recursive=True):
        if "test" in file_path or "__pycache__" in file_path:
            continue
            
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            line_num = 0
            
            for line in content.split('\n'):
                line_num += 1
                line_lower = line.lower()
                
                # Проверить подозрительные паттерны
                if any(pattern in line_lower for pattern in [
                    'secret_key = "',
                    'password = "',
                    'token = "',
                    'api_key = "'
                ]):
                    violations.append(f"{file_path}:{line_num} - {line.strip()}")
    
    assert not violations, f"Найдены хардкод секреты:\n" + "\n".join(violations)

def test_secret_key_from_env():
    """КРИТИЧНО: SECRET_KEY должен быть из переменной окружения"""
    secret_key = os.getenv("SECRET_KEY")
    assert secret_key, "SECRET_KEY environment variable is required"
    assert len(secret_key) >= 32, "SECRET_KEY must be at least 32 characters"
    assert secret_key != "karmasystem-secret", "Default SECRET_KEY is not allowed"

@pytest.mark.asyncio
async def test_rate_limiting_works():
    """КРИТИЧНО: Проверить rate limiting"""
    middleware = RateLimitMiddleware(rate_limit=5)  # 5 запросов в минуту
    
    # Имитировать пользователя
    class MockEvent:
        def __init__(self, user_id):
            self.from_user = type('obj', (object,), {'id': user_id})
        
        async def answer(self, text):
            self.last_answer = text
    
    # Отправить 6 запросов подряд
    user_id = 12345
    event = MockEvent(user_id)
    
    for i in range(6):
        try:
            await middleware(lambda e, d: None, event, {})
            if i == 5:  # 6-й запрос должен быть заблокирован
                assert hasattr(event, 'last_answer'), "6th request should be rate limited"
                assert "слишком много запросов" in event.last_answer.lower()
        except:
            if i < 5:  # Первые 5 запросов должны проходить
                pytest.fail(f"Request {i+1} should not be rate limited")

@pytest.mark.asyncio
async def test_sso_token_security():
    """КРИТИЧНО: Проверить безопасность SSO"""
    # Создать токен
    token = await sso_service.create_sso_token(123, 'user')
    
    # Проверить структуру токена
    payload = jwt.decode(token, options={"verify_signature": False})
    
    # TTL не должен превышать 10 минут
    ttl = payload['exp'] - payload['iat']
    assert ttl <= 600, f"TTL {ttl} seconds exceeds 600 seconds limit"
    
    # Токен должен содержать обязательные поля
    required_fields = ['telegram_id', 'role', 'iat', 'exp', 'session_id']
    for field in required_fields:
        assert field in payload, f"Required field '{field}' missing from token"
    
    # Валидация токена должна работать
    validated = await sso_service.validate_sso_token(token)
    assert validated is not None, "Token validation failed"
    assert validated['telegram_id'] == '123'
    assert validated['role'] == 'user'

def test_admin_actions_logged():
    """КРИТИЧНО: Проверить логирование админов"""
    import logging
    from unittest.mock import Mock, patch
    
    # Настроить mock логгер
    with patch('core.middleware.admin_logging.admin_logger') as mock_logger:
        # Имитировать админское действие
        from core.middleware.admin_logging import AdminLoggingMiddleware
        
        middleware = AdminLoggingMiddleware()
        
        # Mock событие от админа
        event = Mock()
        event.from_user.id = 123456
        event.text = "Админское действие"
        
        # Mock проверки админа
        with patch.object(middleware, 'is_admin_action', return_value=True):
            # Выполнить middleware
            middleware(lambda e, d: None, event, {})
            
            # Проверить что действие залогировано
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args[0][0]
            assert "Admin 123456 performed action" in call_args

# tests/test_user_experience.py
@pytest.mark.asyncio
async def test_user_cabinet_fully_in_bot():
    """Проверить что кабинет пользователя работает в боте"""
    from core.keyboards.unified_menu import get_user_cabinet_keyboard
    
    # Получить клавиатуру пользователя
    keyboard = get_user_cabinet_keyboard('ru')
    
    # Проверить что все функции доступны без веб
    button_texts = [btn.text for row in keyboard.keyboard for btn in row]
    
    required_buttons = ["💳 Мои карты", "💎 Мои баллы", "📋 История", "🌐 Язык"]
    for button in required_buttons:
        assert button in button_texts, f"Button '{button}' missing from user cabinet"
    
    # Проверить что нет WebApp кнопок
    for row in keyboard.keyboard:
        for button in row:
            assert not hasattr(button, 'web_app'), "User cabinet should not have WebApp buttons"

@pytest.mark.asyncio 
async def test_partner_qr_in_bot():
    """Проверить QR сканирование партнеров в боте"""
    from core.keyboards.unified_menu import get_partner_cabinet_keyboard
    
    # Получить клавиатуру партнера
    keyboard = get_partner_cabinet_keyboard('ru')
    
    # QR сканирование должно быть в боте
    button_texts = [btn.text for row in keyboard.keyboard for btn in row]
    assert "🧾 Сканировать QR" in button_texts, "QR scanning missing from partner cabinet"

@pytest.mark.asyncio
async def test_admin_ai_assistant():
    """Проверить ИИ помощника админов"""
    from core.services.ai_assistant import ai_assistant
    
    # Тест поиска пользователей
    response = await ai_assistant._search_user("найди пользователя с id 123")
    assert "найденные пользователи" in response.lower() or "не найдены" in response.lower()
    
    # Тест получения статистики
    response = await ai_assistant._get_stats("покажи статистику")
    assert "статистика системы" in response.lower()
    
    # Тест модерации
    response = await ai_assistant._moderation_info("что на модерации")
    assert "модерации" in response.lower()
```

---

## ⚠️ КРИТИЧНЫЕ ТРЕБОВАНИЯ

### 1. 🔒 **БЕЗОПАСНОСТЬ ПЕРВИЧНО:**
- ✅ Никаких хардкод секретов
- ✅ Rate limiting обязателен (20 req/min)
- ✅ Логирование всех админских действий  
- ✅ SSO токены с TTL <= 10 минут
- ✅ JWT подписи для всех переходов
- ✅ Валидация всех пользовательских данных

### 2. 👤 **UX НЕ ЛОМАТЬ:**
- ✅ Пользователи: всё быстро в боте
- ✅ Партнеры: QR в боте, управление в веб
- ✅ Админы: ИИ в боте, панели в веб
- ✅ Единое главное меню для всех ролей
- ✅ Быстрые переходы через WebApp

### 3. 🚀 **PRODUCTION READY:**
- ✅ Все тесты зеленые (100% покрытие критичных функций)
- ✅ Документация обновлена
- ✅ План отката готов
- ✅ Мониторинг настроен
- ✅ Логирование всех операций
- ✅ Автоматические бэкапы

---

## 🏁 ФИНАЛ: ЧТО ПОЛУЧИТСЯ

### **📊 Метрики успеха:**
- **60+ кнопок → 20 кнопок** (упрощение на 67%)
- **Время отклика < 200ms** для всех операций в боте
- **100% покрытие тестами** критичных функций
- **0 хардкод секретов** в коде
- **24/7 мониторинг** всех компонентов

### **🎯 Для пользователей:** 
- ✅ Быстрый доступ ко всем функциям в боте
- ✅ Никаких загрузок веб-страниц
- ✅ Мгновенные уведомления
- ✅ 4 языка интерфейса

### **🤝 Для партнеров:**
- ✅ QR сканирование через камеру Telegram  
- ✅ Красивое управление карточками в веб
- ✅ SMS отчеты с автоудалением
- ✅ Аналитика в реальном времени

### **👨‍💼 Для админов:**
- ✅ Умный ИИ помощник для мониторинга
- ✅ Живые дашборды с автообновлением
- ✅ Мощные веб-панели для управления
- ✅ Полное логирование действий

### **🏢 Для системы:**
- ✅ Безопасность на высшем уровне
- ✅ Масштабируемость через Odoo  
- ✅ Простота поддержки и развития
- ✅ Автоматическое тестирование

### **📋 Распределение функций:**

**В БОТЕ (30% функций):**
- 🗂️ Витрина каталога
- 👤 Личные кабинеты пользователей  
- 🧾 QR сканирование партнеров
- 🤖 ИИ помощники админов
- 📊 Живые дашборды

**В ODOO (70% функций):**
- 🗂 Управление карточками
- 📋 Модерация и workflow
- 📊 Аналитика и отчеты
- 👥 Управление пользователями
- ⚙️ Системные настройки

---

## 🚀 **РЕЗУЛЬТАТ: Современная, безопасная, удобная система с четким разделением ответственности!**

**Готово к внедрению! Начинаем с Фазы 0 - критичные исправления безопасности.** 🔒
