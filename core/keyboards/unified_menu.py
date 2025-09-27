"""
Унифицированные клавиатуры для всех ролей согласно архитектурному плану рефакторинга
"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from core.utils.locales_v2 import get_text


def get_universal_main_menu(lang: str = 'ru') -> ReplyKeyboardMarkup:
    """
    Единое главное меню для всех ролей (USER, PARTNER, ADMIN, SUPER_ADMIN)
    
    Согласно архитектурному плану:
    - 🗂️ Категории (витрина для всех)
    - 👥 Пригласить друзей (реферальная программа)
    - ⭐ Избранные (сохраненные карточки)
    - ❓ Помощь (справка и поддержка)
    - 👤 Личный кабинет (роль-специфичный кабинет)
    
    Args:
        lang: Язык интерфейса
        
    Returns:
        ReplyKeyboardMarkup: Унифицированное главное меню
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=get_text("choose_category", lang)),
                KeyboardButton(text=get_text("keyboard.referral_program", lang))
            ],
            [
                KeyboardButton(text=get_text("favorites", lang)),
                KeyboardButton(text=get_text("help", lang))
            ],
            [
                KeyboardButton(text=get_text("gamification.achievements", lang)),
                KeyboardButton(text=get_text("choose_language", lang))
            ],
            [
                KeyboardButton(text=get_text("menu.profile", lang))
            ]
        ],
        resize_keyboard=True,
        input_field_placeholder=get_text("choose_action", lang)
    )


def get_user_cabinet_keyboard(lang: str = 'ru') -> ReplyKeyboardMarkup:
    """
    Личный кабинет пользователя (100% в боте)
    
    Функции:
    - 💳 Мои карты: добавление по номеру/QR/виртуальная
    - 💎 Мои баллы: просмотр/списание, конвертация в скидки
    - 📋 История: операции по баллам/картам + SMS уведомления
    - 🌐 Язык: переключение между RU/EN/VI/KO
    - ◀️ Назад: возврат в главное меню
    
    Args:
        lang: Язык интерфейса
        
    Returns:
        ReplyKeyboardMarkup: Клавиатура кабинета пользователя
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=get_text("my_cards", lang)),
                KeyboardButton(text=get_text("my_points", lang))
            ],
            [
                KeyboardButton(text=get_text("history", lang))
            ],
            [
                KeyboardButton(text=get_text("language", lang))
            ],
            [
                KeyboardButton(text=get_text("common.back_simple", lang))
            ]
        ],
        resize_keyboard=True,
        input_field_placeholder=get_text("user_cabinet_placeholder", lang)
    )


def get_partner_cabinet_keyboard(lang: str = 'ru') -> ReplyKeyboardMarkup:
    """
    Партнерский кабинет (гибрид: QR в боте, управление в Odoo)
    
    Функции:
    - 🧾 Сканировать QR: В БОТЕ (камера Telegram)
    - 🗂 Мои карточки: → Odoo WebApp (красивое управление)
    - ➕ Добавить карточку: → Odoo WebApp (формы создания)
    - 📊 Отчёт: SMS из Odoo (автоудаление через 5 мин)
    - ◀️ Назад: возврат в главное меню
    
    Args:
        lang: Язык интерфейса
        
    Returns:
        ReplyKeyboardMarkup: Клавиатура кабинета партнера
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=get_text("scan_qr", lang))
            ],
            [
                KeyboardButton(text=get_text("my_cards", lang)),
                KeyboardButton(text=get_text("add_card", lang))
            ],
            [
                KeyboardButton(text=get_text("daily_report", lang))
            ],
            [
                KeyboardButton(text=get_text("common.back_simple", lang))
            ]
        ],
        resize_keyboard=True,
        input_field_placeholder=get_text("partner_cabinet_placeholder", lang)
    )


