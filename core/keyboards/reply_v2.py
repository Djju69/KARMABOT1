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
    Главное Reply-меню согласно финальному ТЗ.
    
    Args:
        lang: Язык интерфейса
        user_id: ID пользователя для логирования
        
    Returns:
        ReplyKeyboardMarkup: Клавиатура основного меню
        
    Menu layouts:
    - New (3 rows):
      [Категории] [По районам/Рядом]
      [Помощь] [Язык]
      [Личный кабинет]
      
    - Legacy (2x2):
      [Категории] [По районам/Рядом]
      [Помощь] [Язык]
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Log feature flag status
    try:
        feature_enabled = getattr(settings.features, 'new_menu', False)
        logger.info(
            f"[MENU_DEBUG] Building menu | user_id={user_id} | "
            f"new_menu={feature_enabled} | lang={lang}"
        )
    except Exception as e:
        logger.error(f"[MENU_ERROR] Failed to check feature flag: {e}")
        feature_enabled = False
    
    # Legacy compact layout (2x2) for backward compatibility when new menu is disabled
    if not feature_enabled or not getattr(settings.features, 'new_menu', False):
        logger.info("[MENU_DEBUG] Using legacy menu layout (2x2)")
        return ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text=get_text('choose_category', lang)),
                    KeyboardButton(text=get_text('show_nearest', lang)),
                ],
                [
                    KeyboardButton(text=get_text('help', lang)),
                    KeyboardButton(text=get_text('choose_language', lang)),
                ],
            ],
            resize_keyboard=True,
            input_field_placeholder=get_text('choose_action', lang)
        )

    # New layout (3 rows) when feature flag is enabled
    menu_layout = [
        [
            KeyboardButton(text=get_text('choose_category', lang)),
            KeyboardButton(text=get_text('show_nearest', lang)),
        ],
        [
            KeyboardButton(text=get_text('help', lang)),
            KeyboardButton(text=get_text('choose_language', lang)),
        ],
        [
            KeyboardButton(text=get_text('profile', lang)),
        ]
    ]
    
    logger.debug(
        f"[MENU_DEBUG] Using new menu layout | "
        f"user_id={user_id} | buttons={[[b.text for b in row] for row in menu_layout]}"
    )
    
    return ReplyKeyboardMarkup(
        keyboard=menu_layout,
        resize_keyboard=True,
        input_field_placeholder=get_text('choose_action', lang)
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
    - Для супер-админа: скрываем «Личный кабинет», кнопка «👑 Админ кабинет».
    - Для обычного админа: оставляем «Личный кабинет», кнопка «Админ кабинет».
    """
    admin_btn_text = "👑 Админ кабинет" if is_superadmin else "Админ кабинет"

    rows: list[list[KeyboardButton]] = [
        [
            KeyboardButton(text=get_text('choose_category', lang)),
            KeyboardButton(text=get_text('show_nearest', lang)),
        ],
        [
            KeyboardButton(text=get_text('help', lang)),
            KeyboardButton(text=get_text('choose_language', lang)),
        ],
    ]

    # У обычных админов остаётся «Личный кабинет»
    if not is_superadmin:
        rows.append([KeyboardButton(text=get_text('profile', lang))])

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
    """Return to categories keyboard"""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=get_text('back_to_categories', lang))]],
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
    """Клавиатура личного кабинета пользователя с системой кармы"""
    buttons = [
        [KeyboardButton("📊 Карма"), KeyboardButton("📜 История")],
        [KeyboardButton("🔗 Привязать карту"), KeyboardButton("📋 Мои карты")],
        [KeyboardButton("🏅 Достижения"), KeyboardButton("📥 Уведомления")],
        [KeyboardButton("⚙️ Настройки"), KeyboardButton("◀️ Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_admin_keyboard(lang: str = "ru") -> ReplyKeyboardMarkup:
    """Клавиатура админа"""
    buttons = [
        [KeyboardButton("🔍 Поиск пользователей"), KeyboardButton("📊 Статистика")],
        [KeyboardButton("🚫 Забанить"), KeyboardButton("✅ Разбанить")],
        [KeyboardButton("🔗 Заблокировать карту"), KeyboardButton("📋 Очередь модерации")],
        [KeyboardButton("◀️ Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_superadmin_keyboard(lang: str = "ru") -> ReplyKeyboardMarkup:
    """Клавиатура супер-админа"""
    buttons = [
        [KeyboardButton("🧾 Выпустить карты"), KeyboardButton("🗂️ Управление картами")],
        [KeyboardButton("👥 Управление пользователями"), KeyboardButton("🤝 Управление партнёрами")],
        [KeyboardButton("🔍 Поиск"), KeyboardButton("📊 Отчёты")],
        [KeyboardButton("🗑️ Удалить карту/контакт"), KeyboardButton("◀️ Назад")]
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
        [KeyboardButton("◀️ Назад")]
    ])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

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
    'get_superadmin_keyboard'
]
