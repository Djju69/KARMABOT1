"""
Обработчик настроек
"""
import logging
from aiogram import Router, F
from aiogram.types import Message
from core.ui.kb_settings import kb_settings_menu
from core.handlers.language import build_language_inline_kb
from core.services.support_ai_service import SupportAIService

logger = logging.getLogger(__name__)
router = Router()

# Инициализируем AI сервис
support_ai = SupportAIService()


@router.message(F.text == "⚙️ Настройки")
async def settings_handler(message: Message):
    """Обработчик кнопки настроек"""
    try:
        await message.answer(
            "⚙️ <b>Настройки</b>\n\nВыберите что хотите настроить:",
            reply_markup=kb_settings_menu(),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error in settings_handler: {str(e)}", exc_info=True)
        await message.answer(
            "❌ Не удалось загрузить настройки. Пожалуйста, попробуйте позже."
        )


@router.message(F.text == "🌐 Язык")
async def language_handler(message: Message):
    """Обработчик выбора языка"""
    try:
        logger.info(f"Language handler called for user {message.from_user.id}")
        keyboard = build_language_inline_kb()
        logger.info(f"Language keyboard created: {keyboard}")
        
        await message.answer(
            "🌐 <b>Выбор языка</b>\n\nВыберите язык интерфейса:",
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        logger.info("Language selection message sent successfully")
        
    except Exception as e:
        logger.error(f"Error in language_handler: {str(e)}", exc_info=True)
        await message.answer(
            "❌ Не удалось загрузить выбор языка. Пожалуйста, попробуйте позже.",
            reply_markup=kb_settings_menu()
        )


@router.message(F.text == "🔔 Уведомления")
async def notifications_handler(message: Message):
    """Обработчик уведомлений"""
    try:
        # Get user language
        lang = getattr(message.from_user, 'language_code', 'ru') or 'ru'
        
        # Get AI response for notification management
        reply = await support_ai.answer(message.from_user.id, "уведомления", lang)
        
        # Send response
        await message.answer(
            reply,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in notifications handler: {e}")
        await message.answer(
            "❌ Произошла ошибка при получении настроек уведомлений. Попробуйте позже.",
            reply_markup=kb_settings_menu()
        )


@router.message(F.text == "◀️ Назад в кабинет")
async def back_to_cabinet_handler(message: Message):
    """Обработчик возврата в кабинет"""
    try:
        from core.handlers.cabinet_router import user_cabinet_handler
        await user_cabinet_handler(message)
    except Exception as e:
        logger.error(f"Error in back_to_cabinet_handler: {str(e)}", exc_info=True)
        await message.answer(
            "❌ Не удалось вернуться в кабинет. Пожалуйста, попробуйте позже."
        )
