"""
Enhanced keyboard layouts with backward compatibility
Supports new menu structure while preserving existing functionality
"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
try:
    from aiogram.types import WebAppInfo  # aiogram v3
except Exception:
    WebAppInfo = None  # type: ignore
from typing import Optional

from ..settings import settings
from ..utils.locales_v2 import get_text, get_all_texts

def get_main_menu_reply(lang: str = 'ru', user_id: int | None = None) -> ReplyKeyboardMarkup:
    """
    Главное Reply-меню согласно канонической версии.
    
    Args:
        lang: Язык интерфейса
        user_id: ID пользователя для логирования
        
    Returns:
        ReplyKeyboardMarkup: Клавиатура основного меню
        
    Menu layout:
    [🗂️ Категории] [👥 Пригласить друзей]
    [⭐ Избранные] [❓ Помощь]
    [👤 Личный кабинет]
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=get_text("choose_category", lang)), KeyboardButton(text=get_text("keyboard.referral_program", lang))],
            [KeyboardButton(text=get_text("favorites", lang)), KeyboardButton(text=get_text("help", lang))],
            [KeyboardButton(text=get_text("profile", lang))],
        ],
        resize_keyboard=True,
        input_field_placeholder=get_text("choose_action", lang)
    )

def get_admin_keyboard(lang: str = 'ru') -> ReplyKeyboardMarkup:
    """Admin cabinet keyboard."""
    t = get_all_texts(lang)
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t['admin_menu_queue'])],
            [KeyboardButton(text=t['admin_menu_search']), KeyboardButton(text=t['admin_menu_reports'])],
            [KeyboardButton(text=t['back_to_main_menu'])]
        ],
        resize_keyboard=True,
        input_field_placeholder=get_text('choose_action', lang)
    )

def get_superadmin_keyboard(lang: str = 'ru') -> ReplyKeyboardMarkup:
    """Super-admin cabinet keyboard (can be extended with extra rows)."""
    t = get_all_texts(lang)
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t['admin_menu_queue'])],
            [KeyboardButton(text=t['admin_menu_search']), KeyboardButton(text=t['admin_menu_reports'])],
            # extra superadmin-specific entries can be added here later
            [KeyboardButton(text=t['back_to_main_menu'])]
        ],
        resize_keyboard=True,
        input_field_placeholder=get_text('choose_action', lang)
    )

def get_main_menu_reply_admin(lang: str = 'ru', is_superadmin: bool = False) -> ReplyKeyboardMarkup:
    """
    Главное Reply-меню для админов.
    - Для супер-админа: скрываем «Личный кабинет» и «Помощь», кнопка «👑 Админ кабинет».
    - Для обычного админа: оставляем «Личный кабинет» и «Помощь», кнопка «Админ кабинет».
    """
    admin_btn_text = "👑 Админ кабинет" if is_superadmin else "Админ кабинет"

    rows: list[list[KeyboardButton]] = [
        [
            KeyboardButton(text=get_text('choose_category', lang)),
            KeyboardButton(text=get_text('show_nearest', lang)),
        ],
    ]

    # Для супер-админа добавляем визуальный дашборд вместо языка
    if is_superadmin:
        rows.append([KeyboardButton(text="📊 Дашборд: Модерация(0) | Уведомления(0) | Система(OK)")])
    else:
        rows.append([KeyboardButton(text=get_text('choose_language', lang))])

    # У обычных админов остаётся «Личный кабинет» и «Помощь»
    if not is_superadmin:
        rows.append([KeyboardButton(text=get_text('profile', lang))])
        rows.append([KeyboardButton(text=get_text('help', lang))])

    # Всегда добавляем «Админ кабинет» (с короной для супер-админа)
    rows.append([KeyboardButton(text=admin_btn_text)])

    return ReplyKeyboardMarkup(
        keyboard=rows,
        resize_keyboard=True,
        input_field_placeholder=get_text('choose_action', lang)
    )

def get_spa_reply_keyboard(lang: str = 'ru') -> ReplyKeyboardMarkup:
    """Клавиатура для подменю 'SPA'."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=get_text('spa_salon', lang)),
                KeyboardButton(text=get_text('spa_massage', lang)),
                KeyboardButton(text=get_text('spa_sauna', lang)),
            ],
            [
                KeyboardButton(text=get_text('back_to_categories', lang))
            ]
        ],
        resize_keyboard=True
    )

def get_hotels_reply_keyboard(lang: str = 'ru') -> ReplyKeyboardMarkup:
    """Клавиатура для подменю 'Отели'."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=get_text('hotels_hotels', lang)),
                KeyboardButton(text=get_text('hotels_apartments', lang)),
            ],
            [
                KeyboardButton(text=get_text('back_to_categories', lang))
            ]
        ],
        resize_keyboard=True
    )

