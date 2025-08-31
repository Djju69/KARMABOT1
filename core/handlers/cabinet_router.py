"""
Router for user personal cabinet functionality.
Handles all user interactions with their personal account.
"""
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from typing import Optional, Union
import logging

from ..services.user_cabinet_service import user_cabinet_service
from ..keyboards.reply_v2 import (
    get_user_cabinet_keyboard,
    get_partner_cabinet_keyboard,
    get_return_to_main_menu
)
from ..utils.locales_v2 import get_text, get_all_texts

logger = logging.getLogger(__name__)
router = Router()


class CabinetStates(StatesGroup):
    """FSM states for user cabinet interactions."""
    viewing_profile = State()
    viewing_balance = State()
    viewing_history = State()
    spending_points = State()
    viewing_settings = State()


@router.message(F.text.in_(["👤 Профиль", "👤 Profile"]))
async def user_cabinet_handler(message: Message, state: FSMContext):
    """Handle user cabinet entry point."""
    try:
        # Get user data
        user_id = message.from_user.id
        profile = await user_cabinet_service.get_user_profile(user_id)
        
        if not profile:
            await message.answer(
                "❌ Произошла ошибка при загрузке профиля. Пожалуйста, попробуйте позже.",
                reply_markup=get_return_to_main_menu()
            )
            return
        
        # Format profile message
        text = (
            f"👤 <b>Ваш профиль</b>\n\n"
            f"🏷 ID: <code>{profile['telegram_id']}</code>\n"
            f"👤 Имя: {profile['full_name'] or 'Не указано'}\n"
            f"💬 Логин: @{profile['username'] or 'Не указан'}\n"
            f"🎁 Баланс: <b>{profile['balance']} баллов</b>\n"
            f"⭐ Уровень: {profile['level']}\n"
            f"📅 Дата регистрации: {profile['registration_date']}"
        )
        
        # Add partner info if user is a partner
        if profile.get('is_partner'):
            text += "\n\n🔹 <b>Партнёрский статус: Активирован</b>"
        
        # Add referral info if available
        if profile.get('referral_code'):
            text += f"\n🔗 Реферальный код: <code>{profile['referral_code']}</code>"
        
        # Send message with appropriate keyboard
        keyboard = (
            get_partner_cabinet_keyboard(has_cards=profile.get('is_partner', False))
            if profile.get('is_partner') 
            else get_user_cabinet_keyboard()
        )
        
        await message.answer(
            text,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
        # Set state to viewing profile
        await state.set_state(CabinetStates.viewing_profile)
        
    except Exception as e:
        logger.error(f"Error in user_cabinet_handler: {str(e)}", exc_info=True)
        await message.answer(
            "❌ Произошла ошибка при загрузке профиля. Пожалуйста, попробуйте позже.",
            reply_markup=get_return_to_main_menu()
        )


@router.message(F.text.in_(["🎁 Баллы", "🎁 Points"]))
async def view_balance_handler(message: Message, state: FSMContext):
    """Handle balance viewing."""
    try:
        user_id = message.from_user.id
        balance = await user_cabinet_service.get_user_balance(user_id)
        level = await user_cabinet_service.get_user_level(user_id)
        
        text = (
            f"💎 <b>Ваши баллы</b>\n\n"
            f"💰 Доступно: <b>{balance} баллов</b>\n"
            f"⭐ Ваш уровень: <b>{level}</b>\n\n"
            f"💡 Копите баллы и получайте больше привилегий!"
        )
        
        await message.answer(
            text,
            reply_markup=get_user_cabinet_keyboard(),
            parse_mode='HTML'
        )
        
        await state.set_state(CabinetStates.viewing_balance)
        
    except Exception as e:
        logger.error(f"Error in view_balance_handler: {str(e)}", exc_info=True)
        await message.answer(
            "❌ Не удалось загрузить информацию о баллах. Пожалуйста, попробуйте позже.",
            reply_markup=get_user_cabinet_keyboard()
        )


@router.message(F.text.in_(["📜 История", "📜 History"]))
async def view_history_handler(message: Message, state: FSMContext):
    """Handle transaction history viewing."""
    try:
        user_id = message.from_user.id
        history = await user_cabinet_service.get_transaction_history(user_id, limit=5)
        
        if not history.get('transactions'):
            text = "📜 У вас пока нет истории операций."
        else:
            text = "📜 <b>Последние операции</b>\n\n"
            for txn in history['transactions']:
                amount = f"+{txn['amount']}" if txn['amount'] > 0 else str(txn['amount'])
                text += (
                    f"• {txn['description']}: <b>{amount} баллов</b>\n"
                    f"  <i>{txn['created_at']} • {txn['status']}</i>\n\n"
                )
            
            if history['total'] > 5:
                text += f"\n📊 Всего операций: {history['total']}"
        
        await message.answer(
            text,
            reply_markup=get_user_cabinet_keyboard(),
            parse_mode='HTML'
        )
        
        await state.set_state(CabinetStates.viewing_history)
        
    except Exception as e:
        logger.error(f"Error in view_history_handler: {str(e)}", exc_info=True)
        await message.answer(
            "❌ Не удалось загрузить историю операций. Пожалуйста, попробуйте позже.",
            reply_markup=get_user_cabinet_keyboard()
        )


@router.message(F.text.in_(["◀️ Назад", "◀️ Back"]))
async def back_to_profile_handler(message: Message, state: FSMContext):
    """Handle back button to return to profile."""
    # This will be handled by the main menu router
    pass


def get_router():
    """Get the cabinet router with all handlers."""
    return router
