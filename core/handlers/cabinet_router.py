"""
Router for user personal cabinet functionality.
Handles all user interactions with their personal account.
"""
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from typing import Optional, Union, Any, Dict
import logging

# Create router with a name
router = Router(name='cabinet_router')

# Import dependencies
from ..services.user_cabinet_service import user_cabinet_service
from ..keyboards.reply_v2 import (
    get_user_cabinet_keyboard,
    get_partner_cabinet_keyboard,
    get_return_to_main_menu
)
from ..utils.locales_v2 import get_text, get_all_texts

logger = logging.getLogger(__name__)


def get_cabinet_router() -> Router:
    """Get the cabinet router with all handlers."""
    return router


class CabinetStates(StatesGroup):
    """FSM states for user cabinet interactions."""
    viewing_profile = State()
    viewing_balance = State()
    viewing_history = State()
    viewing_cards = State()
    viewing_notifications = State()
    viewing_achievements = State()
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
        
        # Format profile message according to TZ
        text = (
            f"👤 <b>Ваш профиль</b>\n\n"
            f"🏷 ID: <code>{profile['telegram_id']}</code>\n"
            f"👤 Имя: {profile['full_name'] or 'Не указано'}\n"
            f"💬 Логин: @{profile['username'] or 'Не указан'}\n"
            f"⭐ Карма: <b>{profile['karma_points']}</b> (Уровень {profile['level']})\n"
            f"🏆 Репутация: +{profile.get('reputation_score', 0)}\n"
            f"📅 Регистрация: {profile['registration_date']}\n"
            f"💳 Показать карту: {profile['cards_count']}"
        )
        
        # Add level progress if available
        if profile.get('level_progress'):
            progress = profile['level_progress']
            if progress.get('next_threshold'):
                text += f"\n📈 До следующего уровня: {progress['next_threshold'] - progress['progress_karma']} кармы"
        
        # Add notifications count
        if profile.get('unread_notifications', 0) > 0:
            text += f"\n🔔 Непрочитанных уведомлений: {profile['unread_notifications']}"
        
        # Add achievements count
        if profile.get('achievements_count', 0) > 0:
            text += f"\n🏅 Достижений: {profile['achievements_count']}"
        
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


