"""
Moderation FSM handlers for admin card approval/rejection
Behind FEATURE_MODERATION flag for safe deployment
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import Command
import logging

from ..settings import settings
from ..database.db_v2 import db_v2
from ..services.admins import admins_service

logger = logging.getLogger(__name__)

# FSM States for moderation
class ModerationStates(StatesGroup):
    reviewing_card = State()
    entering_rejection_reason = State()

# Router for moderation handlers
moderation_router = Router()

def get_moderation_keyboard(card_id: int) -> InlineKeyboardMarkup:
    """Keyboard for card moderation"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Одобрить", callback_data=f"mod_approve:{card_id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"mod_reject:{card_id}")
        ],
        [
            InlineKeyboardButton(text="⭐ Рекомендуемое", callback_data=f"mod_feature:{card_id}"),
            InlineKeyboardButton(text="🗂️ Архив", callback_data=f"mod_archive:{card_id}")
        ],
        [
            InlineKeyboardButton(text="⏭️ Следующая", callback_data="mod_next"),
            InlineKeyboardButton(text="🏁 Завершить", callback_data="mod_finish")
        ]
    ])

def get_rejection_keyboard(card_id: int) -> InlineKeyboardMarkup:
    """Keyboard for rejection reasons"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Неполная информация", callback_data=f"reject_reason:{card_id}:incomplete")],
        [InlineKeyboardButton(text="🚫 Неподходящий контент", callback_data=f"reject_reason:{card_id}:inappropriate")],
        [InlineKeyboardButton(text="📸 Плохое качество фото", callback_data=f"reject_reason:{card_id}:bad_photo")],
        [InlineKeyboardButton(text="🏷️ Неверная категория", callback_data=f"reject_reason:{card_id}:wrong_category")],
        [InlineKeyboardButton(text="✏️ Написать свою причину", callback_data=f"reject_custom:{card_id}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data=f"mod_back:{card_id}")]
    ])

def format_card_for_moderation(card: dict) -> str:
    """Format card for moderation review"""
    text = f"🔍 **МОДЕРАЦИЯ КАРТОЧКИ #{card['id']}**\n\n"
    text += f"👤 **Партнер:** {card.get('partner_name', 'Неизвестно')}\n"
    text += f"📂 **Категория:** {card.get('category_name', 'Неизвестно')}\n"
    text += f"📝 **Название:** {card['title']}\n"
    
    if card.get('description'):
        text += f"📄 **Описание:** {card['description']}\n"
    
    if card.get('contact'):
        text += f"📞 **Контакт:** {card['contact']}\n"
    
    if card.get('address'):
        text += f"📍 **Адрес:** {card['address']}\n"
    
    if card.get('discount_text'):
        text += f"🎫 **Скидка:** {card['discount_text']}\n"
    
    if card.get('photo_file_id'):
        text += f"📸 **Фото:** Прикреплено\n"
    
    text += f"\n📅 **Создана:** {card.get('created_at', 'Неизвестно')}"
    text += f"\n⏳ **Статус:** {card.get('status', 'pending')}"
    
    return text

async def _ensure_admin(user_id: int) -> bool:
    return await admins_service.is_admin(user_id)

# Command to start moderation
@moderation_router.message(Command("moderate"))
async def start_moderation(message: Message, state: FSMContext):
    """Start moderation process (admin only)"""
    if not settings.features.moderation:
        await message.answer("🚧 Функция модерации временно недоступна.")
        return
    
    if not await _ensure_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещен. Только для администраторов.")
        return
    
    # Get pending cards
    pending_cards = db_v2.get_cards_pending_moderation()
    
    if not pending_cards:
        await message.answer("✅ Нет карточек, ожидающих модерации.")
        return
    
    # Show first card
    card = pending_cards[0]
    await state.update_data(
        pending_cards=pending_cards,
        current_index=0,
        total_count=len(pending_cards)
    )
    await state.set_state(ModerationStates.reviewing_card)
    
    text = format_card_for_moderation(card)
    text += f"\n\n📊 **Карточка 1 из {len(pending_cards)}**"
    
    if card.get('photo_file_id'):
        await message.answer_photo(
            photo=card['photo_file_id'],
            caption=text,
            reply_markup=get_moderation_keyboard(card['id'])
        )
    else:
        await message.answer(
            text,
            reply_markup=get_moderation_keyboard(card['id'])
        )

# Approve card
@moderation_router.callback_query(F.data.startswith("mod_approve:"))
async def approve_card(callback: CallbackQuery, state: FSMContext):
    """Approve card"""
    if not await _ensure_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен")
        return
    
    card_id = int(callback.data.split(":")[1])
    
    # Update card status
    success = db_v2.update_card_status(
        card_id, 
        'published', 
        callback.from_user.id, 
        'Одобрено модератором'
    )
    
    if success:
        await callback.answer("✅ Карточка одобрена!")
        
        # Try to notify partner
        try:
            # Get card details for notification
            with db_v2.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT c.title, p.tg_user_id 
                    FROM cards_v2 c 
                    JOIN partners_v2 p ON c.partner_id = p.id 
                    WHERE c.id = ?
                """, (card_id,))
                row = cursor.fetchone()
                
                if row:
                    bot = callback.bot
                    await bot.send_message(
                        row['tg_user_id'],
                        f"✅ **Ваша карточка одобрена!**\n\n"
                        f"📝 Название: {row['title']}\n"
                        f"📋 ID: #{card_id}\n\n"
                        f"🎉 Карточка теперь видна пользователям в каталоге!"
                    )
        except Exception as e:
            logger.error(f"Failed to notify partner: {e}")
        
        await show_next_card(callback, state)
    else:
        await callback.answer("❌ Ошибка при одобрении карточки")

