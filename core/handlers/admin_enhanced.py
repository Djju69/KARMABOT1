"""
Enhanced Admin Handlers
Advanced admin functionality with comprehensive management features
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from core.settings import settings
from core.utils.locales_v2 import get_text, translations
from core.services import admins_service, profile_service
from core.keyboards.inline_v2 import get_admin_cabinet_inline
from core.database.db_v2 import db_v2
from core.models import User, Card, Transaction, ModerationLog
from core.logger import get_logger

logger = get_logger(__name__)

router = Router(name=__name__)

class AdminStates(StatesGroup):
    waiting_for_user_search = State()
    waiting_for_role_change = State()
    waiting_for_bulk_action = State()
    waiting_for_system_command = State()

# Enhanced admin commands
@router.message(Command("admin"))
async def open_enhanced_admin_cabinet(message: Message, bot: Bot, state: FSMContext):
    """Open enhanced admin cabinet with comprehensive features"""
    logger.info(f"Enhanced admin cabinet accessed by user {message.from_user.id}")
    
    try:
        if not settings.features.moderation:
            await message.answer("🚧 Модуль модерации отключён.")
            return
            
        is_admin = await admins_service.is_admin(message.from_user.id)
        if not is_admin:
            await message.answer("❌ Доступ запрещён.")
            return
            
        lang = await profile_service.get_lang(message.from_user.id)
        is_superadmin = (int(message.from_user.id) == int(settings.bots.admin_id))
        
        # Get system statistics
        stats = await get_system_statistics()
        
        # Create enhanced keyboard
        keyboard = create_enhanced_admin_keyboard(is_superadmin, lang)
        
        # Enhanced welcome message with stats
        welcome_text = f"""
🛡️ **Расширенная админ-панель**

📊 **Статистика системы:**
👥 Пользователей: {stats['total_users']}
🏪 Партнеров: {stats['active_partners']}
📄 Ожидают модерации: {stats['pending_moderation']}
💰 Транзакций сегодня: {stats['today_transactions']}
💵 Общая выручка: {stats['total_revenue']:,} ₽

🔧 **Доступные функции:**
• Управление пользователями
• Система модерации
• Аналитика и отчеты
• Мониторинг системы
• Настройки безопасности

