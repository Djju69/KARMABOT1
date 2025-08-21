from __future__ import annotations

from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery

router = Router(name=__name__)

# Basic text handlers (minimal implementations)
async def get_start(message: Message):
    # Show main menu keyboard on start
    from ..keyboards.reply_v2 import get_main_menu_reply
    await message.answer(
        "👋 Привет! Выберите язык и категорию в главном меню.",
        reply_markup=get_main_menu_reply("ru")
    )

async def get_hello(message: Message):
    await message.answer("Здравствуйте!")

async def get_inline(message: Message):
    await message.answer("Inline команды пока недоступны")

async def feedback_user(message: Message):
    await message.answer("Оставьте отзыв текстом, спасибо!")

async def hiw_user(message: Message):
    await message.answer("Как это работает: выберите категорию — получите рекомендации.")

async def main_menu(message: Message):
    from ..keyboards.reply_v2 import get_main_menu_reply
    await message.answer(
        "Главное меню: используйте кнопки ниже.",
        reply_markup=get_main_menu_reply("ru")
    )

async def user_regional_rest(message: Message):
    await message.answer("Покажем рестораны в вашем регионе.")

async def get_photo(message: Message):
    await message.answer("Фото получено.")

async def get_location(message: Message):
    await message.answer("Локация получена.")

async def get_video(message: Message):
    await message.answer("Видео получено.")

async def get_file(message: Message):
    await message.answer("Файл получен.")

# Callback handlers
async def language_callback(callback: CallbackQuery):
    await callback.message.answer("Язык будет изменен (заглушка)")
    await callback.answer()

async def main_menu_callback(callback: CallbackQuery):
    await callback.message.answer("Открываю главное меню (заглушка)")
    await callback.answer()

# Register defaults to router to ensure availability
router.message.register(get_start, CommandStart())
router.message.register(get_hello, Command("hello"))
router.message.register(main_menu, Command("menu"))

__all__ = [
    "router",
    "get_start","get_photo","get_hello","get_inline","feedback_user",
    "hiw_user","main_menu","user_regional_rest","get_location","get_video","get_file",
    "language_callback","main_menu_callback",
]
