from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from core.utils.locales import translations

def get_return_to_main_menu(lang: str = 'ru') -> ReplyKeyboardMarkup:
    """Кнопка возврата в главное меню на нужном языке."""
    t = translations.get(lang, translations['ru'])
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t['back_to_main'])]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def get_test_restoran(lang: str = 'ru') -> ReplyKeyboardMarkup:
    """Главное меню с ресторанами, районами, категориями и сменой языка."""
    t = translations.get(lang, translations['ru'])
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='Hải sản Mộc quán Nha Trang🦞')],
            [KeyboardButton(text=t['choose_district'])],
            [KeyboardButton(text=t['choose_category'])],
            [KeyboardButton(text=t['show_nearest'])],
            [KeyboardButton(text=t['change_language'])]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def get_language_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура выбора языка."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🇷🇺 Русский"),
                KeyboardButton(text="🇬🇧 English"),
                KeyboardButton(text="🇰🇷 한국어")
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