Выберите раздел для управления:
        """
        
        await message.answer(welcome_text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Error in enhanced admin cabinet: {e}")
        await message.answer("❌ Ошибка загрузки админ-панели.")

async def get_system_statistics() -> Dict[str, Any]:
    """Get comprehensive system statistics"""
    try:
        with db_v2.get_session() as session:
            total_users = session.query(User).count()
            active_partners = session.query(User).filter(
                User.role == "partner", 
                User.is_active == True
            ).count()
            pending_moderation = session.query(Card).filter(Card.status == "pending").count()
            
            today = datetime.utcnow().date()
            today_transactions = session.query(Transaction).filter(
                Transaction.created_at >= today
            ).count()
            
            total_revenue = session.query(Transaction.amount).all()
            total_revenue = sum(t.amount for t in total_revenue) if total_revenue else 0
            
            return {
                "total_users": total_users,
                "active_partners": active_partners,
                "pending_moderation": pending_moderation,
                "today_transactions": today_transactions,
                "total_revenue": total_revenue
            }
    except Exception as e:
        logger.error(f"Error getting system statistics: {e}")
        return {
            "total_users": 0,
            "active_partners": 0,
            "pending_moderation": 0,
            "today_transactions": 0,
            "total_revenue": 0
        }

def create_enhanced_admin_keyboard(is_superadmin: bool, lang: str) -> InlineKeyboardMarkup:
    """Create enhanced admin keyboard with comprehensive features"""
    keyboard = []
    
    # User Management
    keyboard.append([
        InlineKeyboardButton(
            text="👥 Управление пользователями",
            callback_data="admin:users"
        )
    ])
    
    # Moderation
    keyboard.append([
        InlineKeyboardButton(
            text="🛡️ Модерация контента",
            callback_data="admin:moderation"
        )
    ])
    
    # Analytics
    keyboard.append([
        InlineKeyboardButton(
            text="📊 Аналитика и отчеты",
            callback_data="admin:analytics"
        )
    ])
    
    # System Monitoring
    keyboard.append([
        InlineKeyboardButton(
            text="🔍 Мониторинг системы",
            callback_data="admin:monitoring"
        )
    ])
    
    # Financial Management
    keyboard.append([
        InlineKeyboardButton(
            text="💰 Финансовый учет",
            callback_data="admin:finance"
        )
    ])
    
    # Super Admin features
    if is_superadmin:
        keyboard.append([
            InlineKeyboardButton(
                text="⚙️ Системные настройки",
                callback_data="admin:system_settings"
            )
        ])
        keyboard.append([
            InlineKeyboardButton(
                text="🔐 Безопасность",
                callback_data="admin:security"
            )
        ])
    
    # Quick Actions
    keyboard.append([
        InlineKeyboardButton(
            text="⚡ Быстрые действия",
            callback_data="admin:quick_actions"
        )
    ])
    
    # WebApp Dashboard
    keyboard.append([
        InlineKeyboardButton(
            text="🌐 WebApp дашборд",
            callback_data="admin:webapp_dashboard"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

@router.callback_query(F.data.startswith("admin:"))
async def handle_admin_callback(callback: CallbackQuery, bot: Bot, state: FSMContext):
    """Handle admin callback queries"""
    action = callback.data.split(":", 1)[1]
    
    try:
        if action == "users":
            await show_user_management(callback, bot)
        elif action == "moderation":
            await show_moderation_panel(callback, bot)
        elif action == "analytics":
            await show_analytics_panel(callback, bot)
        elif action == "monitoring":
            await show_system_monitoring(callback, bot)
        elif action == "finance":
            await show_financial_management(callback, bot)
        elif action == "system_settings":
            await show_system_settings(callback, bot)
        elif action == "security":
            await show_security_panel(callback, bot)
        elif action == "quick_actions":
            await show_quick_actions(callback, bot)
        elif action == "webapp_dashboard":
            await open_webapp_dashboard(callback, bot)
        else:
            await callback.answer("❌ Неизвестная команда")
            
    except Exception as e:
        logger.error(f"Error handling admin callback {action}: {e}")
        await callback.answer("❌ Ошибка выполнения команды")

async def show_user_management(callback: CallbackQuery, bot: Bot):
    """Show user management interface"""
    try:
        stats = await get_system_statistics()
        
        keyboard = [
            [
                InlineKeyboardButton(
                    text="🔍 Поиск пользователей",
                    callback_data="admin:search_users"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📊 Статистика пользователей",
                    callback_data="admin:user_stats"
                )
            ],
            [
                InlineKeyboardButton(
                    text="👥 Активные пользователи",
                    callback_data="admin:active_users"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🚫 Заблокированные",
                    callback_data="admin:blocked_users"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📤 Экспорт данных",
                    callback_data="admin:export_users"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Назад",
                    callback_data="admin:back"
                )
            ]
        ]
        
        text = f"""
👥 **Управление пользователями**

📊 **Статистика:**
• Всего пользователей: {stats['total_users']}
• Активных партнеров: {stats['active_partners']}
• Новых за сегодня: {await get_today_new_users()}

🔧 **Доступные действия:**
• Поиск и фильтрация пользователей
• Просмотр статистики
• Управление активностью
• Экспорт данных

Выберите действие:
        """
        
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error showing user management: {e}")
        await callback.answer("❌ Ошибка загрузки управления пользователями")

async def show_moderation_panel(callback: CallbackQuery, bot: Bot):
    """Show moderation panel"""
    try:
        stats = await get_system_statistics()
        
        keyboard = [
            [
                InlineKeyboardButton(
                    text="📄 Ожидают модерации",
                    callback_data="admin:moderation_queue"
                )
            ],
            [
                InlineKeyboardButton(
                    text="✅ Одобренные карточки",
                    callback_data="admin:approved_cards"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отклоненные",
                    callback_data="admin:rejected_cards"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📊 Статистика модерации",
                    callback_data="admin:moderation_stats"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⚙️ Настройки модерации",
                    callback_data="admin:moderation_settings"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Назад",
                    callback_data="admin:back"
                )
            ]
        ]
        
        text = f"""