def get_admin_cabinet_keyboard(role: str = 'admin', lang: str = 'ru') -> ReplyKeyboardMarkup:
    """
    Админский кабинет (ИИ в боте + WebApp панели)
    
    Функции:
    - 🗂️ Категории: витрина (остается в боте)
    - 🤖 ИИ Помощник: В БОТЕ (умный поиск/отчёты/мониторинг)
    - 📊 Дашборды: В БОТЕ (живые счетчики модерации/уведомлений)
    - 👤 Админ кабинет: → Odoo WebApp (полная панель управления)
    - ❓ Помощь: справка
    
    Args:
        role: Роль админа ('admin' или 'super_admin')
        lang: Язык интерфейса
        
    Returns:
        ReplyKeyboardMarkup: Клавиатура кабинета админа
    """
    if role == 'super_admin':
        return ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text=get_text("choose_category", lang)),
                    KeyboardButton(text=get_text("ai_assistant", lang))
                ],
                [
                    KeyboardButton(text=get_text("dashboard_moderation", lang)),
                    KeyboardButton(text=get_text("dashboard_notifications", lang)),
                    KeyboardButton(text=get_text("dashboard_system", lang))
                ],
                [
                    KeyboardButton(text="🧪 Тестовые данные")
                ],
                [
                    KeyboardButton(text=get_text("super_admin_cabinet", lang))
                ],
                [
                    KeyboardButton(text=get_text("help", lang))
                ]
            ],
            resize_keyboard=True,
            input_field_placeholder=get_text("super_admin_cabinet_placeholder", lang)
        )
    else:  # admin
        return ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text=get_text("choose_category", lang)),
                    KeyboardButton(text=get_text("ai_assistant", lang))
                ],
                [
                    KeyboardButton(text=get_text("dashboard_moderation", lang)),
                    KeyboardButton(text=get_text("dashboard_notifications", lang))
                ],
                [
                    KeyboardButton(text=get_text("admin_cabinet", lang))
                ],
                [
                    KeyboardButton(text=get_text("help", lang))
                ]
            ],
            resize_keyboard=True,
            input_field_placeholder=get_text("admin_cabinet_placeholder", lang)
        )


def get_role_based_cabinet(user_role: str, lang: str = 'ru') -> ReplyKeyboardMarkup:
    """
    Получить кабинет в зависимости от роли пользователя
    
    Args:
        user_role: Роль пользователя ('user', 'partner', 'admin', 'super_admin')
        lang: Язык интерфейса
        
    Returns:
        ReplyKeyboardMarkup: Соответствующий кабинет
    """
    if user_role == 'user':
        return get_user_cabinet_keyboard(lang)
    elif user_role == 'partner':
        return get_partner_cabinet_keyboard(lang)
    elif user_role in ('admin', 'super_admin'):
        return get_admin_cabinet_keyboard(user_role, lang)
    else:
        # По умолчанию - кабинет пользователя
        return get_user_cabinet_keyboard(lang)


def get_settings_keyboard(lang: str = 'ru') -> ReplyKeyboardMarkup:
    """
    Клавиатура настроек (общая для всех ролей)
    
    Args:
        lang: Язык интерфейса
        
    Returns:
        ReplyKeyboardMarkup: Клавиатура настроек
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=get_text("language", lang)),
                KeyboardButton(text=get_text("notifications", lang))
            ],
            [
                KeyboardButton(text=get_text("privacy", lang)),
                KeyboardButton(text=get_text("about", lang))
            ],
            [
                KeyboardButton(text=get_text("common.back_simple", lang))
            ]
        ],
        resize_keyboard=True,
        input_field_placeholder=get_text("settings_placeholder", lang)
    )


def get_help_keyboard(lang: str = 'ru') -> ReplyKeyboardMarkup:
    """
    Клавиатура помощи (общая для всех ролей)
    
    Args:
        lang: Язык интерфейса
        
    Returns:
        ReplyKeyboardMarkup: Клавиатура помощи
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=get_text("faq", lang)),
                KeyboardButton(text=get_text("contact_support", lang))
            ],
            [
                KeyboardButton(text=get_text("tutorial", lang)),
                KeyboardButton(text=get_text("feedback", lang))
            ],
            [
                KeyboardButton(text=get_text("common.back_simple", lang))
            ]
        ],
        resize_keyboard=True,
        input_field_placeholder=get_text("help_placeholder", lang)
    )


# Константы для проверки текста кнопок
UNIVERSAL_MAIN_MENU_BUTTONS = [
    "choose_category", "keyboard.referral_program", 
    "favorites", "help", "menu.profile"
]

USER_CABINET_BUTTONS = [
    "my_cards", "my_points", "history", "language", "common.back_simple"
]

PARTNER_CABINET_BUTTONS = [
    "scan_qr", "my_cards", "add_card", "daily_report", "common.back_simple"
]

ADMIN_CABINET_BUTTONS = [
    "choose_category", "ai_assistant", "dashboard_moderation", 
    "dashboard_notifications", "admin_cabinet", "help"
]

SUPER_ADMIN_CABINET_BUTTONS = [
    "choose_category", "ai_assistant", "dashboard_moderation", 
    "dashboard_notifications", "dashboard_system", "super_admin_cabinet", "help"
]