# Reject card - show reasons
@moderation_router.callback_query(F.data.startswith("mod_reject:"))
async def show_rejection_reasons(callback: CallbackQuery, state: FSMContext):
    """Show rejection reasons"""
    if not await _ensure_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен")
        return
    
    card_id = int(callback.data.split(":")[1])
    
    await callback.message.edit_reply_markup(
        reply_markup=get_rejection_keyboard(card_id)
    )

# Handle predefined rejection reasons
@moderation_router.callback_query(F.data.startswith("reject_reason:"))
async def reject_with_reason(callback: CallbackQuery, state: FSMContext):
    """Reject card with predefined reason"""
    if not await _ensure_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен")
        return
    
    parts = callback.data.split(":")
    card_id = int(parts[1])
    reason_code = parts[2]
    
    # Map reason codes to messages
    reasons = {
        'incomplete': 'Неполная информация. Пожалуйста, добавьте больше деталей.',
        'inappropriate': 'Неподходящий контент. Проверьте соответствие правилам платформы.',
        'bad_photo': 'Плохое качество фото. Загрузите более четкое изображение.',
        'wrong_category': 'Неверная категория. Выберите подходящую категорию.'
    }
    
    reason = reasons.get(reason_code, 'Карточка не соответствует требованиям.')
    
    await reject_card_with_comment(callback, state, card_id, reason)

# Handle custom rejection reason
@moderation_router.callback_query(F.data.startswith("reject_custom:"))
async def request_custom_reason(callback: CallbackQuery, state: FSMContext):
    """Request custom rejection reason"""
    if not await _ensure_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен")
        return
    
    card_id = int(callback.data.split(":")[1])
    
    await state.update_data(rejecting_card_id=card_id)
    await state.set_state(ModerationStates.entering_rejection_reason)
    
    await callback.message.edit_text(
        "✏️ **Введите причину отклонения:**\n\n"
        "Напишите понятное объяснение, что нужно исправить в карточке.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отменить", callback_data=f"mod_back:{card_id}")]
        ])
    )

# Handle custom rejection reason input
@moderation_router.message(ModerationStates.entering_rejection_reason, F.text)
async def handle_custom_rejection_reason(message: Message, state: FSMContext):
    """Handle custom rejection reason"""
    data = await state.get_data()
    card_id = data.get('rejecting_card_id')
    
    if not card_id:
        await message.answer("❌ Ошибка: карточка не найдена")
        return
    
    reason = message.text.strip()
    if len(reason) < 10:
        await message.answer("❌ Причина слишком короткая. Минимум 10 символов.")
        return
    
    # Create a fake callback for consistency
    class FakeCallback:
        def __init__(self, user_id, bot):
            self.from_user = type('User', (), {'id': user_id})()
            self.bot = bot
            self.answer = lambda text: message.answer(text)
    
    fake_callback = FakeCallback(message.from_user.id, message.bot)
    await reject_card_with_comment(fake_callback, state, card_id, reason)

async def reject_card_with_comment(callback, state: FSMContext, card_id: int, comment: str):
    """Reject card with comment"""
    # Update card status
    success = db_v2.update_card_status(
        card_id, 
        'rejected', 
        callback.from_user.id, 
        comment
    )
    
    if success:
        await callback.answer("❌ Карточка отклонена")
        
        # Try to notify partner
        try:
            with db_v2.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT c.title, p.tg_user_id 
                    FROM cards_v2 c 
                    JOIN partners_v2 p ON c.partner_id = p.id 
                    WHERE c.id = ?
                """, (card_id,))
                row = cursor.fetchone()
                
                if row:
                    bot = callback.bot
                    await bot.send_message(
                        row['tg_user_id'],
                        f"❌ **Ваша карточка отклонена**\n\n"
                        f"📝 Название: {row['title']}\n"
                        f"📋 ID: #{card_id}\n\n"
                        f"💬 **Причина:** {comment}\n\n"
                        f"✏️ Вы можете исправить карточку и отправить заново."
                    )
        except Exception as e:
            logger.error(f"Failed to notify partner: {e}")
        
        await show_next_card(callback, state)
    else:
        await callback.answer("❌ Ошибка при отклонении карточки")

# Feature card
@moderation_router.callback_query(F.data.startswith("mod_feature:"))
async def feature_card(callback: CallbackQuery, state: FSMContext):
    """Mark card as featured"""
    if not await _ensure_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен")
        return
    
    card_id = int(callback.data.split(":")[1])
    
    # Update card status and mark as featured
    with db_v2.get_connection() as conn:
        cursor = conn.execute("""
            UPDATE cards_v2 
            SET status = 'published', is_featured = 1, priority_level = 100,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (card_id,))
        
        if cursor.rowcount > 0:
            # Log moderation action
            conn.execute("""
                INSERT INTO moderation_log (card_id, moderator_id, action, comment)
                VALUES (?, ?, 'feature', 'Отмечено как рекомендуемое')
            """, (card_id, callback.from_user.id))
            
            await callback.answer("⭐ Карточка отмечена как рекомендуемая!")
            await show_next_card(callback, state)
        else:
            await callback.answer("❌ Ошибка при обновлении карточки")

