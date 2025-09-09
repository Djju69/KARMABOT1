"""
Обработчик AI-ассистента "Карма"
"""
import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from core.fsm.support_states import SupportStates
from core.services.support_ai_service import SupportAIService
from core.services.report_service import ReportService
from core.services.stt_service import STTService
from core.ui.kb_support_ai import kb_ai_controls
from core.utils.rate_limit import rate_limiter
from core.i18n import get_text
from core.settings import settings

logger = logging.getLogger(__name__)
router = Router()

# Инициализация сервисов
support_ai = SupportAIService()
report_service = ReportService()
stt_service = STTService()


@router.message(Command("support"))
async def cmd_support(message: Message, state: FSMContext):
    """Скрытая команда /support для прямого запуска AI"""
    try:
        # Проверяем feature flag
        if not settings.features.support_ai:
            await message.answer("🤖 AI-ассистент временно недоступен.")
            return
        
        # Проверяем лимиты
        if not rate_limiter.is_allowed_ai_message(message.from_user.id):
            await message.answer("⏰ Слишком много запросов. Подождите минуту.")
            return
        
        # Устанавливаем состояние
        await state.set_state(SupportStates.chatting)
        
        # Приветствие
        welcome_text = get_text("support_ai_hi", "ru")
        await message.answer(welcome_text, reply_markup=kb_ai_controls())
        
    except Exception as e:
        logger.error(f"Error in support command: {e}")
        await message.answer("❌ Ошибка запуска AI. Попробуйте позже.")


@router.callback_query(F.data == "support_ai_start")
async def support_ai_start(cb: CallbackQuery, state: FSMContext):
    """Запуск AI-ассистента"""
    try:
        # Проверяем лимиты
        if not rate_limiter.is_allowed_ai_message(cb.from_user.id):
            await cb.answer("⏰ Слишком много запросов. Подождите минуту.", show_alert=True)
            return
        
        # Устанавливаем состояние
        await state.set_state(SupportStates.chatting)
        
        # Приветствие
        welcome_text = get_text("support_ai_hi", "ru")
        await cb.message.answer(welcome_text, reply_markup=kb_ai_controls())
        await cb.answer()
        
    except Exception as e:
        logger.error(f"Error starting AI: {e}")
        await cb.answer("❌ Ошибка запуска AI. Попробуйте позже.", show_alert=True)


@router.callback_query(F.data == "support_ai_exit")
async def support_ai_exit(cb: CallbackQuery, state: FSMContext):
    """Выход из AI-режима"""
    try:
        await state.set_state(SupportStates.idle)
        await cb.message.answer("👋 До свидания! Обращайтесь, если нужна помощь.")
        await cb.answer()
        
    except Exception as e:
        logger.error(f"Error exiting AI: {e}")
        await cb.answer("❌ Ошибка выхода. Попробуйте позже.", show_alert=True)


@router.callback_query(F.data == "support_ai_escalate")
async def support_ai_escalate(cb: CallbackQuery, state: FSMContext):
    """Эскалация в админ-чат"""
    try:
        # В реальной реализации здесь будет отправка в админ-чат
        await cb.message.answer("📨 Ваш вопрос передан администратору. Он свяжется с вами.")
        await cb.answer("✅ Вопрос передан администратору")
        
    except Exception as e:
        logger.error(f"Error escalating: {e}")
        await cb.answer("❌ Ошибка эскалации. Попробуйте позже.", show_alert=True)


@router.message(SupportStates.chatting, F.text)
async def support_ai_chat(message: Message, state: FSMContext):
    """Обработка текстовых сообщений в AI-режиме"""
    try:
        # Проверяем лимиты
        if not rate_limiter.is_allowed_ai_message(message.from_user.id):
            await message.answer("⏰ Слишком много запросов. Подождите минуту.")
            return
        
        # Получаем ответ от AI
        reply = await support_ai.answer(message.from_user.id, message.text)
        
        # Отправляем ответ
        await message.answer(reply, reply_markup=kb_ai_controls())
        
    except Exception as e:
        logger.error(f"Error in AI chat: {e}")
        await message.answer("❌ Произошла ошибка. Попробуйте переформулировать вопрос.")


@router.message(SupportStates.chatting, F.voice)
async def support_ai_voice(message: Message, state: FSMContext):
    """Обработка голосовых сообщений в AI-режиме"""
    try:
        # Проверяем feature flag
        if not getattr(settings, 'FEATURE_SUPPORT_VOICE', False):
            await message.answer("🎤 Голосовые сообщения временно недоступны.")
            return
        
        # Проверяем лимиты
        if not rate_limiter.is_allowed_voice(message.from_user.id):
            await message.answer("⏰ Слишком много голосовых сообщений. Подождите минуту.")
            return
        
        # Показываем, что обрабатываем
        processing_msg = await message.answer("🎧 Слушаю… секунду")
        
        try:
            # Подготавливаем аудио
            audio_path, meta = await stt_service.prepare_audio(message)
            
            # Транскрибируем
            text, lang, confidence = await stt_service.transcribe(audio_path)
            
            if not text or confidence < 0.4:
                await processing_msg.edit_text("🎤 Похоже, записалось неразборчиво. Давай ещё раз? Можно ближе к микрофону.")
                return
            
            # Обрабатываем как текст
            reply = await support_ai.answer(message.from_user.id, text, lang)
            await processing_msg.edit_text(reply, reply_markup=kb_ai_controls())
            
        except ValueError as e:
            if "too long" in str(e):
                await processing_msg.edit_text("⏰ Сообщение длинновато. Запиши, пожалуйста, короче — до 60 секунд 🙏")
            elif "too large" in str(e):
                await processing_msg.edit_text("📁 Файл слишком большой. Запиши, пожалуйста, короче — до 2 МБ 🙏")
            else:
                await processing_msg.edit_text("🎤 Похоже, записалось неразборчиво. Давай ещё раз? Можно ближе к микрофону.")
        
    except Exception as e:
        logger.error(f"Error processing voice: {e}")
        await message.answer("🎤 Похоже, записалось неразборчиво. Давай ещё раз? Можно ближе к микрофону.")


@router.message(SupportStates.chatting, F.audio)
async def support_ai_audio(message: Message, state: FSMContext):
    """Обработка аудиофайлов в AI-режиме"""
    # Обрабатываем как голосовое сообщение
    await support_ai_voice(message, state)
