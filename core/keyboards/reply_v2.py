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

def get_main_menu_reply(lang: str = 'ru') -> ReplyKeyboardMarkup:
    """
    Главное Reply-меню согласно финальному ТЗ.
    Ряд 1: 🗂 Категории | 📍 По районам / Рядом
    Ряд 2: ❓ Помощь | 🌐 Язык
    Ряд 3: 👤 Личный кабинет
    """
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
            [
                KeyboardButton(text=get_text('profile', lang)),
            ]
        ],
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

def get_categories_keyboard(lang: str = 'ru') -> ReplyKeyboardMarkup:
    """Новая клавиатура для выбора категории (ReplyKeyboardMarkup)."""
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
                KeyboardButton(text=get_text('back_to_main_menu', lang))
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
            # Separate row for become partner action (reply button)
            [KeyboardButton(text=get_text('btn.partner.become', lang))],
            [KeyboardButton(text=t['profile_stats']), KeyboardButton(text=t['profile_settings'])],
            [KeyboardButton(text=t['back_to_main_menu'])]
        ],
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

# Export commonly used keyboards
__all__ = [
    'get_main_menu_reply',
    'get_main_menu_reply_with_qr',
    'get_return_to_main_menu',
    'get_categories_keyboard',
    'get_transport_reply_keyboard',
    'get_tours_reply_keyboard',
    'get_spa_reply_keyboard',
    'get_hotels_reply_keyboard',
    'get_shops_reply_keyboard',
    'get_language_keyboard',
    'get_profile_keyboard',
    'get_profile_keyboard_with_qr',
    'get_location_request_keyboard',
    'get_contact_request_keyboard',
    # Legacy aliases
    'return_to_main_menu',
    'get_main_menu_keyboard'
]
