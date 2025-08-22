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
    Главное Reply-меню (фикс из ТЗ):
    [🗂 Категории] [👤 Личный кабинет]
    [📍 Районы/Рядом] [❓ Помощь]
    """
    # Legacy 2x2 when feature flag is off
    if not settings.features.new_menu:
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text='🗂 Категории'), KeyboardButton(text='👤 Личный кабинет')],
                [KeyboardButton(text='📍 По районам / Рядом'), KeyboardButton(text='❓ Помощь')]
            ],
            resize_keyboard=True
        )

    # New layout (with language button)
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='🗂 Категории'), KeyboardButton(text='🌐 Язык')],
            [KeyboardButton(text='📍 По районам / Рядом'), KeyboardButton(text='❓ Помощь')],
            [KeyboardButton(text='👤 Личный кабинет')]
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
