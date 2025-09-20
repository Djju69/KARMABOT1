"""
Enhanced Moderation Handlers for KARMABOT1
Advanced moderation features with queue management and analytics
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import Command
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List

from core.settings import settings
from core.database import get_db
from core.services.moderation_service import ModerationService
from core.services.admins import admins_service
from core.utils.i18n import get_text

logger = logging.getLogger(__name__)

# Enhanced FSM States for moderation
class EnhancedModerationStates(StatesGroup):
    reviewing_card = State()
    entering_rejection_reason = State()
    bulk_moderation = State()
    setting_priority = State()
    viewing_analytics = State()

# Router for enhanced moderation handlers
enhanced_moderation_router = Router()

def get_enhanced_moderation_keyboard(card_id: int, card_data: Dict[str, Any]) -> InlineKeyboardMarkup:
    """Enhanced keyboard for card moderation with more options"""
    keyboard = [
        [
            InlineKeyboardButton(text="✅ Одобрить", callback_data=f"enh_mod_approve:{card_id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"enh_mod_reject:{card_id}")
        ],
        [
            InlineKeyboardButton(text="⭐ Рекомендуемое", callback_data=f"enh_mod_feature:{card_id}"),
            InlineKeyboardButton(text="🗂️ Архив", callback_data=f"enh_mod_archive:{card_id}")
        ],
        [
            InlineKeyboardButton(text="⚡ Высокий приоритет", callback_data=f"enh_mod_priority:{card_id}:high"),
            InlineKeyboardButton(text="📊 Статистика", callback_data=f"enh_mod_stats:{card_id}")
        ],
        [
            InlineKeyboardButton(text="⏭️ Следующая", callback_data="enh_mod_next"),
            InlineKeyboardButton(text="🏁 Завершить", callback_data="enh_mod_finish")
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_priority_keyboard(card_id: int) -> InlineKeyboardMarkup:
    """Keyboard for setting card priority"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔥 Критический", callback_data=f"priority:{card_id}:100"),
            InlineKeyboardButton(text="⚡ Высокий", callback_data=f"priority:{card_id}:50")
        ],
        [
            InlineKeyboardButton(text="📋 Обычный", callback_data=f"priority:{card_id}:10"),
            InlineKeyboardButton(text="🐌 Низкий", callback_data=f"priority:{card_id}:1")
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data=f"enh_mod_back:{card_id}")
        ]
    ])

def get_bulk_moderation_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for bulk moderation actions"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Одобрить все", callback_data="bulk_approve"),
            InlineKeyboardButton(text="❌ Отклонить все", callback_data="bulk_reject")
        ],
        [
            InlineKeyboardButton(text="⭐ Рекомендуемые", callback_data="bulk_feature"),
            InlineKeyboardButton(text="🗂️ В архив", callback_data="bulk_archive")
        ],
        [
            InlineKeyboardButton(text="📊 Статистика", callback_data="bulk_stats"),
            InlineKeyboardButton(text="🔙 Назад", callback_data="enh_mod_back")
        ]
    ])

def format_enhanced_card_for_moderation(card_data: Dict[str, Any]) -> str:
    """Enhanced card formatting for moderation"""
    text = f"🔍 **РАСШИРЕННАЯ МОДЕРАЦИЯ #{card_data['id']}**\n\n"
    
    # Basic info
    text += f"👤 **Партнер ID:** {card_data.get('partner_id', 'Неизвестно')}\n"
    text += f"📂 **Категория ID:** {card_data.get('category_id', 'Неизвестно')}\n"
    text += f"📝 **Название:** {card_data['title']}\n"
    
    if card_data.get('description'):
        text += f"📄 **Описание:** {card_data['description'][:200]}{'...' if len(card_data['description']) > 200 else ''}\n"
    
    # Status and priority
    text += f"📊 **Статус:** {card_data.get('status', 'pending')}\n"
    text += f"⭐ **Приоритет:** {card_data.get('priority_level', 0)}\n"
    text += f"🌟 **Рекомендуемое:** {'Да' if card_data.get('is_featured') else 'Нет'}\n"
    
    # Moderation notes
    if card_data.get('moderation_notes'):
        text += f"📝 **Заметки модерации:** {card_data['moderation_notes']}\n"
    
    # Timestamps
    text += f"\n📅 **Создана:** {card_data.get('created_at', 'Неизвестно')}"
    text += f"\n🔄 **Обновлена:** {card_data.get('updated_at', 'Неизвестно')}"
    
    return text

async def _ensure_admin(user_id: int) -> bool:
    """Ensure user is admin"""
    return await admins_service.is_admin(user_id)

