"""
Обработчик команды /help и кнопки помощи
"""

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from core.services.help_service import HelpService
from core.utils.locales_v2 import get_text

logger = logging.getLogger(__name__)
router = Router()

# Инициализируем сервис помощи
help_service = HelpService()

@router.message(Command("help"))
async def help_command_handler(message: Message):
    """Обработчик команды /help"""
    try:
        user_id = message.from_user.id
        
        # Получаем справочное сообщение
        help_message = await help_service.get_help_message(user_id)
        
        # Отправляем сообщение с поддержкой HTML
        await message.answer(
            help_message,
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        
        logger.info(f"Help command executed by user {user_id}")
        
    except Exception as e:
        logger.error(f"Error in help command handler: {e}")
        await message.answer(
            "❌ Произошла ошибка при загрузке справочной информации.\n\n"
            "Попробуйте позже или обратитесь в поддержку: @karma_system_official"
        )

@router.callback_query(F.data == "help")
async def help_button_handler(callback: CallbackQuery):
    """Обработчик кнопки помощи"""
    try:
        user_id = callback.from_user.id
        
        # Получаем справочное сообщение
        help_message = await help_service.get_help_message(user_id)
        
        # Отправляем сообщение с поддержкой HTML
        await callback.message.edit_text(
            help_message,
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        
        # Подтверждаем callback
        await callback.answer()
        
        logger.info(f"Help button clicked by user {user_id}")
        
    except Exception as e:
        logger.error(f"Error in help button handler: {e}")
        await callback.answer(
            "❌ Произошла ошибка при загрузке справочной информации",
            show_alert=True
        )
