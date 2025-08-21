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

# ==== Language & Help (Phase 1) ====
from ..keyboards.inline_v2 import get_language_inline
from ..utils.locales_v2 import get_text
from ..settings import settings


@router.message(F.text == "🌐 Язык")
async def on_language_menu(message: Message):
    lang = getattr(settings, 'default_lang', 'ru')
    await message.answer(
        get_text('choose_language', lang),
        reply_markup=get_language_inline(active=lang)
    )


@router.callback_query(F.data.regexp(r"^lang:set:(ru|en|vi|ko)$"))
async def on_language_set(callback: CallbackQuery):
    # TODO: сохранить язык в профиле пользователя (Redis/DB)
    _, _, lang = callback.data.split(":")
    await callback.message.edit_text(
        get_text('choose_language', lang)
    )
    await callback.message.edit_reply_markup(reply_markup=get_language_inline(active=lang))
    await callback.answer("Язык обновлён")


@router.message(F.text == "❓ Помощь")
async def on_help(message: Message):
    lang = getattr(settings, 'default_lang', 'ru')
    help_text = get_text('help_main', lang)

    # Append docs/support if available
    pdf_user = getattr(settings, f'pdf_user_{lang}', '')
    pdf_partner = getattr(settings, f'pdf_partner_{lang}', '')
    support = getattr(settings, 'support_tg', '')

    extras = []
    if pdf_user:
        extras.append(f"📄 User PDF: {pdf_user}")
    if pdf_partner:
        extras.append(f"📄 Partner PDF: {pdf_partner}")
    if support:
        extras.append(f"🆘 Support: {support}")

    text = help_text + ("\n\n" + "\n".join(extras) if extras else "")
    await message.answer(text)

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