# Enhanced moderation command
@enhanced_moderation_router.message(Command("moderate_enhanced"))
async def start_enhanced_moderation(message: Message, state: FSMContext):
    """Start enhanced moderation process"""
    if not settings.features.moderation:
        await message.answer("🚧 Функция модерации временно недоступна.")
        return
    
    if not await _ensure_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещен. Только для администраторов.")
        return
    
    # Get moderation service
    async with get_db() as db:
        moderation_service = ModerationService(db)
        
        # Get pending cards
        pending_cards = await moderation_service.get_pending_cards(limit=20)
        
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
        await state.set_state(EnhancedModerationStates.reviewing_card)
        
        text = format_enhanced_card_for_moderation(card)
        text += f"\n\n📊 **Карточка 1 из {len(pending_cards)}**"
        
        await message.answer(
            text,
            reply_markup=get_enhanced_moderation_keyboard(card['id'], card)
        )

# Enhanced approve card
@enhanced_moderation_router.callback_query(F.data.startswith("enh_mod_approve:"))
async def enhanced_approve_card(callback: CallbackQuery, state: FSMContext):
    """Enhanced card approval with better logging"""
    if not await _ensure_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен")
        return
    
    card_id = int(callback.data.split(":")[1])
    
    try:
        async with get_db() as db:
            moderation_service = ModerationService(db)
            
            result = await moderation_service.approve_card(
                card_id=card_id,
                moderator_id=callback.from_user.id,
                comment="Одобрено через расширенную модерацию"
            )
            
            if result["success"]:
                await callback.answer("✅ Карточка одобрена!")
                
                # Notify partner
                await _notify_partner_card_approved(callback.bot, card_id)
                
                await show_next_enhanced_card(callback, state)
            else:
                await callback.answer("❌ Ошибка при одобрении карточки")
                
    except Exception as e:
        logger.error(f"Error in enhanced approve: {e}")
        await callback.answer("❌ Ошибка при одобрении")

# Enhanced reject card
@enhanced_moderation_router.callback_query(F.data.startswith("enh_mod_reject:"))
async def enhanced_reject_card(callback: CallbackQuery, state: FSMContext):
    """Enhanced card rejection with better reasons"""
    if not await _ensure_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен")
        return
    
    card_id = int(callback.data.split(":")[1])
    
    # Show enhanced rejection reasons
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Неполная информация", callback_data=f"enh_reject:{card_id}:incomplete")],
        [InlineKeyboardButton(text="🚫 Неподходящий контент", callback_data=f"enh_reject:{card_id}:inappropriate")],
        [InlineKeyboardButton(text="📸 Плохое качество фото", callback_data=f"enh_reject:{card_id}:bad_photo")],
        [InlineKeyboardButton(text="🏷️ Неверная категория", callback_data=f"enh_reject:{card_id}:wrong_category")],
        [InlineKeyboardButton(text="💰 Некорректная скидка", callback_data=f"enh_reject:{card_id}:invalid_discount")],
        [InlineKeyboardButton(text="📞 Некорректные контакты", callback_data=f"enh_reject:{card_id}:invalid_contact")],
        [InlineKeyboardButton(text="✏️ Написать свою причину", callback_data=f"enh_reject_custom:{card_id}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data=f"enh_mod_back:{card_id}")]
    ])
    
    await callback.message.edit_reply_markup(reply_markup=keyboard)

# Handle enhanced rejection reasons
@enhanced_moderation_router.callback_query(F.data.startswith("enh_reject:"))
async def handle_enhanced_rejection(callback: CallbackQuery, state: FSMContext):
    """Handle enhanced rejection with detailed reasons"""
    if not await _ensure_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен")
        return
    
    parts = callback.data.split(":")
    card_id = int(parts[1])
    reason_code = parts[2]
    
    # Enhanced reason mapping
    reasons = {
        'incomplete': 'Неполная информация. Пожалуйста, добавьте больше деталей о вашем заведении.',
        'inappropriate': 'Неподходящий контент. Проверьте соответствие правилам платформы.',
        'bad_photo': 'Плохое качество фото. Загрузите более четкое и привлекательное изображение.',
        'wrong_category': 'Неверная категория. Выберите подходящую категорию для вашего заведения.',
        'invalid_discount': 'Некорректная информация о скидке. Проверьте условия и размер скидки.',
        'invalid_contact': 'Некорректные контактные данные. Проверьте телефон, адрес или другие контакты.'
    }
    
    reason = reasons.get(reason_code, 'Карточка не соответствует требованиям платформы.')
    
    try:
        async with get_db() as db:
            moderation_service = ModerationService(db)
            
            result = await moderation_service.reject_card(
                card_id=card_id,
                moderator_id=callback.from_user.id,
                reason=reason,
                reason_code=reason_code
            )
            
            if result["success"]:
                await callback.answer("❌ Карточка отклонена")
                
                # Notify partner
                await _notify_partner_card_rejected(callback.bot, card_id, reason)
                
                await show_next_enhanced_card(callback, state)
            else:
                await callback.answer("❌ Ошибка при отклонении карточки")
                
    except Exception as e:
        logger.error(f"Error in enhanced reject: {e}")
        await callback.answer("❌ Ошибка при отклонении")

