"""
Router for admin panel functionality.
Handles all administrative operations including user management, karma control, and system monitoring.
"""
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from typing import Optional, Union, Any, Dict
import logging

# Create router with a name
router = Router(name='admin_router')

# Import dependencies
from ..services.admin_service import admin_service
from ..services.user_service import karma_service
from ..keyboards.reply_v2 import get_admin_keyboard, get_return_to_main_menu
from ..utils.locales_v2 import get_text, get_all_texts

logger = logging.getLogger(__name__)


def get_admin_router() -> Router:
    """Get the admin router with all handlers."""
    return router


class AdminStates(StatesGroup):
    """FSM states for admin panel interactions."""
    viewing_dashboard = State()
    searching_users = State()
    viewing_user_details = State()
    modifying_karma = State()
    banning_user = State()
    viewing_logs = State()


@router.message(F.text.in_(["🛡️ Админ панель", "🛡️ Admin Panel"]))
async def admin_dashboard_handler(message: Message, state: FSMContext):
    """Handle admin dashboard entry point."""
    try:
        # Check if user is admin
        user_id = message.from_user.id
        # TODO: Add role check here
        
        # Get admin statistics
        stats = await admin_service.get_admin_stats()
        
        text = (
            f"🛡️ <b>Панель администратора</b>\n\n"
            f"📊 <b>Статистика системы:</b>\n"
            f"👥 Всего пользователей: <b>{stats['total_users']}</b>\n"
            f"✅ Активных: <b>{stats['active_users']}</b>\n"
            f"🚫 Заблокированных: <b>{stats['banned_users']}</b>\n"
            f"📈 За неделю: <b>{stats['recent_registrations']}</b>\n\n"
            f"⭐ <b>Карма и карты:</b>\n"
            f"💎 Общая карма: <b>{stats['total_karma']:,}</b>\n"
            f"💳 Всего карт: <b>{stats['total_cards']}</b>\n"
            f"🔗 Привязанных: <b>{stats['bound_cards']}</b>\n"
            f"📋 Свободных: <b>{stats['unbound_cards']}</b>\n\n"
            f"👥 <b>По ролям:</b>\n"
        )
        
        for role, count in stats['users_by_role'].items():
            role_emoji = {
                'user': '👤',
                'partner': '🤝',
                'admin': '🛡️',
                'superadmin': '👑'
            }.get(role, '❓')
            text += f"{role_emoji} {role}: <b>{count}</b>\n"
        
        await message.answer(
            text,
            reply_markup=get_admin_keyboard(),
            parse_mode='HTML'
        )
        
        await state.set_state(AdminStates.viewing_dashboard)
        
    except Exception as e:
        logger.error(f"Error in admin_dashboard_handler: {str(e)}", exc_info=True)
        await message.answer(
            "❌ Произошла ошибка при загрузке админ панели. Пожалуйста, попробуйте позже.",
            reply_markup=get_return_to_main_menu()
        )


@router.message(F.text.in_(["🔍 Поиск пользователей", "🔍 Search Users"]))
async def search_users_handler(message: Message, state: FSMContext):
    """Handle user search."""
    try:
        text = (
            "🔍 <b>Поиск пользователей</b>\n\n"
            "Введите для поиска:\n"
            "• Telegram ID (например: 123456789)\n"
            "• Имя пользователя (например: @username)\n"
            "• Имя или фамилию\n\n"
            "Примеры:\n"
            "• <code>123456789</code>\n"
            "• <code>@username</code>\n"
            "• <code>Иван</code>"
        )
        
        await message.answer(
            text,
            reply_markup=get_admin_keyboard(),
            parse_mode='HTML'
        )
        
        await state.set_state(AdminStates.searching_users)
        
    except Exception as e:
        logger.error(f"Error in search_users_handler: {str(e)}", exc_info=True)
        await message.answer(
            "❌ Произошла ошибка. Пожалуйста, попробуйте позже.",
            reply_markup=get_admin_keyboard()
        )


@router.message(AdminStates.searching_users)
async def process_user_search(message: Message, state: FSMContext):
    """Process user search query."""
    try:
        query = message.text.strip()
        if not query:
            await message.answer("❌ Пожалуйста, введите поисковый запрос.")
            return
        
        # Search users
        users = await admin_service.search_users(query, limit=10)
        
        if not users:
            text = f"❌ Пользователи по запросу '{query}' не найдены."
        else:
            text = f"🔍 <b>Результаты поиска:</b> '{query}'\n\n"
            for i, user in enumerate(users, 1):
                status_emoji = "🚫" if user['is_banned'] else "✅"
                text += (
                    f"{i}. {status_emoji} <b>{user['full_name'] or 'Без имени'}</b>\n"
                    f"   ID: <code>{user['telegram_id']}</code>\n"
                    f"   @{user['username'] or 'Нет username'}\n"
                    f"   ⭐ Карма: {user['karma_points']} (Уровень {user['level']})\n"
                    f"   🎭 Роль: {user['role']}\n\n"
                )
        
        await message.answer(
            text,
            reply_markup=get_admin_keyboard(),
            parse_mode='HTML'
        )
        
        await state.set_state(AdminStates.viewing_dashboard)
        
    except Exception as e:
        logger.error(f"Error in process_user_search: {str(e)}", exc_info=True)
        await message.answer(
            "❌ Ошибка при поиске пользователей. Пожалуйста, попробуйте позже.",
            reply_markup=get_admin_keyboard()
        )


