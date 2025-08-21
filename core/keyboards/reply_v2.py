"""
Enhanced keyboard layouts with backward compatibility
Supports new menu structure while preserving existing functionality
"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from typing import Optional

from ..settings import settings
from ..utils.locales_v2 import get_text, get_all_texts

def get_main_menu_reply(lang: str = 'ru') -> ReplyKeyboardMarkup:
    """
    Get main menu keyboard with backward compatibility
    Falls back to legacy layout if new menu feature is disabled
    """
    t = get_all_texts(lang)
    
    if not settings.features.new_menu:
        # Legacy 2x2 layout for backward compatibility
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text=t['choose_category']), KeyboardButton(text=t['show_nearest'])],
                [KeyboardButton(text=t['choose_district']), KeyboardButton(text=t['choose_language'])]
            ],
            resize_keyboard=True
        )
    
    # New 3x2 layout as per TZ requirements
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t['choose_category']), KeyboardButton(text=t['profile'])],
            [KeyboardButton(text=t['choose_district']), KeyboardButton(text=t['show_nearest'])],
            [KeyboardButton(text=t['help']), KeyboardButton(text=t['choose_language'])]
        ],
        resize_keyboard=True
    )

def get_return_to_main_menu(lang: str = 'ru') -> ReplyKeyboardMarkup:
    """Return to main menu keyboard"""
    t = get_all_texts(lang)
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t['back_to_main'])]],
        resize_keyboard=True
    )

def get_categories_keyboard(lang: str = 'ru') -> ReplyKeyboardMarkup:
    """Categories selection keyboard"""
    t = get_all_texts(lang)
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='🍜 Рестораны'), KeyboardButton(text='🧘 SPA и массаж')],
            [KeyboardButton(text='🛵 Аренда байков'), KeyboardButton(text='🏨 Отели')],
            [KeyboardButton(text='🗺️ Экскурсии')],
            [KeyboardButton(text=t['show_nearest'])],
            [KeyboardButton(text=t['back_to_main'])]
        ],
        resize_keyboard=True
    )

def get_language_keyboard() -> ReplyKeyboardMarkup:
    """Language selection keyboard"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='🇷🇺 Русский'), KeyboardButton(text='🇺🇸 English')],
            [KeyboardButton(text='🇻🇳 Tiếng Việt'), KeyboardButton(text='🇰🇷 한국어')],
            [KeyboardButton(text='🔙 Назад')]
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
            [KeyboardButton(text=t['profile_stats']), KeyboardButton(text=t['profile_settings'])],
            [KeyboardButton(text=t['back_to_main'])]
        ],
        resize_keyboard=True
    )

def get_location_request_keyboard(lang: str = 'ru') -> ReplyKeyboardMarkup:
    """Location request keyboard"""
    t = get_all_texts(lang)
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='📍 Отправить геолокацию', request_location=True)],
            [KeyboardButton(text=t['back_to_main'])]
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
            [KeyboardButton(text=t['back_to_main'])]
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
    'get_return_to_main_menu', 
    'get_categories_keyboard',
    'get_language_keyboard',
    'get_profile_keyboard',
    'get_location_request_keyboard',
    'get_contact_request_keyboard',
    # Legacy aliases
    'return_to_main_menu',
    'get_main_menu_keyboard'
]
