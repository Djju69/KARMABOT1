# core/keyboards/reply/language.py

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

language_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton("🇷🇺 Русский"), KeyboardButton("🇬🇧 English"), KeyboardButton("🇰🇷 한국어")]
    ],
    resize_keyboard=True
)