🛡️ **Панель модерации**

📊 **Статистика:**
• Ожидают модерации: {stats['pending_moderation']}
• Одобрено сегодня: {await get_today_approved_cards()}
• Отклонено сегодня: {await get_today_rejected_cards()}

🔧 **Доступные действия:**
• Модерация контента
• Просмотр статистики
• Настройка правил

Выберите действие:
        """
        
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error showing moderation panel: {e}")
        await callback.answer("❌ Ошибка загрузки панели модерации")

async def show_analytics_panel(callback: CallbackQuery, bot: Bot):
    """Show analytics panel"""
    try:
        keyboard = [
            [
                InlineKeyboardButton(
                    text="📈 Общая аналитика",
                    callback_data="admin:general_analytics"
                )
            ],
            [
                InlineKeyboardButton(
                    text="👥 Аналитика пользователей",
                    callback_data="admin:user_analytics"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💰 Финансовая аналитика",
                    callback_data="admin:financial_analytics"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📊 Отчеты",
                    callback_data="admin:reports"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📤 Экспорт отчетов",
                    callback_data="admin:export_reports"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Назад",
                    callback_data="admin:back"
                )
            ]
        ]
        
        text = """
📊 **Панель аналитики**

🔧 **Доступные отчеты:**
• Общая статистика системы
• Аналитика пользователей
• Финансовые показатели
• Детальные отчеты

📈 **Возможности:**
• Графики и диаграммы
• Сравнительный анализ
• Экспорт данных
• Настраиваемые периоды

Выберите тип аналитики:
        """
        
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error showing analytics panel: {e}")
        await callback.answer("❌ Ошибка загрузки панели аналитики")

async def show_system_monitoring(callback: CallbackQuery, bot: Bot):
    """Show system monitoring panel"""
    try:
        system_health = await get_system_health()
        
        keyboard = [
            [
                InlineKeyboardButton(
                    text="💚 Статус системы",
                    callback_data="admin:system_status"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📊 Производительность",
                    callback_data="admin:performance"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔍 Логи системы",
                    callback_data="admin:system_logs"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🚨 Алерты",
                    callback_data="admin:alerts"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Назад",
                    callback_data="admin:back"
                )
            ]
        ]
        
        status_emoji = "💚" if system_health["status"] == "healthy" else "⚠️" if system_health["status"] == "warning" else "🔴"
        
        text = f"""
🔍 **Мониторинг системы**

{status_emoji} **Статус:** {system_health["status"].upper()}
⏱️ **Время работы:** {system_health["uptime"]}
💾 **Память:** {system_health["memory_usage"]}%
🖥️ **CPU:** {system_health["cpu_usage"]}%
💿 **Диск:** {system_health["disk_usage"]}%

🔧 **Доступные функции:**
• Мониторинг производительности
• Просмотр логов
• Управление алертами

Выберите действие:
        """
        
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error showing system monitoring: {e}")
        await callback.answer("❌ Ошибка загрузки мониторинга системы")

async def show_financial_management(callback: CallbackQuery, bot: Bot):
    """Show financial management panel"""
    try:
        stats = await get_system_statistics()
        
        keyboard = [
            [
                InlineKeyboardButton(
                    text="💰 Общая выручка",
                    callback_data="admin:total_revenue"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📊 Транзакции",
                    callback_data="admin:transactions"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏪 Партнерские выплаты",
                    callback_data="admin:partner_payouts"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📈 Финансовая аналитика",
                    callback_data="admin:financial_analytics"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Назад",
                    callback_data="admin:back"
                )
            ]
        ]
        
        text = f"""
💰 **Финансовый учет**