def get_main_menu_reply_with_qr(lang: str = 'ru', webapp_url: str | None = None) -> ReplyKeyboardMarkup:
    """
    Deprecated: QR WebApp button is removed per UX. Always return standard main menu without QR.
    """
    return get_main_menu_reply(lang)

def get_return_to_main_menu(lang: str = 'ru') -> ReplyKeyboardMarkup:
    """Return to main menu keyboard"""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=get_text('back_to_main_menu', lang))]],
        resize_keyboard=True
    )

def get_return_to_categories(lang: str = 'ru') -> ReplyKeyboardMarkup:
    """Return to main menu keyboard (changed from categories to main menu)"""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=get_text('back', lang))]],
        resize_keyboard=True
    )

def get_categories_keyboard(lang: str = 'ru') -> ReplyKeyboardMarkup:
    """Новая клавиатура для выбора категории (ReplyKeyboardMarkup) с кнопкой 'Назад'."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=get_text('category_restaurants', lang)),
                KeyboardButton(text=get_text('category_spa', lang)),
            ],
            [
                KeyboardButton(text=get_text('category_transport', lang)),
                KeyboardButton(text=get_text('category_hotels', lang)),
            ],
            [
                KeyboardButton(text=get_text('category_tours', lang)),
                KeyboardButton(text=get_text('category_shops_services', lang)),
            ],
            [
                KeyboardButton(text=get_text('back_to_main_menu', lang)),
            ]
        ],
        resize_keyboard=True,
        input_field_placeholder=get_text('choose_category', lang)
    )

def get_transport_reply_keyboard(lang: str = 'ru') -> ReplyKeyboardMarkup:
    """Клавиатура для подменю 'Транспорт'."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=get_text('transport_bikes', lang)),
                KeyboardButton(text=get_text('transport_cars', lang)),
                KeyboardButton(text=get_text('transport_bicycles', lang)),
            ],
            [
                KeyboardButton(text=get_text('back_to_categories', lang))
            ]
        ],
        resize_keyboard=True
    )

def get_tours_reply_keyboard(lang: str = 'ru') -> ReplyKeyboardMarkup:
    """Клавиатура для подменю 'Экскурсии'."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=get_text('tours_group', lang)),
                KeyboardButton(text=get_text('tours_private', lang)),
            ],
            [
                KeyboardButton(text=get_text('back_to_categories', lang))
            ]
        ],
        resize_keyboard=True
    )

def get_shops_reply_keyboard(lang: str = 'ru') -> ReplyKeyboardMarkup:
    """Клавиатура для подменю 'Магазины и услуги'."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=get_text('shops_shops', lang)),
                KeyboardButton(text=get_text('shops_services', lang)),
            ],
            [
                KeyboardButton(text=get_text('back_to_categories', lang))
            ]
        ],
        resize_keyboard=True
    )

def get_restaurants_reply_keyboard(lang: str = 'ru') -> ReplyKeyboardMarkup:
    """Клавиатура для подменю 'Рестораны' с фильтрами кухни."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=get_text('filter_asia', lang)),
                KeyboardButton(text=get_text('filter_europe', lang)),
            ],
            [
                KeyboardButton(text=get_text('filter_street', lang)),
                KeyboardButton(text=get_text('filter_vege', lang)),
            ],
            [
                KeyboardButton(text=get_text('restaurants_show_all', lang))
            ],
            [
                KeyboardButton(text=get_text('back_to_categories', lang))
            ]
        ],
        resize_keyboard=True
    )

def get_language_keyboard(lang: str = 'ru') -> ReplyKeyboardMarkup:
    """Language selection keyboard"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=get_text('language_ru', lang)),
                KeyboardButton(text=get_text('language_en', lang)),
            ],
            [
                KeyboardButton(text=get_text('language_vi', lang)),
                KeyboardButton(text=get_text('language_ko', lang)),
            ],
            [
                KeyboardButton(text=get_text('back_to_main_menu', lang))
            ]
        ],
        resize_keyboard=True
    )

