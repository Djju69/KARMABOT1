"""
Router for SuperAdmin panel functionality.
Handles all super administrative operations including card generation, data deletion, and system management.
"""
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from typing import Optional, Union, Any, Dict
import logging

# Create router with a name
router = Router(name='superadmin_router')

# Import dependencies
from ..services.superadmin_service import superadmin_service
from ..services.admin_service import admin_service
from ..keyboards.reply_v2 import get_superadmin_keyboard, get_return_to_main_menu
from ..utils.locales_v2 import get_text, get_all_texts

logger = logging.getLogger(__name__)


def get_superadmin_router() -> Router:
    """Get the superadmin router with all handlers."""
    return router


class SuperAdminStates(StatesGroup):
    """FSM states for superadmin panel interactions."""
    viewing_dashboard = State()
    generating_cards = State()
    deleting_user_data = State()
    managing_roles = State()
    viewing_settings = State()


@router.message(F.text.in_(["👑 Супер-админ", "👑 SuperAdmin"]))
async def superadmin_dashboard_handler(message: Message, state: FSMContext):
    """Handle superadmin dashboard entry point."""
    try:
        # Check if user is superadmin
        user_id = message.from_user.id
        # TODO: Add role check here
        
        # Get superadmin statistics
        stats = await superadmin_service.get_superadmin_stats()
        
        text = (
            f"👑 <b>Панель супер-администратора</b>\n\n"
            f"📊 <b>Системная статистика:</b>\n"
            f"👥 Всего пользователей: <b>{stats['total_users']}</b>\n"
            f"✅ Активных: <b>{stats['active_users']}</b>\n"
            f"🚫 Заблокированных: <b>{stats['banned_users']}</b>\n"
            f"💳 Всего карт: <b>{stats['total_cards']}</b>\n"
            f"🔗 Привязанных: <b>{stats['bound_cards']}</b>\n"
            f"📋 Свободных: <b>{stats['unbound_cards']}</b>\n\n"
            f"🔧 <b>Системные логи:</b>\n"
            f"📝 Всего записей: <b>{stats['total_admin_logs']}</b>\n\n"
            f"🏥 <b>Состояние системы:</b>\n"
        )
        
        health = stats.get('system_health', {})
        health_emoji = "✅" if health.get('database_connected') else "❌"
        text += f"{health_emoji} База данных: {'Подключена' if health.get('database_connected') else 'Ошибка'}\n"
        
        health_emoji = "✅" if health.get('migrations_applied') else "❌"
        text += f"{health_emoji} Миграции: {'Применены' if health.get('migrations_applied') else 'Ошибка'}\n"
        
        health_emoji = "✅" if health.get('services_running') else "❌"
        text += f"{health_emoji} Сервисы: {'Работают' if health.get('services_running') else 'Ошибка'}\n"
        
        await message.answer(
            text,
            reply_markup=get_superadmin_keyboard(),
            parse_mode='HTML'
        )
        
        await state.set_state(SuperAdminStates.viewing_dashboard)
        
    except Exception as e:
        logger.error(f"Error in superadmin_dashboard_handler: {str(e)}", exc_info=True)
        await message.answer(
            "❌ Произошла ошибка при загрузке панели супер-админа. Пожалуйста, попробуйте позже.",
            reply_markup=get_return_to_main_menu()
        )


@router.message(F.text.in_(["🏭 Генерация карт", "🏭 Generate Cards"]))
async def generate_cards_handler(message: Message, state: FSMContext):
    """Handle card generation."""
    try:
        text = (
            "🏭 <b>Генерация пластиковых карт</b>\n\n"
            "Введите количество карт для генерации:\n"
            "<code>/generate [количество]</code>\n\n"
            "Примеры:\n"
            "• <code>/generate 100</code> - создать 100 карт\n"
            "• <code>/generate 1000</code> - создать 1000 карт\n\n"
            "⚠️ Максимальное количество за раз: 10000 карт"
        )
        
        await message.answer(
            text,
            reply_markup=get_superadmin_keyboard(),
            parse_mode='HTML'
        )
        
        await state.set_state(SuperAdminStates.generating_cards)
        
    except Exception as e:
        logger.error(f"Error in generate_cards_handler: {str(e)}", exc_info=True)
        await message.answer(
            "❌ Произошла ошибка. Пожалуйста, попробуйте позже.",
            reply_markup=get_superadmin_keyboard()
        )


