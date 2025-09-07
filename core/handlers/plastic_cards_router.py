"""
Router for plastic cards and karma functionality.
Handles card binding, unbinding, management, and karma operations.
"""
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from typing import Optional, Union, Any, Dict
import logging
import re

# Create router with a name
router = Router(name='plastic_cards_router')

# Import dependencies
from ..services.plastic_cards_service import plastic_cards_service
from ..services.user_service import karma_service
from ..keyboards.reply_v2 import get_user_cabinet_keyboard, get_return_to_main_menu
from ..utils.locales_v2 import get_text

logger = logging.getLogger(__name__)


def get_plastic_cards_router() -> Router:
    """Get the plastic cards router with all handlers."""
    return router


class PlasticCardsStates(StatesGroup):
    """FSM states for plastic cards interactions."""
    waiting_for_card_id = State()
    viewing_cards = State()


class KarmaStates(StatesGroup):
    """FSM states for karma interactions."""
    waiting_for_karma_amount = State()
    waiting_for_karma_reason = State()


@router.message(F.text == "📊 Карма")
async def show_karma_handler(message: Message, state: FSMContext):
    """Show user's karma information."""
    try:
        user_id = message.from_user.id
        
        # Get karma information
        karma_points = await karma_service.get_user_karma(user_id)
        karma_level = await karma_service.get_user_level(user_id)
        reputation = await karma_service.get_user_reputation(user_id)
        
        text = (
            f"📊 <b>Ваша карма</b>\n\n"
            f"💎 <b>Очки кармы:</b> {karma_points}\n"
            f"🏅 <b>Уровень:</b> {karma_level}\n"
            f"⭐ <b>Репутация:</b> {reputation['reputation_score']}\n"
            f"   👍 Благодарности: {reputation['thanks']}\n"
            f"   👎 Жалобы: {reputation['complaints']}\n\n"
            f"Карма начисляется за хорошие поступки и списывается за нарушения."
        )
        
        await message.answer(
            text,
            reply_markup=get_user_cabinet_keyboard(),
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"Error in show_karma_handler: {str(e)}", exc_info=True)
        await message.answer(
            "❌ Произошла ошибка при загрузке информации о карме.",
            reply_markup=get_user_cabinet_keyboard()
        )


@router.message(F.text == "📜 История")
async def show_karma_history_handler(message: Message, state: FSMContext):
    """Show user's karma history."""
    try:
        user_id = message.from_user.id
        history = await karma_service.get_karma_history(user_id, limit=10)
        
        if not history:
            await message.answer(
                "📜 <b>История кармы</b>\n\n"
                "У вас пока нет записей в истории кармы.",
                reply_markup=get_user_cabinet_keyboard(),
                parse_mode='HTML'
            )
            return
        
        text = "📜 <b>История кармы</b>\n\n"
        for i, transaction in enumerate(history, 1):
            amount = transaction['amount']
            reason = transaction['reason'] or "Не указано"
            date = transaction['created_at'][:10]  # Show only date
            
            if amount > 0:
                text += f"{i}. ➕ +{amount} кармы\n"
            else:
                text += f"{i}. ➖ {amount} кармы\n"
            
            text += f"   📝 Причина: {reason}\n"
            text += f"   📅 Дата: {date}\n\n"
        
        await message.answer(
            text,
            reply_markup=get_user_cabinet_keyboard(),
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"Error in show_karma_history_handler: {str(e)}", exc_info=True)
        await message.answer(
            "❌ Произошла ошибка при загрузке истории кармы.",
            reply_markup=get_user_cabinet_keyboard()
        )