# Show next card
@moderation_router.callback_query(F.data == "mod_next")
async def show_next_card_callback(callback: CallbackQuery, state: FSMContext):
    """Show next card for moderation"""
    await show_next_card(callback, state)

async def show_next_card(callback, state: FSMContext):
    """Show next card in moderation queue"""
    data = await state.get_data()
    pending_cards = data.get('pending_cards', [])
    current_index = data.get('current_index', 0)
    
    # Move to next card
    next_index = current_index + 1
    
    if next_index >= len(pending_cards):
        await callback.message.edit_text(
            "✅ **Модерация завершена!**\n\n"
            f"Обработано карточек: {len(pending_cards)}",
            reply_markup=None
        )
        await state.clear()
        return
    
    # Show next card
    card = pending_cards[next_index]
    await state.update_data(current_index=next_index)
    
    text = format_card_for_moderation(card)
    text += f"\n\n📊 **Карточка {next_index + 1} из {len(pending_cards)}**"
    
    if card.get('photo_file_id'):
        await callback.message.delete()
        await callback.message.answer_photo(
            photo=card['photo_file_id'],
            caption=text,
            reply_markup=get_moderation_keyboard(card['id'])
        )
    else:
        await callback.message.edit_text(
            text,
            reply_markup=get_moderation_keyboard(card['id'])
        )

# Back to card view
@moderation_router.callback_query(F.data.startswith("mod_back:"))
async def back_to_card(callback: CallbackQuery, state: FSMContext):
    """Go back to card moderation view"""
    card_id = int(callback.data.split(":")[1])
    
    await callback.message.edit_reply_markup(
        reply_markup=get_moderation_keyboard(card_id)
    )

# Finish moderation
@moderation_router.callback_query(F.data == "mod_finish")
async def finish_moderation(callback: CallbackQuery, state: FSMContext):
    """Finish moderation session"""
    data = await state.get_data()
    current_index = data.get('current_index', 0)
    total_count = data.get('total_count', 0)
    
    await callback.message.edit_text(
        f"🏁 **Модерация завершена**\n\n"
        f"Обработано: {current_index + 1} из {total_count} карточек\n"
        f"Оставшиеся карточки можно обработать позже командой /moderate",
        reply_markup=None
    )
    await state.clear()

# Statistics command
@moderation_router.message(Command("mod_stats"))
async def moderation_stats(message: Message):
    """Show moderation statistics"""
    if not await _ensure_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещен")
        return
    
    with db_v2.get_connection() as conn:
        # Get counts by status
        cursor = conn.execute("""
            SELECT status, COUNT(*) as count 
            FROM cards_v2 
            GROUP BY status
        """)
        status_counts = dict(cursor.fetchall())
        
        # Get recent moderation actions
        cursor = conn.execute("""
            SELECT action, COUNT(*) as count 
            FROM moderation_log 
            WHERE created_at >= date('now', '-7 days')
            GROUP BY action
        """)
        recent_actions = dict(cursor.fetchall())
    
    text = "📊 **Статистика модерации**\n\n"
    text += "**По статусам:**\n"
    text += f"⏳ Ожидают: {status_counts.get('pending', 0)}\n"
    text += f"✅ Опубликованы: {status_counts.get('published', 0)}\n"
    text += f"❌ Отклонены: {status_counts.get('rejected', 0)}\n"
    text += f"📝 Черновики: {status_counts.get('draft', 0)}\n"
    text += f"🗂️ Архив: {status_counts.get('archived', 0)}\n\n"
    
    if recent_actions:
        text += "**За последние 7 дней:**\n"
        for action, count in recent_actions.items():
            emoji = {'approve': '✅', 'reject': '❌', 'feature': '⭐', 'archive': '🗂️'}.get(action, '📝')
            text += f"{emoji} {action}: {count}\n"
    
    await message.answer(text)

# Register router only if feature is enabled
def get_moderation_router() -> Router:
    """Get moderation router if feature is enabled"""
    if settings.features.moderation:
        return moderation_router
    return Router()  # Empty router if disabled