@router.message(SuperAdminStates.generating_cards)
async def process_card_generation(message: Message, state: FSMContext):
    """Process card generation command."""
    try:
        command = message.text.strip()
        if not command.startswith('/generate'):
            await message.answer("❌ Неверный формат команды. Используйте /generate [количество]")
            return
        
        # Parse command
        parts = command.split()
        if len(parts) < 2:
            await message.answer("❌ Неверный формат команды. Используйте /generate [количество]")
            return
        
        try:
            count = int(parts[1])
        except ValueError:
            await message.answer("❌ Неверный формат количества.")
            return
        
        # Generate cards
        result = await superadmin_service.generate_cards(count, message.from_user.id)
        
        if result['success']:
            text = (
                f"✅ <b>Карты созданы</b>\n\n"
                f"📊 Создано: <b>{result['created_count']}</b> карт\n"
                f"📋 Диапазон: <b>{result['range']}</b>\n\n"
                f"💡 Карты готовы к использованию!"
            )
        else:
            text = f"❌ {result['message']}"
        
        await message.answer(
            text,
            reply_markup=get_superadmin_keyboard(),
            parse_mode='HTML'
        )
        
        await state.set_state(SuperAdminStates.viewing_dashboard)
        
    except Exception as e:
        logger.error(f"Error in process_card_generation: {str(e)}", exc_info=True)
        await message.answer(
            "❌ Ошибка при генерации карт. Пожалуйста, попробуйте позже.",
            reply_markup=get_superadmin_keyboard()
        )


@router.message(F.text.in_(["🗑️ Удаление данных", "🗑️ Delete Data"]))
async def delete_data_handler(message: Message, state: FSMContext):
    """Handle data deletion."""
    try:
        text = (
            "🗑️ <b>Удаление данных</b>\n\n"
            "⚠️ <b>ВНИМАНИЕ!</b> Это действие необратимо!\n\n"
            "Команды:\n"
            "<code>/delete_user [ID]</code> - удалить все данные пользователя\n"
            "<code>/delete_card [ID]</code> - удалить карту\n\n"
            "Примеры:\n"
            "• <code>/delete_user 123456789</code>\n"
            "• <code>/delete_card KS12340001</code>\n\n"
            "🚨 Будьте осторожны!"
        )
        
        await message.answer(
            text,
            reply_markup=get_superadmin_keyboard(),
            parse_mode='HTML'
        )
        
        await state.set_state(SuperAdminStates.deleting_user_data)
        
    except Exception as e:
        logger.error(f"Error in delete_data_handler: {str(e)}", exc_info=True)
        await message.answer(
            "❌ Произошла ошибка. Пожалуйста, попробуйте позже.",
            reply_markup=get_superadmin_keyboard()
        )


@router.message(SuperAdminStates.deleting_user_data)
async def process_data_deletion(message: Message, state: FSMContext):
    """Process data deletion command."""
    try:
        command = message.text.strip()
        
        if command.startswith('/delete_user'):
            # Parse delete user command
            parts = command.split()
            if len(parts) < 2:
                await message.answer("❌ Неверный формат команды. Используйте /delete_user [ID]")
                return
            
            try:
                user_id = int(parts[1])
            except ValueError:
                await message.answer("❌ Неверный формат ID.")
                return
            
            # Delete user data
            result = await superadmin_service.delete_user_data(user_id, message.from_user.id)
            
        elif command.startswith('/delete_card'):
            # Parse delete card command
            parts = command.split()
            if len(parts) < 2:
                await message.answer("❌ Неверный формат команды. Используйте /delete_card [ID]")
                return
            
            card_id = parts[1]
            
            # Delete card
            result = await superadmin_service.delete_card(card_id, message.from_user.id)
            
        else:
            await message.answer("❌ Неверная команда. Используйте /delete_user или /delete_card")
            return
        
        if result['success']:
            text = f"✅ {result['message']}"
            if 'deleted_user' in result:
                text += f"\n👤 Удален: {result['deleted_user']}"
            elif 'deleted_card' in result:
                text += f"\n💳 Удалена: {result['deleted_card']}"
        else:
            text = f"❌ {result['message']}"
        
        await message.answer(
            text,
            reply_markup=get_superadmin_keyboard(),
            parse_mode='HTML'
        )
        
        await state.set_state(SuperAdminStates.viewing_dashboard)
        
    except Exception as e:
        logger.error(f"Error in process_data_deletion: {str(e)}", exc_info=True)
        await message.answer(
            "❌ Ошибка при удалении данных. Пожалуйста, попробуйте позже.",
            reply_markup=get_superadmin_keyboard()
        )


@router.message(F.text.in_(["👥 Управление админами", "👥 Manage Admins"]))
async def manage_admins_handler(message: Message, state: FSMContext):
    """Handle admin management."""
    try:
        text = (
            "👥 <b>Управление ролями</b>\n\n"
            "Введите команду в формате:\n"
            "<code>/role [ID] [роль]</code>\n\n"
            "Доступные роли:\n"
            "• <code>user</code> - обычный пользователь\n"
            "• <code>partner</code> - партнер\n"
            "• <code>admin</code> - администратор\n"
            "• <code>superadmin</code> - супер-администратор\n\n"
            "Примеры:\n"
            "• <code>/role 123456789 admin</code>\n"
            "• <code>/role 123456789 user</code>"
        )
        
        await message.answer(
            text,
            reply_markup=get_superadmin_keyboard(),
            parse_mode='HTML'
        )
        
        await state.set_state(SuperAdminStates.managing_roles)
        
    except Exception as e:
        logger.error(f"Error in manage_admins_handler: {str(e)}", exc_info=True)
        await message.answer(
            "❌ Произошла ошибка. Пожалуйста, попробуйте позже.",
            reply_markup=get_superadmin_keyboard()
        )