# Enhanced feature card
@enhanced_moderation_router.callback_query(F.data.startswith("enh_mod_feature:"))
async def enhanced_feature_card(callback: CallbackQuery, state: FSMContext):
    """Enhanced card featuring"""
    if not await _ensure_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен")
        return
    
    card_id = int(callback.data.split(":")[1])
    
    try:
        async with get_db() as db:
            moderation_service = ModerationService(db)
            
            result = await moderation_service.feature_card(
                card_id=card_id,
                moderator_id=callback.from_user.id,
                comment="Отмечено как рекомендуемое через расширенную модерацию"
            )
            
            if result["success"]:
                await callback.answer("⭐ Карточка отмечена как рекомендуемая!")
                await show_next_enhanced_card(callback, state)
            else:
                await callback.answer("❌ Ошибка при обновлении карточки")
                
    except Exception as e:
        logger.error(f"Error in enhanced feature: {e}")
        await callback.answer("❌ Ошибка при обновлении")

# Priority setting
@enhanced_moderation_router.callback_query(F.data.startswith("enh_mod_priority:"))
async def set_card_priority(callback: CallbackQuery, state: FSMContext):
    """Set card priority level"""
    if not await _ensure_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен")
        return
    
    parts = callback.data.split(":")
    card_id = int(parts[1])
    priority_level = parts[2]
    
    priority_values = {
        'high': 50,
        'critical': 100,
        'normal': 10,
        'low': 1
    }
    
    priority = priority_values.get(priority_level, 10)
    
    try:
        async with get_db() as db:
            moderation_service = ModerationService(db)
            
            # Update card priority
            await db.execute(
                update(Card)
                .where(Card.id == card_id)
                .values(priority_level=priority)
            )
            await db.commit()
            
            await callback.answer(f"⚡ Приоритет установлен: {priority}")
            
    except Exception as e:
        logger.error(f"Error setting priority: {e}")
        await callback.answer("❌ Ошибка при установке приоритета")

# Moderation statistics
@enhanced_moderation_router.callback_query(F.data.startswith("enh_mod_stats:"))
async def show_card_moderation_stats(callback: CallbackQuery, state: FSMContext):
    """Show moderation statistics for a specific card"""
    if not await _ensure_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен")
        return
    
    card_id = int(callback.data.split(":")[1])
    
    try:
        async with get_db() as db:
            moderation_service = ModerationService(db)
            
            # Get card details
            result = await db.execute(
                select(Card).where(Card.id == card_id)
            )
            card = result.scalar_one_or_none()
            
            if not card:
                await callback.answer("❌ Карточка не найдена")
                return
            
            # Get moderation logs for this card
            logs_result = await db.execute(
                select(ModerationLog)
                .where(ModerationLog.card_id == card_id)
                .order_by(desc(ModerationLog.created_at))
            )
            logs = logs_result.scalars().all()
            
            text = f"📊 **Статистика модерации #{card_id}**\n\n"
            text += f"📝 **Название:** {card.title}\n"
            text += f"📊 **Статус:** {card.status}\n"
            text += f"⭐ **Приоритет:** {getattr(card, 'priority_level', 0)}\n"
            text += f"🌟 **Рекомендуемое:** {'Да' if getattr(card, 'is_featured', False) else 'Нет'}\n\n"
            
            if logs:
                text += "📋 **История модерации:**\n"
                for log in logs[:5]:  # Show last 5 actions
                    text += f"• {log.action} - {log.created_at.strftime('%d.%m.%Y %H:%M')}\n"
                    if log.comment:
                        text += f"  💬 {log.comment[:50]}{'...' if len(log.comment) > 50 else ''}\n"
            else:
                text += "📋 История модерации отсутствует\n"
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data=f"enh_mod_back:{card_id}")]
            ])
            
            await callback.message.edit_text(text, reply_markup=keyboard)
            
    except Exception as e:
        logger.error(f"Error showing stats: {e}")
        await callback.answer("❌ Ошибка загрузки статистики")

