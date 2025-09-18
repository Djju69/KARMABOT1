"""
Роутер для FSM состояний регистрации партнеров
"""
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
import logging

from core.fsm.partner_registration import (
    PartnerRegistrationStates,
    handle_business_name,
    handle_contact_name,
    handle_contact_phone,
    handle_contact_email,
    handle_legal_info,
    handle_confirmation
)

logger = logging.getLogger(__name__)

router = Router()

# Регистрируем обработчики FSM состояний
@router.message(PartnerRegistrationStates.waiting_for_business_name)
async def fsm_business_name(message: Message, state: FSMContext):
    """Обработчик состояния ожидания названия бизнеса"""
    await handle_business_name(message, state)

@router.message(PartnerRegistrationStates.waiting_for_contact_name)
async def fsm_contact_name(message: Message, state: FSMContext):
    """Обработчик состояния ожидания имени контакта"""
    await handle_contact_name(message, state)

@router.message(PartnerRegistrationStates.waiting_for_contact_phone)
async def fsm_contact_phone(message: Message, state: FSMContext):
    """Обработчик состояния ожидания телефона"""
    await handle_contact_phone(message, state)

@router.message(PartnerRegistrationStates.waiting_for_contact_email)
async def fsm_contact_email(message: Message, state: FSMContext):
    """Обработчик состояния ожидания email"""
    await handle_contact_email(message, state)

@router.message(PartnerRegistrationStates.waiting_for_legal_info)
async def fsm_legal_info(message: Message, state: FSMContext):
    """Обработчик состояния ожидания юридической информации"""
    await handle_legal_info(message, state)

@router.message(PartnerRegistrationStates.waiting_for_confirmation)
async def fsm_confirmation(message: Message, state: FSMContext):
    """Обработчик состояния ожидания подтверждения"""
    await handle_confirmation(message, state)