@router.message(F.text.in_(["📊 Моя карма", "📊 My Karma"]))
async def view_karma_handler(message: Message, state: FSMContext):
    """Handle karma viewing according to TZ."""
    try:
        user_id = message.from_user.id
        profile = await user_cabinet_service.get_user_profile(user_id)
        
        if not profile:
            await message.answer(
                "❌ Произошла ошибка при загрузке кармы. Пожалуйста, попробуйте позже.",
                reply_markup=get_user_cabinet_keyboard()
            )
            return
        
        karma_points = profile.get('karma_points', 0)
        level = profile.get('level', 1)
        level_progress = profile.get('level_progress', {})
        
        text = (
            f"📊 <b>Система кармы</b>\n\n"
            f"⭐ Текущая карма: <b>{karma_points}</b>\n"
            f"🎯 Уровень: <b>{level} из 10</b>\n"
        )
        
        if level_progress.get('next_threshold'):
            text += f"📈 До следующего: {level_progress['next_threshold'] - karma_points} кармы\n\n"
            
            # Add progress bar
            progress_percent = level_progress.get('progress_percent', 0)
            filled_bars = int(progress_percent / 10)
            empty_bars = 10 - filled_bars
            progress_bar = "█" * filled_bars + "░" * empty_bars
            text += f"Прогресс: {progress_bar} {progress_percent:.0f}%"
        else:
            text += "\n🎉 Максимальный уровень достигнут!"
        
        await message.answer(
            text,
            reply_markup=get_user_cabinet_keyboard(),
            parse_mode='HTML'
        )
        
        await state.set_state(CabinetStates.viewing_balance)
        
    except Exception as e:
        logger.error(f"Error in view_karma_handler: {str(e)}", exc_info=True)
        await message.answer(
            "❌ Не удалось загрузить информацию о карме. Пожалуйста, попробуйте позже.",
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


@router.message(F.text.in_(["💳 Мои карты", "💳 My Cards"]))
async def view_cards_handler(message: Message, state: FSMContext):
    """Handle cards viewing according to TZ."""
    try:
        user_id = message.from_user.id
        cards = await user_cabinet_service.get_user_cards(user_id)
        
        if not cards:
            text = (
                "💳 <b>Мои карты</b>\n\n"
                "У вас пока нет привязанных карт.\n\n"
                "💡 Чтобы привязать карту, отсканируйте QR-код на пластиковой карте или введите код карты."
            )
        else:
            text = f"💳 <b>Мои карты</b>\n\n"
            for i, card in enumerate(cards, 1):
                status_emoji = "✅" if not card.get('is_blocked') else "🔒"
                text += f"{status_emoji} <b>{card['card_id_printable']}</b>\n"
                text += f"   Привязана: {card['bound_at'].strftime('%d.%m.%Y')}\n"
                if card.get('is_blocked'):
                    text += f"   🔒 Заблокирована\n"
                text += "\n"
        
        await message.answer(
            text,
            reply_markup=get_user_cabinet_keyboard(),
            parse_mode='HTML'
        )
        
        await state.set_state(CabinetStates.viewing_cards)
        
    except Exception as e:
        logger.error(f"Error in view_cards_handler: {str(e)}", exc_info=True)
        await message.answer(
            "❌ Не удалось загрузить информацию о картах. Пожалуйста, попробуйте позже.",
            reply_markup=get_user_cabinet_keyboard()
        )


@router.message(F.text.in_(["🔔 Уведомления", "🔔 Notifications"]))
async def view_notifications_handler(message: Message, state: FSMContext):
    """Handle notifications viewing according to TZ."""
    try:
        user_id = message.from_user.id
        notifications = await user_cabinet_service.get_user_notifications(user_id, limit=10)
        
        if not notifications:
            text = (
                "🔔 <b>Уведомления</b>\n\n"
                "У вас нет уведомлений."
            )
        else:
            text = f"🔔 <b>Уведомления</b>\n\n"
            for i, notif in enumerate(notifications, 1):
                read_status = "✅" if notif['is_read'] else "🔴"
                text += f"{read_status} {notif['message']}\n"
                text += f"   📅 {notif['created_at'].strftime('%d.%m.%Y %H:%M')}\n\n"
        
        await message.answer(
            text,
            reply_markup=get_user_cabinet_keyboard(),
            parse_mode='HTML'
        )
        
        await state.set_state(CabinetStates.viewing_notifications)
        
    except Exception as e:
        logger.error(f"Error in view_notifications_handler: {str(e)}", exc_info=True)
        await message.answer(
            "❌ Не удалось загрузить уведомления. Пожалуйста, попробуйте позже.",
            reply_markup=get_user_cabinet_keyboard()
        )


@router.message(F.text.in_(["🏆 Достижения", "🏆 Achievements"]))
async def view_achievements_handler(message: Message, state: FSMContext):
    """Handle achievements viewing according to TZ."""
    try:
        user_id = message.from_user.id
        achievements = await user_cabinet_service.get_user_achievements(user_id, limit=10)
        
        if not achievements:
            text = (
                "🏆 <b>Достижения</b>\n\n"
                "У вас пока нет достижений.\n\n"
                "💡 Выполняйте действия в боте, чтобы получить достижения!"
            )
        else:
            text = f"🏆 <b>Достижения</b>\n\n"
            for i, achievement in enumerate(achievements, 1):
                achievement_type = achievement['achievement_type']
                achievement_data = achievement['achievement_data']
                
                if achievement_type == 'level_up':
                    level = achievement_data.get('level', '?')
                    text += f"⭐ Достигнут {level} уровень\n"
                elif achievement_type == 'karma_milestone':
                    karma = achievement_data.get('karma', '?')
                    text += f"💎 {karma} кармы\n"
                elif achievement_type == 'first_card':
                    text += f"🎉 Первая карта\n"
                elif achievement_type == 'card_collector':
                    count = achievement_data.get('card_count', '?')
                    text += f"🏆 Коллекционер ({count} карт)\n"
                else:
                    text += f"🏅 {achievement_type}\n"
                
                text += f"   📅 {achievement['earned_at'].strftime('%d.%m.%Y')}\n\n"
        
        await message.answer(
            text,
            reply_markup=get_user_cabinet_keyboard(),
            parse_mode='HTML'
        )
        
        await state.set_state(CabinetStates.viewing_achievements)
        
    except Exception as e:
        logger.error(f"Error in view_achievements_handler: {str(e)}", exc_info=True)
        await message.answer(
            "❌ Не удалось загрузить достижения. Пожалуйста, попробуйте позже.",
            reply_markup=get_user_cabinet_keyboard()
        )


@router.message(F.text.in_(["◀️ Назад", "◀️ Back"]))
async def back_to_profile_handler(message: Message, state: FSMContext):
    """Handle back button to return to main menu."""
    try:
        # Импортируем get_start из basic.py
        from core.handlers.basic import get_start
        from aiogram import Bot
        bot = Bot.get_current()
        await get_start(message, bot, state)
    except Exception as e:
        logger.error(f"Error returning to main menu from cabinet: {e}", exc_info=True)
        await message.answer("Не удалось вернуться в главное меню. Попробуйте позже.")


# Register all handlers
router.message.register(user_cabinet_handler, F.text == "👤 Личный кабинет")
router.message.register(view_karma_handler, F.text == "📊 Моя карма")
router.message.register(view_history_handler, F.text == "📜 История")
router.message.register(view_cards_handler, F.text == "💳 Мои карты")
router.message.register(view_notifications_handler, F.text == "🔔 Уведомления")
router.message.register(view_achievements_handler, F.text == "🏆 Достижения")
router.message.register(back_to_profile_handler, F.text == "◀️ Назад")

# For backward compatibility
def get_cabinet_router():
    """Get the cabinet router instance."""
    return router

# Export the router
__all__ = ['router', 'get_cabinet_router']
