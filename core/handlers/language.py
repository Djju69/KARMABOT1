from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import Bot

from core.utils.locales import translations
from core.utils.storage import user_language
from core.windows.main_menu import get_main_menu
from core.keyboards.reply import test_restoran

# Сопоставление текста с языковым кодом
LANG_MAP = {
    "🇷🇺 Русский": "ru",
    "🇬🇧 English": "en",
    "🇰🇷 한국어": "ko"
}

# Инлайн-клавиатура для выбора языка
def language_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='🇷🇺 Русский', callback_data='lang_ru')],
        [InlineKeyboardButton(text='🇬🇧 English', callback_data='lang_en')],
        [InlineKeyboardButton(text='🇰🇷 한국어', callback_data='lang_ko')],
    ])

# Обработка выбора языка через обычную клавиатуру
async def language_chosen(message: Message, bot: Bot):
    lang = LANG_MAP.get(message.text)
    if not lang:
        await message.answer("Пожалуйста, выберите язык с клавиатуры.")
        return
    user_language[message.from_user.id] = lang
    await message.answer(translations[lang]["start"], reply_markup=test_restoran)
    await bot.send_message(chat_id=message.chat.id, text=get_main_menu(lang), reply_markup=test_restoran)
