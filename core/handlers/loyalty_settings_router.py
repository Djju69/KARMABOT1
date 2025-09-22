"""
Роутер для FSM состояний редактирования настроек лояльности
"""
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
import logging

from core.fsm.loyalty_settings import (
    LoyaltySettingsStates,
    handle_setting_choice,
    handle_redeem_rate,
    handle_min_purchase,
    handle_max_discount,
    handle_max_percent_bill,
    handle_bonus_points_usage,
    handle_confirmation
)

logger = logging.getLogger(__name__)

router = Router()

# Регистрируем обработчики FSM состояний
@router.message(LoyaltySettingsStates.waiting_for_setting_choice)
async def fsm_setting_choice(message: Message, state: FSMContext):
    """Обработчик состояния ожидания выбора настройки"""
    await handle_setting_choice(message, state)

@router.message(LoyaltySettingsStates.waiting_for_redeem_rate)
async def fsm_redeem_rate(message: Message, state: FSMContext):
    """Обработчик состояния ожидания курса обмена"""
    await handle_redeem_rate(message, state)

@router.message(LoyaltySettingsStates.waiting_for_min_purchase)
async def fsm_min_purchase(message: Message, state: FSMContext):
    """Обработчик состояния ожидания минимальной покупки"""
    await handle_min_purchase(message, state)

@router.message(LoyaltySettingsStates.waiting_for_max_discount)
async def fsm_max_discount(message: Message, state: FSMContext):
    """Обработчик состояния ожидания максимальной скидки"""
    await handle_max_discount(message, state)

@router.message(LoyaltySettingsStates.waiting_for_max_percent_bill)
async def fsm_max_percent_bill(message: Message, state: FSMContext):
    """Обработчик состояния ожидания границы закрытия чека"""
    await handle_max_percent_bill(message, state)

@router.message(LoyaltySettingsStates.waiting_for_bonus_points_usage)
async def fsm_bonus_points_usage(message: Message, state: FSMContext):
    """Обработчик состояния ожидания дополнительной скидки при оплате баллами"""
    await handle_bonus_points_usage(message, state)

@router.message(LoyaltySettingsStates.waiting_for_confirmation)
async def fsm_confirmation(message: Message, state: FSMContext):
    """Обработчик состояния ожидания подтверждения"""
    await handle_confirmation(message, state)