def get_profile_keyboard(lang: str = 'ru') -> ReplyKeyboardMarkup:
    """Profile management keyboard"""
    if not settings.features.partner_fsm:
        # Fallback if partner features disabled
        t = get_all_texts(lang)
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text='🚧 Скоро доступно')],
                [KeyboardButton(text=t['back_to_main'])]
            ],
            resize_keyboard=True
        )
    
    t = get_all_texts(lang)
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t['add_card']), KeyboardButton(text=t['my_cards'])],
            # Activity entry point
            [KeyboardButton(text=get_text('actv_title', lang))],
            # Separate row for become partner action (reply button)
            [KeyboardButton(text=get_text('btn.partner.become', lang))],
            [KeyboardButton(text=t['profile_stats']), KeyboardButton(text=t['profile_settings'])],
            [KeyboardButton(text=t['back_to_main_menu'])]
        ],
        resize_keyboard=True
    )

def get_partner_keyboard(lang: str = 'ru', show_qr: bool = False) -> ReplyKeyboardMarkup:
    """Partner cabinet keyboard.
    show_qr: если True — добавляем верхнюю широкую кнопку "Сканировать QR" (WebApp при наличии).
    """
    t = get_all_texts(lang)
    rows: list[list[KeyboardButton]] = []

    if show_qr:
        # Верхняя широкая кнопка "Сканировать QR". Если доступен WebApp и включён флаг — добавим web_app.
        qr_btn: KeyboardButton
        try:
            if settings.features.qr_webapp and settings.webapp_qr_url and WebAppInfo is not None:
                qr_btn = KeyboardButton(text=get_text('menu_scan_qr', lang), web_app=WebAppInfo(url=settings.webapp_qr_url))
            else:
                qr_btn = KeyboardButton(text=get_text('menu_scan_qr', lang))
        except Exception:
            qr_btn = KeyboardButton(text=get_text('menu_scan_qr', lang))
        rows.append([qr_btn])

    rows.extend([
        [KeyboardButton(text=t['add_card']), KeyboardButton(text=t['my_cards'])],
        [KeyboardButton(text=t['profile_stats']), KeyboardButton(text=t['profile_settings'])],
        [KeyboardButton(text=t['back_to_main_menu'])],
    ])

    return ReplyKeyboardMarkup(
        keyboard=rows,
        resize_keyboard=True
    )

def get_profile_keyboard_with_qr(lang: str = 'ru', webapp_url: str | None = None) -> ReplyKeyboardMarkup:
    """
    Deprecated: QR WebApp button is removed per UX. Always return profile keyboard without QR.
    """
    return get_profile_keyboard(lang)

