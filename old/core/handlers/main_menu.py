"""
Обработчики главного меню и профилей пользователей.
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from core.keyboards.reply_v2 import get_main_menu_reply
from core.utils.locales import get_text

router = Router(name="main_menu")

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Обработчик команды /start"""
    await state.clear()
    
    # Приветственное сообщение
    welcome_text = get_text("welcome.message", message.from_user.language_code or "ru")
    
    # Получаем клавиатуру главного меню
    kb = get_main_menu_reply(message.from_user.language_code or "ru")
    
    await message.answer(welcome_text, reply_markup=kb)

@router.message(F.text == get_text("keyboard.profile", "ru"))
async def show_profile(message: Message, state: FSMContext):
    """Показ профиля пользователя"""
    user = message.from_user
    profile_text = get_text("profile.info", user.language_code or "ru").format(
        username=user.full_name,
        user_id=user.id,
        status="Партнёр" if user.id == 12345678 else "Пользователь"  # Пример проверки на партнёра
    )
    
    await message.answer(profile_text)

@router.message(F.text == "🎫 QR-коды")
async def show_qr_codes_menu(message: Message, state: FSMContext):
    """Показ меню QR-кодов"""
    from core.handlers.qr_code_handlers import show_qr_codes_menu as qr_menu
    await qr_menu(message, state)