@router.message(SuperAdminStates.managing_roles)
async def process_role_change(message: Message, state: FSMContext):
    """Process role change command."""
    try:
        command = message.text.strip()
        if not command.startswith('/role'):
            await message.answer("❌ Неверный формат команды. Используйте /role [ID] [роль]")
            return
        
        # Parse command
        parts = command.split()
        if len(parts) < 3:
            await message.answer("❌ Неверный формат команды. Используйте /role [ID] [роль]")
            return
        
        try:
            user_id = int(parts[1])
            new_role = parts[2].lower()
        except ValueError:
            await message.answer("❌ Неверный формат ID.")
            return
        
        # Change role
        result = await superadmin_service.manage_admin_role(
            user_id, new_role, message.from_user.id
        )
        
        if result['success']:
            text = (
                f"✅ <b>Роль изменена</b>\n\n"
                f"👤 Пользователь: <code>{user_id}</code>\n"
                f"🔄 Было: <b>{result['old_role']}</b>\n"
                f"🔄 Стало: <b>{result['new_role']}</b>"
            )
        else:
            text = f"❌ {result['message']}"
        
        await message.answer(
            text,
            reply_markup=get_superadmin_keyboard(),
            parse_mode='HTML'
        )
        
        await state.set_state(SuperAdminStates.viewing_dashboard)
        
    except Exception as e:
        logger.error(f"Error in process_role_change: {str(e)}", exc_info=True)
        await message.answer(
            "❌ Ошибка при изменении роли. Пожалуйста, попробуйте позже.",
            reply_markup=get_superadmin_keyboard()
        )


@router.message(F.text.in_(["⚙️ Системные настройки", "⚙️ System Settings"]))
async def system_settings_handler(message: Message, state: FSMContext):
    """Handle system settings viewing."""
    try:
        # Get system settings
        settings = await superadmin_service.get_system_settings()
        
        text = (
            "⚙️ <b>Системные настройки</b>\n\n"
            "🔧 <b>Конфигурация кармы:</b>\n"
        )
        
        karma_config = settings.get('karma_config', {})
        text += f"📊 Пороги уровней: {karma_config.get('level_thresholds', [])}\n"
        text += f"🎁 Бонус за вход: {karma_config.get('daily_login_bonus', 0)}\n"
        text += f"💳 Бонус за карту: {karma_config.get('card_bind_bonus', 0)}\n"
        text += f"🔗 Реферальный бонус: {karma_config.get('referral_bonus', 0)}\n"
        text += f"⚡ Лимит админа: {karma_config.get('admin_karma_limit', 0)}\n"
        text += f"🏭 Лимит генерации: {karma_config.get('card_generation_limit', 0)}\n"
        text += f"⏱️ Лимит запросов: {karma_config.get('rate_limit_per_minute', 0)}/мин\n\n"
        
        text += "💳 <b>Конфигурация карт:</b>\n"
        card_config = settings.get('card_config', {})
        text += f"🏷️ Префикс: {card_config.get('prefix', '')}\n"
        text += f"🔢 Стартовый номер: {card_config.get('start_number', 0)}\n"
        text += f"📝 Формат: {card_config.get('format', '')}\n"
        text += f"🖨️ Печатный формат: {card_config.get('printable_format', '')}\n\n"
        
        text += "🚀 <b>Функции системы:</b>\n"
        features = settings.get('features', {})
        for feature, enabled in features.items():
            status = "✅" if enabled else "❌"
            text += f"{status} {feature}: {'Включено' if enabled else 'Отключено'}\n"
        
        await message.answer(
            text,
            reply_markup=get_superadmin_keyboard(),
            parse_mode='HTML'
        )
        
        await state.set_state(SuperAdminStates.viewing_settings)
        
    except Exception as e:
        logger.error(f"Error in system_settings_handler: {str(e)}", exc_info=True)
        await message.answer(
            "❌ Не удалось загрузить настройки системы. Пожалуйста, попробуйте позже.",
            reply_markup=get_superadmin_keyboard()
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
        logger.error(f"Error returning to main menu from superadmin: {e}", exc_info=True)
        await message.answer("Не удалось вернуться в главное меню. Попробуйте позже.")


# Register all handlers
router.message.register(superadmin_dashboard_handler, F.text == "👑 Супер-админ")
router.message.register(generate_cards_handler, F.text == "🏭 Генерация карт")
router.message.register(delete_data_handler, F.text == "🗑️ Удаление данных")
router.message.register(manage_admins_handler, F.text == "👥 Управление админами")
router.message.register(system_settings_handler, F.text == "⚙️ Системные настройки")
router.message.register(back_to_main_handler, F.text == "◀️ Назад")

# For backward compatibility
def get_superadmin_router():
    """Get the superadmin router instance."""
    return router

# Export the router
__all__ = ['router', 'get_superadmin_router']