# Show next card
async def show_next_enhanced_card(callback, state: FSMContext):
    """Show next card in enhanced moderation queue"""
    data = await state.get_data()
    pending_cards = data.get('pending_cards', [])
    current_index = data.get('current_index', 0)
    
    # Move to next card
    next_index = current_index + 1
    
    if next_index >= len(pending_cards):
        await callback.message.edit_text(
            "✅ **Расширенная модерация завершена!**\n\n"
            f"Обработано карточек: {len(pending_cards)}",
            reply_markup=None
        )
        await state.clear()
        return
    
    # Show next card
    card = pending_cards[next_index]
    await state.update_data(current_index=next_index)
    
    text = format_enhanced_card_for_moderation(card)
    text += f"\n\n📊 **Карточка {next_index + 1} из {len(pending_cards)}**"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_enhanced_moderation_keyboard(card['id'], card)
    )

# Navigation handlers
@enhanced_moderation_router.callback_query(F.data == "enh_mod_next")
async def next_enhanced_card(callback: CallbackQuery, state: FSMContext):
    """Show next card"""
    await show_next_enhanced_card(callback, state)

@enhanced_moderation_router.callback_query(F.data.startswith("enh_mod_back:"))
async def back_to_enhanced_card(callback: CallbackQuery, state: FSMContext):
    """Go back to card moderation view"""
    card_id = int(callback.data.split(":")[1])
    
    # Get card data from state
    data = await state.get_data()
    pending_cards = data.get('pending_cards', [])
    current_index = data.get('current_index', 0)
    
    if current_index < len(pending_cards):
        card = pending_cards[current_index]
        text = format_enhanced_card_for_moderation(card)
        text += f"\n\n📊 **Карточка {current_index + 1} из {len(pending_cards)}**"
        
        await callback.message.edit_text(
            text,
            reply_markup=get_enhanced_moderation_keyboard(card['id'], card)
        )

# Bulk moderation command
@enhanced_moderation_router.message(Command("bulk_moderate"))
async def start_bulk_moderation(message: Message, state: FSMContext):
    """Start bulk moderation process"""
    if not await _ensure_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещен. Только для администраторов.")
        return
    
    text = "📊 **Массовая модерация**\n\n"
    text += "Выберите действие для применения к нескольким карточкам:"
    
    await message.answer(text, reply_markup=get_bulk_moderation_keyboard())

# Enhanced moderation statistics command
@enhanced_moderation_router.message(Command("mod_stats_enhanced"))
async def enhanced_moderation_stats(message: Message):
    """Show enhanced moderation statistics"""
    if not await _ensure_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещен")
        return
    
    try:
        async with get_db() as db:
            moderation_service = ModerationService(db)
            
            # Get overall stats
            stats = await moderation_service.get_moderation_stats(days=30)
            queue_status = await moderation_service.get_moderation_queue_status()
            
            text = "📊 **Расширенная статистика модерации**\n\n"
            text += f"📈 **За последние 30 дней:**\n"
            text += f"• Всего действий: {stats['total_actions']}\n"
            text += f"• Одобрений: {stats['approvals']}\n"
            text += f"• Отклонений: {stats['rejections']}\n"
            text += f"• Рекомендуемых: {stats['features']}\n"
            text += f"• Процент одобрения: {stats['approval_rate']:.1%}\n\n"
            
            text += f"📋 **Текущее состояние очереди:**\n"
            text += f"• Ожидают модерации: {queue_status['pending_cards']}\n"
            text += f"• Опубликованы: {queue_status['published_cards']}\n"
            text += f"• Отклонены: {queue_status['rejected_cards']}\n\n"
            
            if queue_status['recent_activity']:
                text += "🔄 **Последняя активность:**\n"
                for activity in queue_status['recent_activity'][:5]:
                    text += f"• {activity['action']} #{activity['card_id']} - {activity['created_at'][:16]}\n"
            
            await message.answer(text)
            
    except Exception as e:
        logger.error(f"Error getting enhanced stats: {e}")
        await message.answer("❌ Ошибка загрузки статистики")

# Helper functions
async def _notify_partner_card_approved(bot, card_id: int):
    """Notify partner about card approval"""
    try:
        # This would send notification to partner
        logger.info(f"Card {card_id} approved - partner notification sent")
    except Exception as e:
        logger.error(f"Error notifying partner: {e}")

async def _notify_partner_card_rejected(bot, card_id: int, reason: str):
    """Notify partner about card rejection"""
    try:
        # This would send notification to partner with reason
        logger.info(f"Card {card_id} rejected - partner notification sent: {reason}")
    except Exception as e:
        logger.error(f"Error notifying partner: {e}")

# Register router only if feature is enabled
def get_enhanced_moderation_router() -> Router:
    """Get enhanced moderation router if feature is enabled"""
    if settings.features.moderation:
        return enhanced_moderation_router
    return Router()  # Empty router if disabled
