"""
Роутер для живых дашбордов
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from typing import Optional, Dict, Any
import logging

from ..services.live_dashboard import live_dashboard
from ..utils.locales_v2 import get_text
from ..security.roles import get_user_role

logger = logging.getLogger(__name__)
router = Router(name='live_dashboard_router')


class LiveDashboardStates(StatesGroup):
    """Состояния живых дашбордов"""
    viewing_moderation = State()
    viewing_notifications = State()
    viewing_system = State()


@router.message(F.text.in_(["📊 Модерация", "📊 Moderation"]))
async def moderation_dashboard_handler(message: Message, state: FSMContext):
    """Дашборд модерации"""
    try:
        user_id = message.from_user.id
        user_role = await get_user_role(user_id)
        
        # Проверить права доступа
        if user_role not in ['admin', 'super_admin']:
            await message.answer(
                "❌ <b>Доступ запрещен</b>\n\n"
                "Дашборды доступны только администраторам.",
                parse_mode='HTML'
            )
            return
        
        # Получить данные дашборда
        dashboard = await live_dashboard.get_moderation_dashboard()
        dashboard_message = live_dashboard.format_dashboard_message(dashboard)
        
        # Создать клавиатуру управления
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Обновить", callback_data="dashboard_refresh_moderation"),
                InlineKeyboardButton(text="⏸️ Пауза", callback_data="dashboard_pause_moderation")
            ],
            [
                InlineKeyboardButton(text="📊 Другие дашборды", callback_data="dashboard_menu"),
                InlineKeyboardButton(text="◀️ Назад", callback_data="dashboard_back")
            ]
        ])
        
        await message.answer(
            dashboard_message,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
        await state.set_state(LiveDashboardStates.viewing_moderation)
        
    except Exception as e:
        logger.error(f"Error in moderation_dashboard_handler: {e}")
        await message.answer("❌ Ошибка при загрузке дашборда модерации")


@router.message(F.text.in_(["🔔 Уведомления", "🔔 Notifications"]))
async def notifications_dashboard_handler(message: Message, state: FSMContext):
    """Дашборд уведомлений"""
    try:
        user_id = message.from_user.id
        user_role = await get_user_role(user_id)
        
        # Проверить права доступа
        if user_role not in ['admin', 'super_admin']:
            await message.answer(
                "❌ <b>Доступ запрещен</b>\n\n"
                "Дашборды доступны только администраторам.",
                parse_mode='HTML'
            )
            return
        
        # Получить данные дашборда
        dashboard = await live_dashboard.get_notifications_dashboard()
        dashboard_message = live_dashboard.format_dashboard_message(dashboard)
        
        # Создать клавиатуру управления
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Обновить", callback_data="dashboard_refresh_notifications"),
                InlineKeyboardButton(text="⏸️ Пауза", callback_data="dashboard_pause_notifications")
            ],
            [
                InlineKeyboardButton(text="📊 Другие дашборды", callback_data="dashboard_menu"),
                InlineKeyboardButton(text="◀️ Назад", callback_data="dashboard_back")
            ]
        ])
        
        await message.answer(
            dashboard_message,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
        await state.set_state(LiveDashboardStates.viewing_notifications)
        
    except Exception as e:
        logger.error(f"Error in notifications_dashboard_handler: {e}")
        await message.answer("❌ Ошибка при загрузке дашборда уведомлений")


@router.message(F.text.in_(["⚙️ Система", "⚙️ System"]))
async def system_dashboard_handler(message: Message, state: FSMContext):
    """Дашборд системы"""
    try:
        user_id = message.from_user.id
        user_role = await get_user_role(user_id)
        
        # Проверить права доступа
        if user_role not in ['admin', 'super_admin']:
            await message.answer(
                "❌ <b>Доступ запрещен</b>\n\n"
                "Дашборды доступны только администраторам.",
                parse_mode='HTML'
            )
            return
        
        # Получить данные дашборда
        dashboard = await live_dashboard.get_system_dashboard()
        dashboard_message = live_dashboard.format_dashboard_message(dashboard)
        
        # Создать клавиатуру управления
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Обновить", callback_data="dashboard_refresh_system"),
                InlineKeyboardButton(text="⏸️ Пауза", callback_data="dashboard_pause_system")
            ],
            [
                InlineKeyboardButton(text="📊 Другие дашборды", callback_data="dashboard_menu"),
                InlineKeyboardButton(text="◀️ Назад", callback_data="dashboard_back")
            ]
        ])
        
        await message.answer(
            dashboard_message,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
        await state.set_state(LiveDashboardStates.viewing_system)
        
    except Exception as e:
        logger.error(f"Error in system_dashboard_handler: {e}")
        await message.answer("❌ Ошибка при загрузке дашборда системы")


@router.callback_query(F.data.startswith("dashboard_refresh_"))
async def refresh_dashboard_callback(callback: CallbackQuery, state: FSMContext):
    """Обновить дашборд"""
    try:
        dashboard_type = callback.data.replace("dashboard_refresh_", "")
        
        # Показать индикатор загрузки
        await callback.message.edit_text(
            f"🔄 <b>Обновление дашборда...</b>\n\n"
            "⏳ Загружаем актуальные данные...",
            parse_mode='HTML'
        )
        
        # Получить обновленные данные
        if dashboard_type == "moderation":
            dashboard = await live_dashboard.get_moderation_dashboard()
        elif dashboard_type == "notifications":
            dashboard = await live_dashboard.get_notifications_dashboard()
        elif dashboard_type == "system":
            dashboard = await live_dashboard.get_system_dashboard()
        else:
            await callback.answer("❌ Неизвестный тип дашборда")
            return
        
        # Форматировать сообщение
        dashboard_message = live_dashboard.format_dashboard_message(dashboard)
        
        # Создать клавиатуру управления
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Обновить", callback_data=f"dashboard_refresh_{dashboard_type}"),
                InlineKeyboardButton(text="⏸️ Пауза", callback_data=f"dashboard_pause_{dashboard_type}")
            ],
            [
                InlineKeyboardButton(text="📊 Другие дашборды", callback_data="dashboard_menu"),
                InlineKeyboardButton(text="◀️ Назад", callback_data="dashboard_back")
            ]
        ])
        
        await callback.message.edit_text(
            dashboard_message,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
        await callback.answer("✅ Дашборд обновлен!")
        
    except Exception as e:
        logger.error(f"Error in refresh_dashboard_callback: {e}")
        await callback.answer("❌ Ошибка при обновлении дашборда")


@router.callback_query(F.data.startswith("dashboard_pause_"))
async def pause_dashboard_callback(callback: CallbackQuery, state: FSMContext):
    """Приостановить автообновление дашборда"""
    try:
        dashboard_type = callback.data.replace("dashboard_pause_", "")
        
        # Остановить автообновление
        await live_dashboard.stop_auto_refresh(dashboard_type)
        
        # Обновить кнопку
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Обновить", callback_data=f"dashboard_refresh_{dashboard_type}"),
                InlineKeyboardButton(text="▶️ Запустить", callback_data=f"dashboard_resume_{dashboard_type}")
            ],
            [
                InlineKeyboardButton(text="📊 Другие дашборды", callback_data="dashboard_menu"),
                InlineKeyboardButton(text="◀️ Назад", callback_data="dashboard_back")
            ]
        ])
        
        await callback.message.edit_reply_markup(reply_markup=keyboard)
        await callback.answer("⏸️ Автообновление приостановлено")
        
    except Exception as e:
        logger.error(f"Error in pause_dashboard_callback: {e}")
        await callback.answer("❌ Ошибка при приостановке дашборда")


@router.callback_query(F.data.startswith("dashboard_resume_"))
async def resume_dashboard_callback(callback: CallbackQuery, state: FSMContext):
    """Возобновить автообновление дашборда"""
    try:
        dashboard_type = callback.data.replace("dashboard_resume_", "")
        
        # Запустить автообновление
        await live_dashboard.start_auto_refresh(
            dashboard_type,
            self._update_dashboard_message,
            callback.from_user.id
        )
        
        # Обновить кнопку
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Обновить", callback_data=f"dashboard_refresh_{dashboard_type}"),
                InlineKeyboardButton(text="⏸️ Пауза", callback_data=f"dashboard_pause_{dashboard_type}")
            ],
            [
                InlineKeyboardButton(text="📊 Другие дашборды", callback_data="dashboard_menu"),
                InlineKeyboardButton(text="◀️ Назад", callback_data="dashboard_back")
            ]
        ])
        
        await callback.message.edit_reply_markup(reply_markup=keyboard)
        await callback.answer("▶️ Автообновление запущено")
        
    except Exception as e:
        logger.error(f"Error in resume_dashboard_callback: {e}")
        await callback.answer("❌ Ошибка при запуске дашборда")


@router.callback_query(F.data == "dashboard_menu")
async def dashboard_menu_callback(callback: CallbackQuery, state: FSMContext):
    """Меню дашбордов"""
    try:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📊 Модерация", callback_data="dashboard_show_moderation"),
                InlineKeyboardButton(text="🔔 Уведомления", callback_data="dashboard_show_notifications")
            ],
            [
                InlineKeyboardButton(text="⚙️ Система", callback_data="dashboard_show_system")
            ],
            [
                InlineKeyboardButton(text="◀️ Назад", callback_data="dashboard_back")
            ]
        ])
        
        await callback.message.edit_text(
            "📊 <b>Живые дашборды</b>\n\n"
            "Выберите дашборд для просмотра:\n\n"
            "📊 <b>Модерация</b> - статистика карточек\n"
            "🔔 <b>Уведомления</b> - SMS и уведомления\n"
            "⚙️ <b>Система</b> - статус компонентов\n\n"
            "💡 Все дашборды поддерживают автообновление!",
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in dashboard_menu_callback: {e}")
        await callback.answer("❌ Ошибка при показе меню дашбордов")


@router.callback_query(F.data.startswith("dashboard_show_"))
async def show_dashboard_callback(callback: CallbackQuery, state: FSMContext):
    """Показать конкретный дашборд"""
    try:
        dashboard_type = callback.data.replace("dashboard_show_", "")
        
        # Получить данные дашборда
        if dashboard_type == "moderation":
            dashboard = await live_dashboard.get_moderation_dashboard()
        elif dashboard_type == "notifications":
            dashboard = await live_dashboard.get_notifications_dashboard()
        elif dashboard_type == "system":
            dashboard = await live_dashboard.get_system_dashboard()
        else:
            await callback.answer("❌ Неизвестный тип дашборда")
            return
        
        # Форматировать сообщение
        dashboard_message = live_dashboard.format_dashboard_message(dashboard)
        
        # Создать клавиатуру управления
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Обновить", callback_data=f"dashboard_refresh_{dashboard_type}"),
                InlineKeyboardButton(text="⏸️ Пауза", callback_data=f"dashboard_pause_{dashboard_type}")
            ],
            [
                InlineKeyboardButton(text="📊 Другие дашборды", callback_data="dashboard_menu"),
                InlineKeyboardButton(text="◀️ Назад", callback_data="dashboard_back")
            ]
        ])
        
        await callback.message.edit_text(
            dashboard_message,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in show_dashboard_callback: {e}")
        await callback.answer("❌ Ошибка при показе дашборда")


@router.callback_query(F.data == "dashboard_back")
async def dashboard_back_callback(callback: CallbackQuery, state: FSMContext):
    """Возврат к админскому меню"""
    try:
        # Остановить все автообновления
        await live_dashboard.stop_auto_refresh("moderation")
        await live_dashboard.stop_auto_refresh("notifications")
        await live_dashboard.stop_auto_refresh("system")
        
        # Показать админское меню
        from core.keyboards.unified_menu import get_admin_cabinet_keyboard
        keyboard = get_admin_cabinet_keyboard('admin')
        
        await callback.message.edit_text(
            "👨‍💼 <b>Админский кабинет</b>\n\n"
            "Добро пожаловать в панель администратора!\n\n"
            "🔍 <b>Доступные функции:</b>\n"
            "• Категории и витрина\n"
            "• ИИ помощник\n"
            "• Живые дашборды\n"
            "• Админ кабинет в Odoo\n\n"
            "Выберите действие:",
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
        await state.clear()
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in dashboard_back_callback: {e}")
        await callback.answer("❌ Ошибка при возврате")
    
    async def _update_dashboard_message(self, user_id: int, message: str):
        """Обновить сообщение дашборда"""
        try:
            # Здесь должна быть логика обновления сообщения
            # Пока просто логируем
            logger.info(f"Updating dashboard message for user {user_id}")
        except Exception as e:
            logger.error(f"Error updating dashboard message: {e}")


def get_live_dashboard_router() -> Router:
    """Получить роутер живых дашбордов"""
    return router
