"""
Обработчик help с кнопкой AI-ассистента
"""
import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from core.ui.kb_support_ai import kb_support_ai
from core.services.user_service import get_user_role
from core.services.help_service import HelpService

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Обработчик команды /help с кнопкой AI"""
    try:
        # Получаем роль пользователя
        user_role = await get_user_role(message.from_user.id)
        
        # Получаем текст помощи для роли
        help_service = HelpService()
        text = await help_service.get_help_message(message.from_user.id)
        
        # Отправляем с кнопкой AI
        await message.answer(text, reply_markup=kb_support_ai(), parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Error in help command: {e}")
        await message.answer(
            "❌ Произошла ошибка при получении справки. Попробуйте позже.",
            reply_markup=kb_support_ai()
        )


@router.message(F.text.casefold() == "помощь")
async def txt_help(message: Message):
    """Обработчик текста 'помощь' с кнопкой AI"""
    try:
        # Получаем роль пользователя
        user_role = await get_user_role(message.from_user.id)
        
        # Получаем текст помощи для роли
        help_service = HelpService()
        text = await help_service.get_help_message(message.from_user.id)
        
        # Отправляем с кнопкой AI
        await message.answer(text, reply_markup=kb_support_ai(), parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Error in help text: {e}")
        await message.answer(
            "❌ Произошла ошибка при получении справки. Попробуйте позже.",
            reply_markup=kb_support_ai()
        )


@router.message(F.text == "❓ Помощь")
async def txt_help_button(message: Message):
    """Обработчик кнопки '❓ Помощь' с кнопкой AI"""
    try:
        logger.info(f"🔍 Help button pressed by user {message.from_user.id}")
        
        # Получаем роль пользователя
        user_role = await get_user_role(message.from_user.id)
        logger.info(f"🔍 User role: {user_role}")
        
        # Получаем текст помощи для роли
        help_service = HelpService()
        text = await help_service.get_help_message(message.from_user.id)
        logger.info(f"🔍 Help text length: {len(text)}")
        
        # Отправляем с кнопкой AI
        await message.answer(text, reply_markup=kb_support_ai(), parse_mode="HTML")
        logger.info("✅ Help message sent successfully")
        
    except Exception as e:
        logger.error(f"Error in help button: {e}", exc_info=True)
        await message.answer(
            "❌ Произошла ошибка при получении справки. Попробуйте позже.",
            reply_markup=kb_support_ai()
        )