📊 **Основные показатели:**
• Общая выручка: {stats['total_revenue']:,} ₽
• Транзакций сегодня: {stats['today_transactions']}
• Средний чек: {await get_average_transaction_amount():.2f} ₽

🔧 **Доступные функции:**
• Просмотр транзакций
• Управление выплатами
• Финансовая аналитика

Выберите действие:
        """
        
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error showing financial management: {e}")
        await callback.answer("❌ Ошибка загрузки финансового учета")

async def show_quick_actions(callback: CallbackQuery, bot: Bot):
    """Show quick actions panel"""
    try:
        keyboard = [
            [
                InlineKeyboardButton(
                    text="🔄 Обновить статистику",
                    callback_data="admin:refresh_stats"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🧹 Очистить кэш",
                    callback_data="admin:clear_cache"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📤 Создать бэкап",
                    callback_data="admin:create_backup"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔍 Проверить систему",
                    callback_data="admin:system_check"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Назад",
                    callback_data="admin:back"
                )
            ]
        ]
        
        text = """
⚡ **Быстрые действия**

🔧 **Доступные команды:**
• Обновление статистики
• Очистка кэша
• Создание резервных копий
• Проверка системы

⚠️ **Внимание:** Некоторые действия могут занять время

Выберите действие:
        """
        
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error showing quick actions: {e}")
        await callback.answer("❌ Ошибка загрузки быстрых действий")

async def open_webapp_dashboard(callback: CallbackQuery, bot: Bot):
    """Open WebApp admin dashboard"""
    try:
        webapp_url = f"{settings.webapp.base_url}/api/admin/dashboard-enhanced"
        
        keyboard = [
            [
                InlineKeyboardButton(
                    text="🌐 Открыть WebApp",
                    url=webapp_url
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Назад",
                    callback_data="admin:back"
                )
            ]
        ]
        
        text = f"""
🌐 **WebApp админ-дашборд**

🔗 **Ссылка:** {webapp_url}

📱 **Возможности WebApp:**
• Интерактивные графики
• Расширенная аналитика
• Удобное управление
• Мобильная адаптация

Нажмите кнопку для открытия:
        """
        
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error opening WebApp dashboard: {e}")
        await callback.answer("❌ Ошибка открытия WebApp")

# Helper functions
async def get_today_new_users() -> int:
    """Get count of new users today"""
    try:
        with db_v2.get_session() as session:
            today = datetime.utcnow().date()
            return session.query(User).filter(
                User.created_at >= today
            ).count()
    except Exception:
        return 0

async def get_today_approved_cards() -> int:
    """Get count of approved cards today"""
    try:
        with db_v2.get_session() as session:
            today = datetime.utcnow().date()
            return session.query(ModerationLog).filter(
                ModerationLog.action == "approve",
                ModerationLog.created_at >= today
            ).count()
    except Exception:
        return 0

async def get_today_rejected_cards() -> int:
    """Get count of rejected cards today"""
    try:
        with db_v2.get_session() as session:
            today = datetime.utcnow().date()
            return session.query(ModerationLog).filter(
                ModerationLog.action == "reject",
                ModerationLog.created_at >= today
            ).count()
    except Exception:
        return 0

async def get_average_transaction_amount() -> float:
    """Get average transaction amount"""
    try:
        with db_v2.get_session() as session:
            transactions = session.query(Transaction.amount).all()
            if transactions:
                return sum(t.amount for t in transactions) / len(transactions)
            return 0.0
    except Exception:
        return 0.0

async def get_system_health() -> Dict[str, Any]:
    """Get system health status"""
    try:
        # Mock system health data
        return {
            "status": "healthy",
            "uptime": "99.9%",
            "memory_usage": 65.2,
            "cpu_usage": 23.8,
            "disk_usage": 45.7,
            "database_status": "healthy",
            "redis_status": "healthy"
        }
    except Exception:
        return {
            "status": "error",
            "uptime": "0%",
            "memory_usage": 0,
            "cpu_usage": 0,
            "disk_usage": 0,
            "database_status": "error",
            "redis_status": "error"
        }