def get_profile_settings_keyboard(lang: str = 'ru') -> ReplyKeyboardMarkup:
    """Settings menu for profile as ReplyKeyboardMarkup (Language + Notifications)."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=get_text('choose_language', lang))],
            [KeyboardButton(text=get_text('btn.notify.on', lang)), KeyboardButton(text=get_text('btn.notify.off', lang))],
            [KeyboardButton(text=get_text('back_to_main_menu', lang))]
        ],
        resize_keyboard=True,
        input_field_placeholder=get_text('choose_action', lang)
    )

def get_location_request_keyboard(lang: str = 'ru') -> ReplyKeyboardMarkup:
    """Location request keyboard"""
    t = get_all_texts(lang)
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='📍 Отправить геолокацию', request_location=True)],
            [KeyboardButton(text=t['back_to_main_menu'])]
        ],
        resize_keyboard=True
    )

def get_contact_request_keyboard(lang: str = 'ru') -> ReplyKeyboardMarkup:
    """Contact request keyboard"""
    t = get_all_texts(lang)
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='📞 Поделиться контактом', request_contact=True)],
            [KeyboardButton(text=t['skip'])],
            [KeyboardButton(text=t['back_to_main_menu'])]
        ],
        resize_keyboard=True
    )

# Backward compatibility aliases
def return_to_main_menu(lang: str = 'ru') -> ReplyKeyboardMarkup:
    """Legacy alias for backward compatibility"""
    return get_return_to_main_menu(lang)

def get_main_menu_keyboard(lang: str = 'ru') -> ReplyKeyboardMarkup:
    """Legacy alias for backward compatibility"""
    return get_main_menu_reply(lang)

def get_user_cabinet_keyboard(lang: str = "ru") -> ReplyKeyboardMarkup:
    """Клавиатура личного кабинета пользователя"""
    buttons = [
        [KeyboardButton(text="📊 Моя карма"), KeyboardButton(text="💳 Мои карты")],
        [KeyboardButton(text="💎 Мои баллы"), KeyboardButton(text="🏪 Каталог мест")],
        [KeyboardButton(text="🏆 Достижения"), KeyboardButton(text="📋 История")],
        [KeyboardButton(text="⚙️ Настройки")],
        [KeyboardButton(text="🤝 Стать партнером"), KeyboardButton(text="❓ Помощь")],
        [KeyboardButton(text="◀️ Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_admin_keyboard(lang: str = "ru") -> ReplyKeyboardMarkup:
    """Клавиатура админа"""
    buttons = [
        [KeyboardButton(text="📋 Модерация"), KeyboardButton(text="🔍 Поиск")],
        [KeyboardButton(text="📊 Статистика"), KeyboardButton(text="👥 Пользователи")],
        [KeyboardButton(text="⚙️ Настройки"), KeyboardButton(text="❓ Помощь")],
        [KeyboardButton(text="◀️ Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_superadmin_keyboard(lang: str = "ru") -> ReplyKeyboardMarkup:
    """Клавиатура супер-админа"""
    buttons = [
        [KeyboardButton(text="📋 Модерация"), KeyboardButton(text="👥 Админы")],
        [KeyboardButton(text="🔍 Поиск"), KeyboardButton(text="📊 Статистика")],
        [KeyboardButton(text="👥 Пользователи"), KeyboardButton(text="🤝 Партнёры")],
        [KeyboardButton(text="🧾 Карты"), KeyboardButton(text="📧 Рассылка")],
        [KeyboardButton(text="⚙️ Настройки лояльности"), KeyboardButton(text="🗑️ Удаление")],
        [KeyboardButton(text="⚙️ Настройки"), KeyboardButton(text="❓ Помощь")],
        [KeyboardButton(text="◀️ Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_partner_cabinet_keyboard(lang: str = "ru", has_cards: bool = False) -> ReplyKeyboardMarkup:
    """Клавиатура кабинета партнера"""
    buttons = []
    if has_cards:
        buttons.append([KeyboardButton("🧾 Сканировать QR")])
    
    buttons.extend([
        [KeyboardButton("🗂 Мои карточки"), KeyboardButton("📊 Отчёт")],
        [KeyboardButton("📈 Статистика"), KeyboardButton("⚙️ Настройки")],
        [KeyboardButton("🌐 Язык"), KeyboardButton("❓ Помощь")],
        [KeyboardButton("◀️ Назад")]
    ])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def get_reply_keyboard(user: dict | None = None, screen: str = "main") -> ReplyKeyboardMarkup:
    """Универсальная функция для получения reply клавиатуры"""
    if not user:
        return get_main_menu_reply()
    
    role = user.get("role", "user")
    lang = user.get("lang", "ru")
    
    if screen == "main":
        if role == "admin":
            return get_admin_keyboard(lang)
        elif role == "superadmin":
            return get_superadmin_keyboard(lang)
        elif role == "partner":
            return get_partner_keyboard(lang)
        else:
            return get_main_menu_reply(lang)
    
    return get_main_menu_reply(lang)


def get_test_restoran(lang: str = "ru") -> ReplyKeyboardMarkup:
    """Тестовая клавиатура для ресторанов"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=get_text("choose_category", lang))],
            [KeyboardButton(text=get_text("back_to_main_menu", lang))],
        ],
        resize_keyboard=True,
        input_field_placeholder=get_text("choose_action", lang)
    )

# Export commonly used keyboards
__all__ = [
    'get_main_menu_reply',
    'get_main_menu_reply_admin',
    'get_user_cabinet_keyboard',
    'get_partner_cabinet_keyboard',
    'get_main_menu_reply_with_qr',
    'get_return_to_main_menu',
    'get_return_to_categories',
    'get_categories_keyboard',
    'get_transport_reply_keyboard',
    'get_tours_reply_keyboard',
    'get_spa_reply_keyboard',
    'get_hotels_reply_keyboard',
    'get_shops_reply_keyboard',
    'get_restaurants_reply_keyboard',
    'get_language_keyboard',
    'get_profile_keyboard',
    'get_profile_keyboard_with_qr',
    'get_location_request_keyboard',
    'get_contact_request_keyboard',
    # Legacy aliases
    'return_to_main_menu',
    'get_main_menu_keyboard',
    'get_partner_keyboard',
    'get_admin_keyboard',
    'get_superadmin_keyboard',
    # New functions
    'get_reply_keyboard',
    'get_test_restoran'
]