@router.message(F.text.in_(["⚡ Управление кармой", "⚡ Karma Management"]))
async def karma_management_handler(message: Message, state: FSMContext):
    """Handle karma management."""
    try:
        text = (
            "⚡ <b>Управление кармой</b>\n\n"
            "Введите команду в формате:\n"
            "<code>/karma [ID] [±сумма] [причина]</code>\n\n"
            "Примеры:\n"
            "• <code>/karma 123456789 +100 Бонус за активность</code>\n"
            "• <code>/karma 123456789 -50 Нарушение правил</code>\n\n"
            "⚠️ Максимальное изменение за раз: 1000 кармы"
        )
        
        await message.answer(
            text,
            reply_markup=get_admin_keyboard(),
            parse_mode='HTML'
        )
        
        await state.set_state(AdminStates.modifying_karma)
        
    except Exception as e:
        logger.error(f"Error in karma_management_handler: {str(e)}", exc_info=True)
        await message.answer(
            "❌ Произошла ошибка. Пожалуйста, попробуйте позже.",
            reply_markup=get_admin_keyboard()
        )


@router.message(AdminStates.modifying_karma)
async def process_karma_modification(message: Message, state: FSMContext):
    """Process karma modification command."""
    try:
        command = message.text.strip()
        if not command.startswith('/karma'):
            await message.answer("❌ Неверный формат команды. Используйте /karma [ID] [±сумма] [причина]")
            return
        
        # Parse command
        parts = command.split()
        if len(parts) < 4:
            await message.answer("❌ Неверный формат команды. Используйте /karma [ID] [±сумма] [причина]")
            return
        
        try:
            user_id = int(parts[1])
            amount = int(parts[2])
            reason = ' '.join(parts[3:])
        except ValueError:
            await message.answer("❌ Неверный формат ID или суммы.")
            return
        
        # Modify karma
        result = await admin_service.modify_user_karma(
            user_id, amount, reason, message.from_user.id
        )
        
        if result['success']:
            text = (
                f"✅ <b>Карма изменена</b>\n\n"
                f"👤 Пользователь: <code>{user_id}</code>\n"
                f"📊 Изменение: {amount:+d}\n"
                f"⭐ Было: {result['old_karma']}\n"
                f"⭐ Стало: {result['new_karma']}\n"
                f"📝 Причина: {reason}"
            )
        else:
            text = f"❌ {result['message']}"
        
        await message.answer(
            text,
            reply_markup=get_admin_keyboard(),
            parse_mode='HTML'
        )
        
        await state.set_state(AdminStates.viewing_dashboard)
        
    except Exception as e:
        logger.error(f"Error in process_karma_modification: {str(e)}", exc_info=True)
        await message.answer(
            "❌ Ошибка при изменении кармы. Пожалуйста, попробуйте позже.",
            reply_markup=get_admin_keyboard()
        )


@router.message(F.text.in_(["🚫 Бан/разбан", "🚫 Ban/Unban"]))
async def ban_management_handler(message: Message, state: FSMContext):
    """Handle ban/unban management."""
    try:
        text = (
            "🚫 <b>Управление блокировками</b>\n\n"
            "Введите команду в формате:\n"
            "<code>/ban [ID] [причина]</code> - заблокировать\n"
            "<code>/unban [ID]</code> - разблокировать\n\n"
            "Примеры:\n"
            "• <code>/ban 123456789 Спам</code>\n"
            "• <code>/unban 123456789</code>"
        )
        
        await message.answer(
            text,
            reply_markup=get_admin_keyboard(),
            parse_mode='HTML'
        )
        
        await state.set_state(AdminStates.banning_user)
        
    except Exception as e:
        logger.error(f"Error in ban_management_handler: {str(e)}", exc_info=True)
        await message.answer(
            "❌ Произошла ошибка. Пожалуйста, попробуйте позже.",
            reply_markup=get_admin_keyboard()
        )


