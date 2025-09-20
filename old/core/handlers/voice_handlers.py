"""
Обработчики голосовых сообщений для AI-помощника
Интегрируется с существующей системой поддержки
"""

import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from core.services.voice_service import voice_service
from core.utils.locales_v2 import get_text
from core.settings import settings

logger = logging.getLogger(__name__)
router = Router()

# Импортируем состояния поддержки (если они существуют)
try:
    from core.fsm.support_states import SupportStates
except ImportError:
    # Создаем заглушку для состояний поддержки
    class SupportStates:
        chatting = "chatting"

@router.message(StateFilter(SupportStates.chatting), F.voice)
@router.message(StateFilter(SupportStates.chatting), F.audio)
async def handle_voice_message(message: Message, bot: Bot, state: FSMContext):
    """Обработчик голосовых сообщений"""
    
    # Проверка фичи
    if not settings.features.support_voice:
        logger.debug("Voice feature disabled, ignoring voice message")
        return
    
    user_id = message.from_user.id
    logger.info(f"Processing voice message from user {user_id}")
    
    try:
        # Отправляем сообщение о обработке
        processing_msg = await message.answer(get_text('voice.processing', 'ru'))
        
        # Обрабатываем голосовое сообщение
        text, language, error_code = await voice_service.process_voice_message(bot, message)
        
        # Удаляем сообщение о обработке
        await processing_msg.delete()
        
        if error_code:
            await _handle_voice_error(message, error_code)
            return
        
        if not text:
            await _handle_voice_error(message, "couldnt_understand")
            return
        
        # Показываем распознанный текст
        await message.answer(
            f"🎤 **Распознано:**\n{text}\n\n"
            f"🌐 **Язык:** {language}\n\n"
            f"Обрабатываю ваш запрос..."
        )
        
        # Передаем текст в существующий AI-помощник
        await _process_ai_request(message, text, language, state)
        
    except Exception as e:
        logger.error(f"Error handling voice message: {e}")
        await message.answer("❌ Произошла ошибка при обработке голосового сообщения")

async def _handle_voice_error(message: Message, error_code: str):
    """Обработка ошибок голосового ввода"""
    
    error_messages = {
        "too_long": get_text('voice.too_long', 'ru'),
        "too_large": get_text('voice.too_large', 'ru'),
        "rate_limit": get_text('voice.rate_limit', 'ru'),
        "couldnt_understand": get_text('voice.couldnt_understand', 'ru'),
        "download_error": "❌ Ошибка загрузки файла",
        "conversion_error": "❌ Ошибка конвертации аудио",
        "transcription_error": "❌ Ошибка распознавания речи",
        "processing_error": "❌ Ошибка обработки"
    }
    
    error_text = error_messages.get(error_code, "❌ Неизвестная ошибка")
    
    # Для некоторых ошибок показываем кнопку повтора
    if error_code in ["couldnt_understand", "transcription_error"]:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=get_text('voice.btn_retry', 'ru'),
                callback_data="voice_retry"
            )]
        ])
        await message.answer(error_text, reply_markup=keyboard)
    else:
        await message.answer(error_text)

@router.callback_query(F.data == "voice_retry")
async def handle_voice_retry(callback: CallbackQuery):
    """Обработчик кнопки повтора голосового сообщения"""
    await callback.message.edit_text(
        "🎤 Отправьте голосовое сообщение еще раз"
    )
    await callback.answer()

async def _process_ai_request(message: Message, text: str, language: str, state: FSMContext):
    """Обработка запроса к AI-помощнику"""
    
    try:
        # Здесь должна быть интеграция с существующим AI-сервисом
        # Пока что создаем заглушку
        
        # Импортируем существующий сервис поддержки (если есть)
        try:
            from core.services.support_ai_service import support_ai_service
            
            # Получаем ответ от AI
            answer = await support_ai_service.answer(
                user_id=message.from_user.id,
                question=text,
                lang_hint=language
            )
            
            await message.answer(answer)
            
        except ImportError:
            # Заглушка если сервис поддержки не существует
            await message.answer(
                f"🤖 **AI-помощник получил ваш запрос:**\n\n"
                f"📝 **Текст:** {text}\n"
                f"🌐 **Язык:** {language}\n\n"
                f"⚠️ Сервис AI-помощника временно недоступен"
            )
            
    except Exception as e:
        logger.error(f"Error processing AI request: {e}")
        await message.answer("❌ Ошибка при обработке запроса к AI-помощнику")

# Обработчик для команды /help с голосовым вводом
@router.message(F.text.in_([get_text('menu.help', 'ru'), get_text('menu.help', 'en')]))
async def handle_help_with_voice(message: Message, state: FSMContext):
    """Обработчик команды помощи с поддержкой голосового ввода"""
    
    # Проверяем фичу голосового ввода
    if settings.features.support_voice:
        help_text = (
            "📚 **Справочный центр**\n\n"
            "Доступные команды:\n"
            "• Текстовые сообщения\n"
            "• 🎤 Голосовые сообщения (до 60 сек)\n\n"
            "Отправьте голосовое сообщение для быстрого доступа к AI-помощнику!"
        )
    else:
        help_text = (
            "📚 **Справочный центр**\n\n"
            "Отправьте текстовое сообщение для получения помощи"
        )
    
    await message.answer(help_text)
    
    # Устанавливаем состояние для поддержки
    await state.set_state(SupportStates.chatting)

# Обработчик для начала чата с поддержкой
@router.message(F.text.in_(["🤖 Задать вопрос ИИ", "🤖 Ask AI question"]))
async def start_ai_chat(message: Message, state: FSMContext):
    """Начало чата с AI-помощником"""
    
    if settings.features.support_voice:
        welcome_text = (
            "🤖 **AI-помощник готов помочь!**\n\n"
            "Вы можете:\n"
            "• Написать текстовое сообщение\n"
            "• 🎤 Отправить голосовое сообщение\n\n"
            "Задавайте любые вопросы о системе!"
        )
    else:
        welcome_text = (
            "🤖 **AI-помощник готов помочь!**\n\n"
            "Напишите ваш вопрос текстом"
        )
    
    await message.answer(welcome_text)
    await state.set_state(SupportStates.chatting)

# Обработчик для выхода из чата поддержки
@router.message(F.text.in_(["◀️ Назад", "◀️ Back"]))
async def exit_support_chat(message: Message, state: FSMContext):
    """Выход из чата поддержки"""
    await state.clear()
    await message.answer("👋 Чат с поддержкой завершен")