@router.message(F.text == "🏅 Достижения")
async def show_achievements_handler(message: Message, state: FSMContext):
    """Show user's achievements based on karma."""
    try:
        user_id = message.from_user.id
        karma_points = await karma_service.get_user_karma(user_id)
        karma_level = await karma_service.get_user_level(user_id)
        
        # Calculate achievements
        achievements = []
        
        if karma_points >= 100:
            achievements.append("🥉 Первые 100 очков кармы")
        if karma_points >= 500:
            achievements.append("🥈 500 очков кармы")
        if karma_points >= 1000:
            achievements.append("🥇 1000 очков кармы")
        if karma_points >= 5000:
            achievements.append("💎 5000 очков кармы")
        if karma_points >= 10000:
            achievements.append("👑 10000 очков кармы")
        
        if karma_level == "Bronze":
            achievements.append("🥉 Бронзовый уровень")
        elif karma_level == "Silver":
            achievements.append("🥈 Серебряный уровень")
        elif karma_level == "Gold":
            achievements.append("🥇 Золотой уровень")
        elif karma_level == "Platinum":
            achievements.append("💎 Платиновый уровень")
        
        text = f"🏅 <b>Достижения</b>\n\n"
        text += f"💎 <b>Текущий уровень:</b> {karma_level}\n"
        text += f"📊 <b>Очки кармы:</b> {karma_points}\n\n"
        
        if achievements:
            text += "<b>Полученные достижения:</b>\n"
            for achievement in achievements:
                text += f"✅ {achievement}\n"
        else:
            text += "Пока нет достижений. Продолжайте зарабатывать карму!"
        
        await message.answer(
            text,
            reply_markup=get_user_cabinet_keyboard(),
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"Error in show_achievements_handler: {str(e)}", exc_info=True)
        await message.answer(
            "❌ Произошла ошибка при загрузке достижений.",
            reply_markup=get_user_cabinet_keyboard()
        )


@router.message(F.text == "🔗 Привязать карту")
async def bind_card_handler(message: Message, state: FSMContext):
    """Handle card binding request."""
    try:
        user_id = message.from_user.id
        
        # Check if user already has cards
        cards = await plastic_cards_service.get_user_cards(user_id)
        
        if len(cards) >= 5:  # Limit to 5 cards per user
            await message.answer(
                "❌ Вы можете привязать максимум 5 карт к одному аккаунту.\n\n"
                "Для привязки новой карты сначала отвяжите одну из существующих.",
                reply_markup=get_user_cabinet_keyboard()
            )
            return
        
        await message.answer(
            "🔗 <b>Привязка пластиковой карты</b>\n\n"
            "Для привязки карты используйте QR-код на карте или введите ID карты вручную.\n\n"
            "📱 <b>Способ 1:</b> Отсканируйте QR-код на карте\n"
            "⌨️ <b>Способ 2:</b> Введите ID карты (например: KS12340001)\n\n"
            "Введите ID карты:",
            reply_markup=get_return_to_main_menu(),
            parse_mode='HTML'
        )
        
        await state.set_state(PlasticCardsStates.waiting_for_card_id)
        
    except Exception as e:
        logger.error(f"Error in bind_card_handler: {str(e)}", exc_info=True)
        await message.answer(
            "❌ Произошла ошибка. Попробуйте позже.",
            reply_markup=get_user_cabinet_keyboard()
        )


@router.message(PlasticCardsStates.waiting_for_card_id)
async def process_card_id_handler(message: Message, state: FSMContext):
    """Process card ID input."""
    try:
        user_id = message.from_user.id
        card_id = message.text.strip()
        
        # Validate card ID format
        if not await plastic_cards_service.validate_card_id(card_id):
            await message.answer(
                "❌ Неверный формат ID карты.\n\n"
                "ID карты должен содержать только буквы, цифры, дефисы и подчеркивания.\n"
                "Длина: от 3 до 20 символов.\n\n"
                "Попробуйте еще раз:",
                reply_markup=get_return_to_main_menu()
            )
            return
        
        # Try to bind the card
        result = await plastic_cards_service.bind_card_to_user(
            telegram_id=user_id,
            card_id=card_id,
            card_id_printable=card_id
        )
        
        if result['success']:
            await message.answer(
                f"✅ {result['message']}\n\n"
                "Теперь вы можете использовать эту карту для получения скидок!",
                reply_markup=get_user_cabinet_keyboard(),
                parse_mode='HTML'
            )
        else:
            await message.answer(
                f"❌ {result['message']}\n\n"
                "Попробуйте другую карту или обратитесь в поддержку.",
                reply_markup=get_user_cabinet_keyboard(),
                parse_mode='HTML'
            )
        
        await state.clear()
        
    except Exception as e:
        logger.error(f"Error in process_card_id_handler: {str(e)}", exc_info=True)
        await message.answer(
            "❌ Произошла ошибка при обработке карты. Попробуйте позже.",
            reply_markup=get_user_cabinet_keyboard()
        )
        await state.clear()