@router.message(AdminStates.banning_user)
async def process_ban_command(message: Message, state: FSMContext):
    """Process ban/unban command."""
    try:
        command = message.text.strip()
        
        if command.startswith('/ban'):
            # Parse ban command
            parts = command.split()
            if len(parts) < 3:
                await message.answer("❌ Неверный формат команды. Используйте /ban [ID] [причина]")
                return
            
            try:
                user_id = int(parts[1])
                reason = ' '.join(parts[2:])
            except ValueError:
                await message.answer("❌ Неверный формат ID.")
                return
            
            # Ban user
            result = await admin_service.ban_user(user_id, reason, message.from_user.id)
            
        elif command.startswith('/unban'):
            # Parse unban command
            parts = command.split()
            if len(parts) < 2:
                await message.answer("❌ Неверный формат команды. Используйте /unban [ID]")
                return
            
            try:
                user_id = int(parts[1])
            except ValueError:
                await message.answer("❌ Неверный формат ID.")
                return
            
            # Unban user
            result = await admin_service.unban_user(user_id, message.from_user.id)
            
        else:
            await message.answer("❌ Неверная команда. Используйте /ban или /unban")
            return
        
        if result['success']:
            text = f"✅ {result['message']}"
            if 'reason' in result:
                text += f"\n📝 Причина: {result['reason']}"
        else:
            text = f"❌ {result['message']}"
        
        await message.answer(
            text,
            reply_markup=get_admin_keyboard(),
            parse_mode='HTML'
        )
        
        await state.set_state(AdminStates.viewing_dashboard)
        
    except Exception as e:
        logger.error(f"Error in process_ban_command: {str(e)}", exc_info=True)
        await message.answer(
            "❌ Ошибка при выполнении команды. Пожалуйста, попробуйте позже.",
            reply_markup=get_admin_keyboard()
        )


@router.message(F.text.in_(["📋 Логи действий", "📋 Action Logs"]))
async def view_logs_handler(message: Message, state: FSMContext):
    """Handle admin logs viewing."""
    try:
        # Get recent admin logs
        logs = await admin_service.get_admin_logs(limit=10)
        
        if not logs:
            text = "📋 <b>Логи действий</b>\n\nНет записей в логах."
        else:
            text = "📋 <b>Последние действия администраторов</b>\n\n"
            for log in logs:
                action_emoji = {
                    'modify_karma': '⚡',
                    'ban_user': '🚫',
                    'unban_user': '✅',
                    'generate_cards': '💳',
                    'block_card': '🔒'
                }.get(log['action'], '🔧')
                
                text += (
                    f"{action_emoji} <b>{log['action']}</b>\n"
                    f"👤 Админ: <code>{log['admin_id']}</code>\n"
                )
                
                if log['target_user_id']:
                    text += f"🎯 Пользователь: <code>{log['target_user_id']}</code>\n"
                    if log['target_full_name']:
                        text += f"   {log['target_full_name']}\n"
                
                if log['target_card_id']:
                    text += f"💳 Карта: <code>{log['target_card_id']}</code>\n"
                
                if log['details']:
                    text += f"📝 {log['details']}\n"
                
                text += f"📅 {log['created_at'].strftime('%d.%m.%Y %H:%M')}\n\n"
        
        await message.answer(
            text,
            reply_markup=get_admin_keyboard(),
            parse_mode='HTML'
        )
        
        await state.set_state(AdminStates.viewing_logs)
        
    except Exception as e:
        logger.error(f"Error in view_logs_handler: {str(e)}", exc_info=True)
        await message.answer(
            "❌ Не удалось загрузить логи. Пожалуйста, попробуйте позже.",
            reply_markup=get_admin_keyboard()
        )


@router.message(F.text.in_(["◀️ Назад", "◀️ Back"]))
async def back_to_main_handler(message: Message, state: FSMContext):
    """Handle back button to return to main menu."""
    try:
        # Импортируем get_start из basic.py
        from core.handlers.basic import get_start
        from aiogram import Bot
        bot = Bot.get_current()
        await get_start(message, bot, state)
    except Exception as e:
        logger.error(f"Error returning to main menu from admin: {e}", exc_info=True)
        await message.answer("Не удалось вернуться в главное меню. Попробуйте позже.")


# Register all handlers
router.message.register(admin_dashboard_handler, F.text == "🛡️ Админ панель")
router.message.register(search_users_handler, F.text == "🔍 Поиск пользователей")
router.message.register(karma_management_handler, F.text == "⚡ Управление кармой")
router.message.register(ban_management_handler, F.text == "🚫 Бан/разбан")
router.message.register(view_logs_handler, F.text == "📋 Логи действий")
router.message.register(back_to_main_handler, F.text == "◀️ Назад")

# For backward compatibility
def get_admin_router():
    """Get the admin router instance."""
    return router

# Export the router
__all__ = ['router', 'get_admin_router']
