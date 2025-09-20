"""
Клавиатуры для настроек
"""
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def kb_settings_menu() -> ReplyKeyboardMarkup:
    """Клавиатура меню настроек"""
    buttons = [
        [KeyboardButton(text="🌐 Язык"), KeyboardButton(text="🔔 Уведомления")],
        [KeyboardButton(text="◀️ Назад в кабинет")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