@router.message(F.text == "📋 Мои карты")
async def view_cards_handler(message: Message, state: FSMContext):
    """Handle viewing user's bound cards."""
    try:
        user_id = message.from_user.id
        cards = await plastic_cards_service.get_user_cards(user_id)
        
        if not cards:
            await message.answer(
                "📋 <b>Мои карты</b>\n\n"
                "У вас пока нет привязанных карт.\n\n"
                "Нажмите «🔗 Привязать карту» чтобы добавить первую карту.",
                reply_markup=get_user_cabinet_keyboard(),
                parse_mode='HTML'
            )
            return
        
        text = "📋 <b>Мои карты</b>\n\n"
        for i, card in enumerate(cards, 1):
            text += f"{i}. <b>{card['card_id_printable'] or card['card_id']}</b>\n"
            text += f"   ID: <code>{card['card_id']}</code>\n"
            text += f"   Привязана: {card['bound_at'][:10]}\n\n"
        
        text += f"Всего карт: {len(cards)}/5"
        
        await message.answer(
            text,
            reply_markup=get_user_cabinet_keyboard(),
            parse_mode='HTML'
        )
        
        await state.set_state(PlasticCardsStates.viewing_cards)
        
    except Exception as e:
        logger.error(f"Error in view_cards_handler: {str(e)}", exc_info=True)
        await message.answer(
            "❌ Не удалось загрузить список карт. Попробуйте позже.",
            reply_markup=get_user_cabinet_keyboard()
        )


@router.message(F.text.regexp(r'^Отвязать карту \d+$'))
async def unbind_card_handler(message: Message, state: FSMContext):
    """Handle card unbinding."""
    try:
        user_id = message.from_user.id
        
        # Extract card number from message
        match = re.search(r'Отвязать карту (\d+)', message.text)
        if not match:
            await message.answer("❌ Неверный формат команды.")
            return
        
        card_number = int(match.group(1))
        cards = await plastic_cards_service.get_user_cards(user_id)
        
        if card_number < 1 or card_number > len(cards):
            await message.answer("❌ Неверный номер карты.")
            return
        
        card = cards[card_number - 1]
        result = await plastic_cards_service.unbind_card(user_id, card['card_id'])
        
        if result['success']:
            await message.answer(
                f"✅ {result['message']}",
                reply_markup=get_user_cabinet_keyboard()
            )
        else:
            await message.answer(
                f"❌ {result['message']}",
                reply_markup=get_user_cabinet_keyboard()
            )
        
    except Exception as e:
        logger.error(f"Error in unbind_card_handler: {str(e)}", exc_info=True)
        await message.answer(
            "❌ Произошла ошибка при отвязке карты. Попробуйте позже.",
            reply_markup=get_user_cabinet_keyboard()
        )


# Register all handlers
router.message.register(show_karma_handler, F.text == "📊 Карма")
router.message.register(show_karma_history_handler, F.text == "📜 История")
router.message.register(show_achievements_handler, F.text == "🏅 Достижения")
router.message.register(bind_card_handler, F.text == "🔗 Привязать карту")
router.message.register(view_cards_handler, F.text == "📋 Мои карты")
router.message.register(unbind_card_handler, F.text.regexp(r'^Отвязать карту \d+$'))

# Export the router
__all__ = ['router', 'get_plastic_cards_router']
