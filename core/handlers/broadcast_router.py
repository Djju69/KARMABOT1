"""
Роутер для FSM состояний системы рассылок
"""
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
import logging

from core.fsm.broadcast import (
    BroadcastStates,
    handle_message_text,
    handle_recipients_selection,
    handle_confirmation
)

logger = logging.getLogger(__name__)

router = Router()

# Регистрируем обработчики FSM состояний
@router.message(BroadcastStates.waiting_for_message)
async def fsm_message_text(message: Message, state: FSMContext):
    """Обработчик состояния ожидания текста сообщения"""
    await handle_message_text(message, state)

@router.message(BroadcastStates.waiting_for_recipients)
async def fsm_recipients_selection(message: Message, state: FSMContext):
    """Обработчик состояния ожидания выбора получателей"""
    await handle_recipients_selection(message, state)

@router.message(BroadcastStates.waiting_for_confirmation)
async def fsm_confirmation(message: Message, state: FSMContext):
    """Обработчик состояния ожидания подтверждения"""
    await handle_confirmation(message, state)
