from aiogram.types import ReplyKeyboardMarkup, KeyboardButton 
from core.utils.locales import translations


def get_return_to_main_menu(lang: str = 'ru') -> ReplyKeyboardMarkup:
    """Кнопка возврата в главное меню на нужном языке."""
    t = translations.get(lang, translations['ru'])
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t['back_to_main'])]
        ],
        resize_keyboard=True
    )


def get_test_restoran(lang: str = 'ru') -> ReplyKeyboardMarkup:
    """Генерация меню с выбором ресторана, района, категории и сменой языка."""
    t = translations.get(lang, translations['ru'])
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='Hải sản Mộc quán Nha Trang🦞')],
            [KeyboardButton(text=t['choose_district'])],
            [KeyboardButton(text=t['choose_category'])],
            [KeyboardButton(text=t['show_nearest'])],
            [KeyboardButton(text="🌐 Сменить язык")]
        ],
        resize_keyboard=True
    )


def get_main_menu_reply(lang: str = 'ru') -> ReplyKeyboardMarkup:
    """
    Главное меню с кнопками внизу (reply keyboard).
    Располагаем кнопки в 2 ряда по 2 кнопки:
    🗂️ Категории | 🌆 Выбор по районам
    📍 Показать ближайшие | 🌐 Сменить язык
    """
    t = translations.get(lang, translations['ru'])
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t['choose_category']), KeyboardButton(text=t['choose_district'])],
            [KeyboardButton(text=t['show_nearest']), KeyboardButton(text=t['choose_language'])]
        ],
        resize_keyboard=True
    )
