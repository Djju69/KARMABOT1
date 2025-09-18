"""
Admin cabinet: inline menu and callbacks under adm:* namespace.
Conditioned by FEATURE_MODERATION and admin whitelist (settings.bots.admin_id for MVP).
"""
import logging
import logging
import contextlib
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from core.settings import settings
from core.utils.locales_v2 import get_text, translations
from core.services import admins_service
from core.services.profile import profile_service
from core.utils.admin_logger import log_admin_action_direct
from core.keyboards.inline_v2 import (
    get_admin_cabinet_inline, 
    get_superadmin_inline, 
    get_superadmin_delete_inline
)
from core.utils.locales_v2 import translations, get_text
from ..keyboards.reply_v2 import get_main_menu_reply, get_admin_keyboard, get_superadmin_keyboard
from ..database.db_v2 import db_v2

logger = logging.getLogger(__name__)

router = Router(name=__name__)


async def admin_cabinet_handler(message: Message, state: FSMContext):
    """Handle admin cabinet entry point."""
    try:
        user_id = message.from_user.id
        
        # Check if user is admin or super admin
        from core.security.roles import get_user_role
        user_role = await get_user_role(user_id)
        role_name = getattr(user_role, "name", str(user_role)).lower()
        
        if role_name not in ("admin", "super_admin"):
            await message.answer("⛔ Недостаточно прав для доступа к админ-кабинету")
            return
        
        # Show admin cabinet reply keyboard
        from core.keyboards.reply_v2 import get_admin_keyboard, get_superadmin_keyboard
        
        if role_name == "super_admin":
            keyboard = get_superadmin_keyboard()
            text = "👑 <b>Супер-админ панель</b>\n\nВыберите действие:"
        else:
            keyboard = get_admin_keyboard()
            text = "🛡️ <b>Админ панель</b>\n\nВыберите действие:"
        
        await message.answer(
            text,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"Error in admin_cabinet_handler: {str(e)}", exc_info=True)
        await message.answer("❌ Произошла ошибка при открытии админ-кабинета. Пожалуйста, попробуйте позже.")


@router.message(F.text.in_(["🌐 Язык", "🌐 Language", "🌐 Ngôn ngữ", "🌐 언어"]))
async def admin_language_handler(message: Message, state: FSMContext):
    """Handle language selection in admin cabinet."""
    try:
        from core.handlers.language import build_language_inline_kb
        await message.answer(
            "🌐 <b>Выбор языка</b>\n\nВыберите язык интерфейса:",
            reply_markup=build_language_inline_kb(),
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Error in admin_language_handler: {str(e)}", exc_info=True)
        await message.answer(
            "❌ Не удалось загрузить выбор языка. Попробуйте позже.",
            reply_markup=get_admin_keyboard()
        )

# Simple in-memory rate limit for search (per admin)
_search_last_at: dict[int, float] = {}
import time


@router.message(F.text == "📋 Модерация")
async def handle_moderation(message: Message, state: FSMContext):
    """Handle moderation queue."""
    try:
        # Проверяем права доступа
        from core.security.roles import get_user_role
        user_role = await get_user_role(message.from_user.id)
        role_name = getattr(user_role, "name", str(user_role)).lower()
        
        if role_name not in ("admin", "super_admin"):
            await message.answer("⛔ Недостаточно прав. Только администраторы могут просматривать модерацию.")
            return
        
        # Получаем партнеров на модерации
        try:
            import asyncpg
            from core.settings import settings
            
            conn = await asyncpg.connect(settings.database.url)
            try:
                # Партнеры на модерации
                pending_partners = await conn.fetch("""
                    SELECT id, title, contact_name, contact_phone, contact_email, created_at, status
                    FROM partners 
                    WHERE status = 'pending' 
                    ORDER BY created_at ASC 
                    LIMIT 10
                """)
                
                # Заведения на модерации
                pending_places = await conn.fetch("""
                    SELECT pp.id, pp.title, pp.address, pp.status, p.title as partner_name, pp.created_at
                    FROM partner_places pp
                    JOIN partners p ON pp.partner_id = p.id
                    WHERE pp.status = 'pending' 
                    ORDER BY pp.created_at ASC 
                    LIMIT 10
                """)
            finally:
                await conn.close()
                
        except Exception as e:
            logger.error(f"Error getting moderation data: {e}")
            pending_partners = []
            pending_places = []
        
        text = "📋 <b>Очередь модерации</b>\n\n"
        
        # Партнеры на модерации
        if pending_partners:
            text += f"🤝 <b>Партнеры на модерации ({len(pending_partners)}):</b>\n"
            for partner in pending_partners[:5]:  # Показываем только первые 5
                text += f"• <b>{partner['title']}</b>\n"
                text += f"  👤 {partner['contact_name']}\n"
                text += f"  📞 {partner['contact_phone']}\n"
                text += f"  📅 {str(partner['created_at'])[:10]}\n\n"
        else:
            text += "🤝 <b>Партнеры на модерации:</b> Нет заявок\n\n"
        
        # Заведения на модерации
        if pending_places:
            text += f"🏪 <b>Заведения на модерации ({len(pending_places)}):</b>\n"
            for place in pending_places[:5]:  # Показываем только первые 5
                text += f"• <b>{place['title']}</b>\n"
                text += f"  🏢 {place['partner_name']}\n"
                text += f"  📍 {place['address'] or 'Адрес не указан'}\n"
                text += f"  📅 {str(place['created_at'])[:10]}\n\n"
        else:
            text += "🏪 <b>Заведения на модерации:</b> Нет заявок\n\n"
        
        # Статистика
        total_pending = len(pending_partners) + len(pending_places)
        text += f"📊 <b>Общая статистика:</b>\n"
        text += f"• Всего на модерации: {total_pending}\n"
        text += f"• Партнеры: {len(pending_partners)}\n"
        text += f"• Заведения: {len(pending_places)}\n\n"
        
        if total_pending > 0:
            text += "💡 <b>Доступные действия:</b>\n"
            text += "• Одобрить заявку\n"
            text += "• Отклонить заявку\n"
            text += "• Запросить дополнительную информацию\n\n"
            text += "🚧 <i>Функции одобрения/отклонения будут реализованы в следующих обновлениях.</i>"
        else:
            text += "✅ Все заявки обработаны!"
        
        await message.answer(text, parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"Error in handle_moderation: {str(e)}", exc_info=True)
        await message.answer("❌ Ошибка при загрузке очереди модерации.")


@router.message(F.text == "👥 Админы")
async def handle_admins_management(message: Message, state: FSMContext):
    """Handle admins management (super admin only)."""
    try:
        # Check if user is super admin
        from core.security.roles import get_user_role
        user_role = await get_user_role(message.from_user.id)
        role_name = getattr(user_role, "name", str(user_role)).lower()
        
        if role_name != "super_admin":
            await message.answer("⛔ Недостаточно прав. Только супер-админ может управлять админами.")
            return
        
        # Получаем список всех администраторов
        try:
            import asyncpg
            from core.settings import settings
            
            conn = await asyncpg.connect(settings.database.url)
            try:
                admins = await conn.fetch("""
                    SELECT telegram_id, first_name, last_name, username, role, is_banned, created_at
                    FROM users 
                    WHERE role IN ('admin', 'super_admin')
                    ORDER BY created_at ASC
                """)
            finally:
                await conn.close()
                
        except Exception as e:
            logger.error(f"Error getting admins data: {e}")
            admins = []
        
        text = "👥 <b>Управление администраторами</b>\n\n"
        
        if admins:
            text += f"📋 <b>Список администраторов ({len(admins)}):</b>\n\n"
            
            for admin in admins:
                # Определяем статус
                status_emoji = "👑" if admin['role'] == "super_admin" else "👤"
                ban_status = "🚫 Заблокирован" if admin['is_banned'] else "✅ Активен"
                
                # Имя
                full_name = f"{admin['first_name'] or ''} {admin['last_name'] or ''}".strip()
                if not full_name:
                    full_name = admin['username'] or f"ID: {admin['telegram_id']}"
                
                text += f"{status_emoji} <b>{full_name}</b>\n"
                text += f"   🆔 ID: {admin['telegram_id']}\n"
                text += f"   🎭 Роль: {admin['role']}\n"
                text += f"   📊 Статус: {ban_status}\n"
                text += f"   📅 С: {str(admin['created_at'])[:10]}\n\n"
        else:
            text += "📋 <b>Администраторы не найдены</b>\n\n"
        
        # Статистика
        super_admins_count = len([a for a in admins if a['role'] == 'super_admin'])
        regular_admins_count = len([a for a in admins if a['role'] == 'admin'])
        banned_count = len([a for a in admins if a['is_banned']])
        
        text += f"📊 <b>Статистика:</b>\n"
        text += f"• Супер-админы: {super_admins_count}\n"
        text += f"• Обычные админы: {regular_admins_count}\n"
        text += f"• Заблокированные: {banned_count}\n\n"
        
        text += "💡 <b>Доступные действия:</b>\n"
        text += "• ➕ Добавить нового админа\n"
        text += "• 🗑️ Удалить админа\n"
        text += "• 🚫 Заблокировать админа\n"
        text += "• ✅ Разблокировать админа\n"
        text += "• 📋 Просмотр логов действий\n\n"
        text += "🚧 <i>Функции управления админами будут реализованы в следующих обновлениях.</i>"
        
        await message.answer(text, parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"Error in handle_admins_management: {str(e)}", exc_info=True)
        await message.answer("❌ Ошибка при загрузке управления админами.")


@router.message(F.text == "🔍 Поиск")
async def handle_search(message: Message, state: FSMContext):
    """Handle search functionality."""
    try:
        await message.answer(
            "🔍 <b>Поиск</b>\n\n"
            "Доступные типы поиска:\n\n"
            "• 👥 Поиск пользователей\n"
            "• 🤝 Поиск партнёров\n"
            "• 🧾 Поиск карточек\n"
            "• 📊 Поиск по статистике\n\n"
            "🚧 <i>Функция поиска будет реализована в следующих обновлениях.</i>",
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Error in handle_search: {str(e)}", exc_info=True)
        await message.answer("❌ Ошибка при загрузке поиска.")


@router.message(F.text == "📊 Статистика")
async def handle_statistics(message: Message, state: FSMContext):
    """Handle statistics."""
    try:
        await message.answer(
            "📊 <b>Статистика</b>\n\n"
            "Доступная статистика:\n\n"
            "• 👥 Количество пользователей\n"
            "• 🤝 Количество партнёров\n"
            "• 🧾 Количество карточек\n"
            "• 📈 Активность пользователей\n"
            "• 💰 Финансовая статистика\n\n"
            "🚧 <i>Функция статистики будет реализована в следующих обновлениях.</i>",
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Error in handle_statistics: {str(e)}", exc_info=True)
        await message.answer("❌ Ошибка при загрузке статистики.")


@router.message(F.text == "👥 Пользователи")
async def handle_users_management(message: Message, state: FSMContext):
    """Handle users management."""
    try:
        await message.answer(
            "👥 <b>Управление пользователями</b>\n\n"
            "Доступные действия:\n\n"
            "• 🔍 Поиск пользователя\n"
            "• 👤 Просмотр профиля\n"
            "• 🚫 Заблокировать пользователя\n"
            "• ✅ Разблокировать пользователя\n"
            "• 📊 Статистика пользователя\n\n"
            "🚧 <i>Функция управления пользователями будет реализована в следующих обновлениях.</i>",
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Error in handle_users_management: {str(e)}", exc_info=True)
        await message.answer("❌ Ошибка при загрузке управления пользователями.")


@router.message(F.text == "🤝 Партнёры")
async def handle_partners_management(message: Message, state: FSMContext):
    """Быстрый список партнёров (минимальный вывод вместо пустого сообщения)."""
    try:
        from core.database.db_v2 import db_v2
        with db_v2.get_connection() as conn:
            rows = conn.execute(
                "SELECT id, tg_user_id, name FROM partners_v2 ORDER BY id DESC LIMIT 10"
            ).fetchall()
        if not rows:
            await message.answer("🤝 Партнёров пока нет.")
            return
        lines = ["🤝 <b>Последние партнёры</b>\n"]
        for r in rows:
            pid = r[0]
            uid = r[1]
            pname = r[2] or "(без имени)"
            lines.append(f"#{pid} — {pname} (tg:{uid})")
        await message.answer("\n".join(lines), parse_mode='HTML')
    except Exception as e:
        logger.error(f"Error in handle_partners_management: {str(e)}", exc_info=True)
        await message.answer("❌ Ошибка при загрузке партнёров.")


@router.message(F.text == "🧾 Карты")
async def handle_cards_management(message: Message, state: FSMContext):
    """Handle cards management."""
    try:
        await message.answer(
            "🧾 <b>Управление картами</b>\n\n"
            "Доступные действия:\n\n"
            "• 🧾 Выпустить новые карты\n"
            "• 🔍 Поиск карты\n"
            "• 📋 Список всех карт\n"
            "• 🔗 Привязать карту\n"
            "• 🔓 Развязать карту\n"
            "• 📊 Статистика карт\n\n"
            "🚧 <i>Функция управления картами будет реализована в следующих обновлениях.</i>",
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Error in handle_cards_management: {str(e)}", exc_info=True)
        await message.answer("❌ Ошибка при загрузке управления картами.")


@router.message(F.text == "🗑️ Удаление")
async def handle_deletion(message: Message, state: FSMContext):
    """Handle deletion operations (super admin only)."""
    try:
        # Check if user is super admin
        from core.security.roles import get_user_role
        user_role = await get_user_role(message.from_user.id)
        role_name = getattr(user_role, "name", str(user_role)).lower()
        
        if role_name != "super_admin":
            await message.answer("⛔ Недостаточно прав. Только супер-админ может выполнять операции удаления.")
            return
        
        await message.answer(
            "🗑️ <b>Операции удаления</b>\n\n"
            "⚠️ <b>ВНИМАНИЕ!</b> Эти операции необратимы!\n\n"
            "Доступные действия:\n\n"
            "• 🗑️ Удалить карточку\n"
            "• 🗑️ Удалить пользователя\n"
            "• 🗑️ Удалить партнёра\n"
            "• 🗑️ Удалить все карточки партнёра\n"
            "• 🗑️ Массовое удаление\n\n"
            "🚧 <i>Функция удаления будет реализована в следующих обновлениях.</i>",
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Error in handle_deletion: {str(e)}", exc_info=True)
        await message.answer("❌ Ошибка при загрузке операций удаления.")


@router.message(F.text.startswith("📊 Дашборд:"))
async def handle_dashboard(message: Message, state: FSMContext):
    """Handle dashboard button for super admin."""
    try:
        # Check if user is super admin
        from core.security.roles import get_user_role
        user_role = await get_user_role(message.from_user.id)
        role_name = getattr(user_role, "name", str(user_role)).lower()
        
        if role_name != "super_admin":
            await message.answer("⛔ Недостаточно прав. Только супер-админ может просматривать дашборд.")
            return
        
        # Получаем реальные данные из базы
        try:
            import asyncpg
            from core.settings import settings
            
            # Подключаемся к PostgreSQL
            conn = await asyncpg.connect(settings.database.url)
            try:
                # Партнеры на модерации
                partners_pending = await conn.fetchval("SELECT COUNT(*) FROM partners WHERE status = 'pending'")
                
                # Заведения на модерации
                places_pending = await conn.fetchval("SELECT COUNT(*) FROM partner_places WHERE status = 'pending'")
                
                # Непрочитанные уведомления
                notifications_count = await conn.fetchval("SELECT COUNT(*) FROM user_notifications WHERE is_read = false")
                
                # Общее количество пользователей
                total_users = await conn.fetchval("SELECT COUNT(*) FROM users WHERE role = 'user'")
                
                # Активные партнеры
                active_partners = await conn.fetchval("SELECT COUNT(*) FROM partners WHERE status = 'approved'")
                
            finally:
                await conn.close()
                
        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")
            # Fallback значения
            partners_pending = 0
            places_pending = 0
            notifications_count = 0
            total_users = 0
            active_partners = 0
        
        moderation_count = partners_pending + places_pending
        system_status = "OK"  # TODO: Проверить статус системы
        
        await message.answer(
            f"📊 <b>Системный дашборд</b>\n\n"
            f"📋 <b>Модерация:</b> {moderation_count} карточек в очереди\n"
            f"   • Партнеры: {partners_pending}\n"
            f"   • Заведения: {places_pending}\n"
            f"🔔 <b>Уведомления:</b> {notifications_count} непрочитанных\n"
            f"👥 <b>Пользователи:</b> {total_users} зарегистрированных\n"
            f"🤝 <b>Партнеры:</b> {active_partners} активных\n"
            f"⚙️ <b>Система:</b> {system_status}\n\n"
            f"💡 <b>Быстрые действия:</b>\n"
            f"• Нажмите '📋 Модерация' для просмотра очереди\n"
            f"• Нажмите '👥 Админы' для управления администраторами\n"
            f"• Нажмите '📊 Статистика' для детальной аналитики\n\n"
            f"🚧 <i>Дашборд обновляется в реальном времени.</i>",
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Error in handle_dashboard: {str(e)}", exc_info=True)
        await message.answer("❌ Ошибка при загрузке дашборда.")

@router.message(F.text == "📧 Рассылка")
async def handle_broadcast(message: Message, state: FSMContext):
    """Handle broadcast functionality for admins."""
    try:
        # Check if user is admin or super admin
        from core.security.roles import get_user_role
        user_role = await get_user_role(message.from_user.id)
        role_name = getattr(user_role, "name", str(user_role)).lower()
        
        if role_name not in ("admin", "super_admin"):
            await message.answer("⛔ Недостаточно прав. Только администраторы могут делать рассылки.")
            return
        
        # Запускаем FSM для создания рассылки
        from core.fsm.broadcast import start_broadcast
        await start_broadcast(message, state)
    except Exception as e:
        logger.error(f"Error in handle_broadcast: {str(e)}", exc_info=True)
        await message.answer("❌ Ошибка при загрузке системы рассылок.")

@router.message(F.text == "⚙️ Настройки лояльности")
async def handle_loyalty_settings(message: Message, state: FSMContext):
    """Handle loyalty settings management for admins."""
    try:
        # Check if user is admin or super admin
        from core.security.roles import get_user_role
        user_role = await get_user_role(message.from_user.id)
        role_name = getattr(user_role, "name", str(user_role)).lower()
        
        if role_name not in ("admin", "super_admin"):
            await message.answer("⛔ Недостаточно прав. Только администраторы могут управлять настройками лояльности.")
            return
        
        # Получаем текущие настройки
        from core.database.db_v2 import get_connection
        
        with get_connection() as conn:
            cursor = conn.execute("""
                SELECT redeem_rate, max_accrual_percent, min_purchase_for_points, max_discount_percent
                FROM platform_loyalty_config 
                ORDER BY id DESC LIMIT 1
            """)
            config = cursor.fetchone()
            
            if config:
                redeem_rate, max_accrual_percent, min_purchase_for_points, max_discount_percent = config
            else:
                redeem_rate = 5000.0
                max_accrual_percent = 20.0
                min_purchase_for_points = 10000
                max_discount_percent = 40.0
        
        # Получаем границу закрытия чека баллами
        cursor = conn.execute("""
            SELECT max_percent_per_bill FROM platform_loyalty_config 
            ORDER BY id DESC LIMIT 1
        """)
        max_percent_per_bill = cursor.fetchone()
        max_percent_per_bill = max_percent_per_bill[0] if max_percent_per_bill else 50.0
        
        await message.answer(
            f"⚙️ <b>Настройки системы лояльности</b>\n\n"
            f"💰 <b>Текущие параметры:</b>\n"
            f"• Курс обмена: 1 балл = {redeem_rate:,.0f} VND\n"
            f"• Максимальное начисление: {max_accrual_percent}%\n"
            f"• Минимальная покупка для начисления: {min_purchase_for_points:,.0f} VND\n"
            f"• Максимальная скидка за баллы: {max_discount_percent}%\n"
            f"• 🎯 Граница закрытия чека баллами: {max_percent_per_bill}%\n\n"
            f"🔧 <b>Доступные изменения:</b>\n"
            f"• Изменить курс обмена баллов\n"
            f"• Настроить минимальную сумму покупки\n"
            f"• Установить максимальный процент скидки\n"
            f"• 🎯 Изменить границу закрытия чека баллами\n\n"
            f"💡 <b>Примеры:</b>\n"
            f"• При курсе 5000 VND: 100 баллов = 500,000 VND скидки\n"
            f"• При минимуме 10,000 VND: покупки меньше не дают баллы\n"
            f"• При максимуме 40%: скидка за баллы не может превышать 40% от чека\n"
            f"• При границе 50%: баллы могут закрыть до 50% от суммы чека\n\n"
            f"✏️ <b>Для редактирования настроек отправьте любое сообщение.</b>",
            parse_mode='HTML'
        )
        
        # Запускаем FSM для редактирования настроек
        from core.fsm.loyalty_settings import start_loyalty_settings_edit
        await start_loyalty_settings_edit(message, state)
    except Exception as e:
        logger.error(f"Error in handle_loyalty_settings: {str(e)}", exc_info=True)
        await message.answer("❌ Ошибка при загрузке настроек лояльности.")


@router.message(F.text == "◀️ Назад")
async def handle_back_to_main(message: Message, state: FSMContext):
    """Handle back to main menu."""
    try:
        from core.keyboards.reply_v2 import get_main_menu_reply_admin
        from core.security.roles import get_user_role
        
        # Check user role to show appropriate menu
        user_role = await get_user_role(message.from_user.id)
        role_name = getattr(user_role, "name", str(user_role)).lower()
        is_superadmin = role_name == "super_admin"
        
        keyboard = get_main_menu_reply_admin(is_superadmin=is_superadmin)
        
        await message.answer(
            "🏠 Главное меню",
            reply_markup=keyboard
        )
    except Exception as e:
        logger.error(f"Error in handle_back_to_main: {str(e)}", exc_info=True)
        await message.answer("❌ Ошибка при возврате в главное меню.")

# Simple anti-spam for superadmin prompt flows
_su_last_at: dict[int, float] = {}

def _su_allowed(user_id: int, window: float = 2.5) -> bool:
    now = time.time()
    last = _su_last_at.get(user_id, 0.0)
    if now - last < window:
        return False
    _su_last_at[user_id] = now
    return True

def _search_allowed(user_id: int, window: float = 2.5) -> bool:
    now = time.time()
    last = _search_last_at.get(user_id, 0.0)
    if now - last < window:
        return False
    _search_last_at[user_id] = now
    return True

def _search_keyboard() -> 'InlineKeyboardMarkup':
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏳ В очереди", callback_data="adm:search:status:pending"),
         InlineKeyboardButton(text="✅ Опубликованы", callback_data="adm:search:status:published")],
        [InlineKeyboardButton(text="❌ Отклонены", callback_data="adm:search:status:rejected"),
         InlineKeyboardButton(text="🆕 Последние 20", callback_data="adm:search:recent")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="adm:queue")],
    ])

def _queue_nav_keyboard(page: int, has_prev: bool, has_next: bool) -> 'InlineKeyboardMarkup':
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    row = []
    if has_prev:
        row.append(InlineKeyboardButton(text="⬅️", callback_data=f"adm:q:page:{page-1}"))
    row.append(InlineKeyboardButton(text=f"{page+1}", callback_data="noop"))
    if has_next:
        row.append(InlineKeyboardButton(text="➡️", callback_data=f"adm:q:page:{page+1}"))
    return InlineKeyboardMarkup(inline_keyboard=[row, [InlineKeyboardButton(text="🔎 Поиск", callback_data="adm:search")]])

def _build_queue_list_buttons(cards: list[dict], page: int) -> 'InlineKeyboardMarkup':
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    rows: list[list[InlineKeyboardButton]] = []
    for c in cards:
        cid = int(c.get('id'))
        title = (c.get('title') or '(без названия)')
        rows.append([InlineKeyboardButton(text=f"🔎 #{cid} · {title[:40]}", callback_data=f"adm:q:view:{cid}:{page}")])
    if not rows:
        rows = [[]]
    rows.append([InlineKeyboardButton(text="↩️ К меню", callback_data="adm:queue")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def _build_queue_list_text(cards: list[dict], page: int, page_size: int, total: int) -> str:
    start = page * page_size + 1
    end = min((page + 1) * page_size, total)
    lines = [f"🗂️ Очередь модерации: {start}–{end} из {total}"]
    for c in cards:
        lines.append(f"• #{c.get('id')} — {(c.get('title') or '(без названия)')} — {c.get('category_name') or ''}")
    return "\n".join(lines)

async def _render_queue_page(message_or_cbmsg, admin_id: int, page: int, *, edit: bool = False):
    PAGE_SIZE = 5
    logger.info("admin.queue_render: admin=%s page=%s", admin_id, page)
    with db_v2.get_connection() as conn:
        total = int(conn.execute("SELECT COUNT(*) FROM cards_v2 WHERE status = 'pending' ").fetchone()[0])
        offset = max(page, 0) * PAGE_SIZE
        cur = conn.execute(
            """
            SELECT c.id, c.title, cat.name as category_name
            FROM cards_v2 c
            JOIN categories_v2 cat ON c.category_id = cat.id
            WHERE c.status = 'pending'
            ORDER BY c.created_at ASC
            LIMIT ? OFFSET ?
            """,
            (PAGE_SIZE, offset),
        )
        cards = [dict(r) for r in cur.fetchall()]
    has_prev = page > 0
    has_next = (page + 1) * PAGE_SIZE < total
    if total == 0:
        text = "✅ Нет карточек, ожидающих модерации."
        kb = _queue_nav_keyboard(page=0, has_prev=False, has_next=False)
        if edit:
            try:
                await message_or_cbmsg.edit_text(text, reply_markup=kb)
            except Exception:
                await message_or_cbmsg.answer(text, reply_markup=kb)
        else:
            await message_or_cbmsg.answer(text, reply_markup=kb)
        return
    if not cards:
        text = "📭 На этой странице карточек нет."
        kb = _queue_nav_keyboard(page=page, has_prev=has_prev, has_next=has_next)
        if edit:
            try:
                await message_or_cbmsg.edit_text(text, reply_markup=kb)
            except Exception:
                await message_or_cbmsg.answer(text, reply_markup=kb)
        else:
            await message_or_cbmsg.answer(text, reply_markup=kb)
        return
    text = _build_queue_list_text(cards, page=page, page_size=PAGE_SIZE, total=total)
    try:
        if edit:
            await message_or_cbmsg.edit_text(text, reply_markup=_build_queue_list_buttons(cards, page=page))
        else:
            await message_or_cbmsg.answer(text, reply_markup=_build_queue_list_buttons(cards, page=page))
    except Exception:
        await message_or_cbmsg.answer(text, reply_markup=_build_queue_list_buttons(cards, page=page))
    # Навигация отдельным сообщением
    await message_or_cbmsg.answer("Навигация:", reply_markup=_queue_nav_keyboard(page=page, has_prev=has_prev, has_next=has_next))

def _build_card_view_text(card: dict) -> str:
    lines = [f"🔍 Карточка #{card['id']}"]
    lines.append(f"📝 {card.get('title') or '(без названия)'}")
    if card.get('category_name'):
        lines.append(f"📂 {card['category_name']}")
    if card.get('partner_name'):
        lines.append(f"👤 {card['partner_name']}")
    if card.get('description'):
        lines.append(f"📄 {card['description']}")
    if card.get('contact'):
        lines.append(f"📞 {card['contact']}")
    if card.get('address'):
        lines.append(f"📍 {card['address']}")
    if card.get('discount_text'):
        lines.append(f"🎫 {card['discount_text']}")
    return "\n".join(lines)

def _build_card_view_kb(card_id: int, page: int):
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    # Набор для модерации: [✅ Одобрить] [❌ Отклонить] [✏️ На доработку] / [📜 История изменений] [📷 Медиа] [ℹ️ Подробнее]
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Одобрить", callback_data=f"adm:q:approve:{card_id}:{page}"),
         InlineKeyboardButton(text="❌ Отклонить", callback_data=f"adm:q:reject:{card_id}:{page}"),
         InlineKeyboardButton(text="✏️ На доработку", callback_data=f"adm:q:revise:{card_id}:{page}")],
        [InlineKeyboardButton(text="📜 История изменений", callback_data=f"adm:q:hist:{card_id}:{page}"),
         InlineKeyboardButton(text="📷 Медиа", callback_data=f"gallery:{card_id}"),
         InlineKeyboardButton(text="ℹ️ Подробнее", callback_data=f"adm:q:view:{card_id}:{page}")],
    ])

def _format_cards_rows(rows) -> str:
    lines = ["🔎 Результаты поиска (до 20):"]
    if not rows:
        lines.append("(пусто)")
        return "\n".join(lines)
    for r in rows:
        title = r.get('title') or '(без названия)'
        status = r.get('status') or ''
        cid = r.get('id')
        cat = r.get('category_name') or ''
        lines.append(f"• #{cid} — {title} — {status} — {cat}")
    return "\n".join(lines)


@router.message(Command("admin"))
async def open_admin_cabinet(message: Message, bot: Bot, state: FSMContext):
    """
    Открывает админ-панель, если включена функция модерации и пользователь является администратором.
    
    Args:
        message: Входящее сообщение
        bot: Экземпляр бота
        state: Контекст состояния FSM
    """
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"open_admin_cabinet called by user {message.from_user.id}")
        logger.info(f"Moderation feature enabled: {settings.features.moderation}")
        
        if not settings.features.moderation:
            logger.warning("Moderation feature is disabled")
            await message.answer("🚧 Модуль модерации отключён.")
            return
            
        is_admin = await admins_service.is_admin(message.from_user.id)
        logger.info(f"User {message.from_user.id} is admin: {is_admin}")
        
        if not is_admin:
            logger.warning(f"Access denied for user {message.from_user.id}")
            await message.answer("❌ Доступ запрещён.")
            return
            
        lang = await profile_service.get_lang(message.from_user.id)
        logger.info(f"User language: {lang}")
        
        # Top-level: use Reply keyboard (superadmin has crown in main menu; here use dedicated keyboard)
        is_superadmin = (int(message.from_user.id) == int(settings.bots.admin_id))
        logger.info(f"Is superadmin: {is_superadmin}, admin_id: {settings.bots.admin_id}")
        
        kb = get_superadmin_keyboard(lang) if is_superadmin else get_admin_keyboard(lang)
        
        # Debug: Log the admin_cabinet_title text
        admin_title = get_text('admin_cabinet_title', lang)
        logger.info(f"Admin title text: {admin_title}")
        
        response_text = f"{admin_title}\n\nВыберите раздел:"
        logger.info(f"Full response text: {response_text}")
        
        logger.info(f"Sending response with keyboard: {kb}")
        await message.answer(
            response_text,
            reply_markup=kb,
        )
        logger.info("Response sent successfully")
        
    except Exception as e:
        logger.error(f"Error in open_admin_cabinet: {e}", exc_info=True)
        # Re-raise to see the full traceback in test output
        raise
        await message.answer("❌ Произошла ошибка при открытии админ-панели. Пожалуйста, попробуйте позже.")


@router.message(Command("test_odoo"))
async def test_odoo_command(message: Message):
    """Команда для тестирования Odoo подключения (только для админов)"""
    
    # Проверить права админа
    is_admin = await admins_service.is_admin(message.from_user.id)
    if not is_admin:
        await message.answer("❌ Команда только для администраторов")
        return
    
    try:
        await message.answer("🔄 Тестирую подключение к Odoo...")
        
        from core.services.odoo_api import OdooAPI
        odoo = OdooAPI()
        
        if odoo.connect():
            # Попробовать выполнить простой запрос
            try:
                databases = odoo.models.execute_kw(
                    odoo.db, odoo.uid, odoo.password,
                    'res.users', 'search_read',
                    [[['id', '=', odoo.uid]]],
                    {'fields': ['name', 'login'], 'limit': 1}
                )
                
                user_info = databases[0] if databases else {}
                
                result_text = (
                    "✅ Odoo подключение успешно!\n\n"
                    f"🔗 URL: {odoo.url}\n"
                    f"🗄️ Database: {odoo.db}\n"
                    f"👤 User: {user_info.get('name', 'Unknown')} ({user_info.get('login', 'N/A')})\n"
                    f"🆔 UID: {odoo.uid}"
                )
                
            except Exception as e:
                result_text = (
                    "⚠️ Подключение есть, но ошибка запроса:\n"
                    f"Ошибка: {str(e)}"
                )
        else:
            result_text = "❌ Не удалось подключиться к Odoo"
        
        await message.answer(result_text)
        
    except Exception as e:
        await message.answer(f"❌ Критическая ошибка: {str(e)}")


# --- Inline callbacks ---
@router.message(F.text == "👑 Админ кабинет")
async def open_admin_cabinet_by_button(message: Message, bot: Bot, state: FSMContext):
    """
    Открывает админ-панель при нажатии на кнопку в основном меню.
    
    Args:
        message: Входящее сообщение
        bot: Экземпляр бота
        state: Контекст состояния FSM
    """
    try:
        if not settings.features.moderation:
            await message.answer("🚧 Модуль модерации отключён.")
            return
            
        if not await admins_service.is_admin(message.from_user.id):
            await message.answer("❌ Доступ запрещён.")
            return
            
        lang = await profile_service.get_lang(message.from_user.id)
        kb = get_superadmin_keyboard(lang) if (message.from_user.id == settings.bots.admin_id) else get_admin_keyboard(lang)
        await message.answer(
            f"{get_text('admin_cabinet_title', lang)}\n\nВыберите раздел:",
            reply_markup=kb,
        )
    except Exception as e:
        logger.error(f"Error in open_admin_cabinet_by_button: {e}", exc_info=True)
        await message.answer("❌ Произошла ошибка при открытии админ-панели. Пожалуйста, попробуйте позже.")

@router.callback_query(F.data == "adm:back")
async def admin_back(callback: CallbackQuery):
    """Обработчик кнопки 'Назад' в админ-меню."""
    try:
        lang = await profile_service.get_lang(callback.from_user.id)
        # Роль‑зависимый возврат: админ/суперадмин → admin меню, не юзерское
        is_superadmin = (int(callback.from_user.id) == int(settings.bots.admin_id))
        kb = get_main_menu_reply_admin(lang, is_superadmin)
        await callback.message.answer(get_text('admin_cabinet_title', lang), reply_markup=kb)
        await callback.answer()
    except Exception as e:
        logger.error(f"Error in admin_back: {e}", exc_info=True)
        await callback.answer("❌ Произошла ошибка. Пожалуйста, попробуйте ещё раз.")

# --- Reply-based admin menu entries ---
@router.message(F.text.in_([t.get('admin_menu_queue', '') for t in translations.values()]))
async def admin_menu_queue_entry(message: Message, bot: Bot, state: FSMContext) -> None:
    """
    Обработчик кнопки очереди на модерацию в админ-меню.
    
    Args:
        message: Входящее сообщение
        bot: Экземпляр бота
        state: Контекст состояния FSM
    """
    try:
        if not settings.features.moderation:
            await message.answer("🚧 Модуль модерации отключён.")
            return
            
        if not await admins_service.is_admin(message.from_user.id):
            await message.answer("❌ Доступ запрещён.")
            return
            
        await _render_queue_page(message, message.from_user.id, 0)
    except Exception as e:
        logger.error(f"Error in admin_menu_queue_entry: {e}", exc_info=True)
        await message.answer("❌ Произошла ошибка при загрузке очереди. Пожалуйста, попробуйте позже.")

@router.message(F.text.in_([t.get('admin_menu_reports', '') for t in translations.values()]))
async def admin_menu_reports_entry(message: Message, bot: Bot, state: FSMContext) -> None:
    """
    Обработчик кнопки отчётов в админ-меню.
    
    Args:
        message: Входящее сообщение
        bot: Экземпляр бота
        state: Контекст состояния FSM
    """
    try:
        if not settings.features.moderation:
            await message.answer("🚧 Модуль модерации отключён.")
            return
            
        if not await admins_service.is_admin(message.from_user.id):
            await message.answer("❌ Доступ запрещён.")
            return
            
        lang = await profile_service.get_lang(message.from_user.id)
        with db_v2.get_connection() as conn:
            cur = conn.execute("""
                SELECT status, COUNT(*) as cnt
                FROM cards_v2
                GROUP BY status
            """)
            by_status = {row[0] or 'unknown': int(row[1]) for row in cur.fetchall()}

            cur = conn.execute("SELECT COUNT(*) FROM cards_v2")
            total_cards = int(cur.fetchone()[0])

            cur = conn.execute("SELECT COUNT(*) FROM partners_v2")
            total_partners = int(cur.fetchone()[0])

            try:
                cur = conn.execute(
                    """
                    SELECT action, COUNT(*) as cnt
                    FROM moderation_log
                    WHERE created_at >= datetime('now','-7 days')
                    GROUP BY action
                    """
                )
                recent_actions = {row[0]: int(row[1]) for row in cur.fetchall()}
            except Exception:
                recent_actions = {}

        lines = [
            "📊 Отчёты (сводка)",
            f"Всего карточек: {total_cards}",
            f"Всего партнёров: {total_partners}",
            "",
            "По статусам:",
            f"⏳ pending: {by_status.get('pending', 0)}",
            f"✅ published: {by_status.get('published', 0)}",
            f"❌ rejected: {by_status.get('rejected', 0)}",
            f"🗂️ archived: {by_status.get('archived', 0)}",
            f"📝 draft: {by_status.get('draft', 0)}",
        ]
        if recent_actions:
            lines += [
                "",
                "За 7 дней:",
                *[f"• {k}: {v}" for k, v in recent_actions.items()],
            ]
        text = "\n".join(lines)
        # Keep user in reply-based admin menu
        kb = get_superadmin_keyboard(lang) if (message.from_user.id == settings.bots.admin_id) else get_admin_keyboard(lang)
        await message.answer(text, reply_markup=kb)
    except Exception as e:
        logger.error(f"Error in admin_menu_reports_entry: {e}", exc_info=True)
        await message.answer("❌ Произошла ошибка при загрузке отчёта. Пожалуйста, попробуйте позже.")

@router.message(F.text.in_(
    [
        t.get('back_admin', '') for t in translations.values() if t.get('back_admin')
    ] + [
        t.get('back_admin_verbose', '') for t in translations.values() if t.get('back_admin_verbose')
    ] + [
        t.get('back_superadmin_verbose', '') for t in translations.values() if t.get('back_superadmin_verbose')
    ]
))
async def admin_menu_back_to_main(message: Message, bot: Bot, state: FSMContext) -> None:
    """
    Возвращает пользователя в главное меню из админ-панели.
    
    Args:
        message: Входящее сообщение
        bot: Экземпляр бота
        state: Контекст состояния FSM
    """
    try:
        lang = await profile_service.get_lang(message.from_user.id)
        # Роль‑зависимый возврат: суперадмин/админ → админское главное меню
        from core.settings import settings
        from core.keyboards.reply_v2 import get_main_menu_reply_admin, get_main_menu_reply
        is_superadmin = int(message.from_user.id) == int(settings.bots.admin_id)
        if is_superadmin:
            kb = get_main_menu_reply_admin(lang, True)
        else:
            from core.services.admins import admins_service
            is_admin = await admins_service.is_admin(message.from_user.id)
            kb = get_main_menu_reply_admin(lang, False) if is_admin else get_main_menu_reply(lang)
        await message.answer(get_text('admin_cabinet_title', lang), reply_markup=kb)
    except Exception as e:
        logger.error(f"Error in admin_menu_back_to_main: {e}", exc_info=True)
        await message.answer("❌ Произошла ошибка при возврате в главное меню. Пожалуйста, попробуйте ещё раз.")


@router.callback_query(F.data == "adm:su:del")
async def su_menu_delete(callback: CallbackQuery) -> None:
    """
    Обработчик кнопки удаления в меню суперадмина.
    
    Args:
        callback: Callback запрос
    """
    try:
        if not _is_super_admin(callback.from_user.id):
            await callback.answer("❌ Доступ запрещён")
            return
            
        lang = await profile_service.get_lang(callback.from_user.id)
        try:
            await callback.message.edit_text(
                "🗑 Удаление: выберите вариант", 
                reply_markup=get_superadmin_delete_inline(lang)
            )
        except Exception:
            await callback.message.answer(
                "🗑 Удаление: выберите вариант", 
                reply_markup=get_superadmin_delete_inline(lang)
            )
        await callback.answer()
    except Exception as e:
        logger.error(f"Error in su_menu_delete: {e}", exc_info=True)
        await callback.answer("❌ Произошла ошибка. Пожалуйста, попробуйте ещё раз.", show_alert=True)


@router.callback_query(F.data == "adm:queue")
async def admin_queue(callback: CallbackQuery) -> None:
    """
    Обработчик кнопки очереди на модерацию.
    
    Args:
        callback: Callback запрос
    """
    try:
        if not await admins_service.is_admin(callback.from_user.id):
            await callback.answer("❌ Доступ запрещён")
            return
            
        if not settings.features.moderation:
            await callback.answer("🚧 Модуль модерации отключён.")
            return
            
        await _render_queue_page(callback.message, callback.from_user.id, page=0, edit=True)
    except Exception as e:
        logger.error(f"Error in admin_queue: {e}", exc_info=True)
        await callback.answer("❌ Произошла ошибка при загрузке очереди. Пожалуйста, попробуйте позже.", show_alert=True)
    finally:
        with contextlib.suppress(Exception):
            await callback.answer()

@router.callback_query(F.data.startswith("adm:q:page:"))
async def admin_queue_page(callback: CallbackQuery) -> None:
    """
    Обработчик пагинации в очереди на модерацию.
    
    Args:
        callback: Callback запрос, содержащий номер страницы
    """
    try:
        if not await admins_service.is_admin(callback.from_user.id):
            await callback.answer("❌ Доступ запрещён")
            return
            
        if not settings.features.moderation:
            await callback.answer("🚧 Модуль модерации отключён.")
            return
            
        try:
            page = int(callback.data.split(":")[3])
            await _render_queue_page(callback.message, callback.from_user.id, page=page, edit=True)
        except (IndexError, ValueError) as e:
            logger.error(f"Invalid page number in callback data: {callback.data}")
            await callback.answer("❌ Неверный номер страницы", show_alert=True)
        except Exception as e:
            raise e
    except Exception as e:
        logger.error(f"Error in admin_queue_page: {e}", exc_info=True)
        await callback.answer("❌ Произошла ошибка при загрузке страницы. Пожалуйста, попробуйте ещё раз.", show_alert=True)

@router.callback_query(F.data.startswith("adm:q:view:"))
async def admin_queue_view(callback: CallbackQuery) -> None:
    """
    Просмотр деталей карточки в очереди модерации.
    
    Args:
        callback: Callback запрос, содержащий ID карточки и номер страницы
    """
    try:
        if not await admins_service.is_admin(callback.from_user.id):
            await callback.answer("❌ Доступ запрещён")
            return
            
        if not settings.features.moderation:
            await callback.answer("🚧 Модуль модерации отключён.")
            return
            
        try:
            parts = callback.data.split(":")
            if len(parts) < 5:
                raise ValueError("Неверный формат callback данных")
                
            card_id = int(parts[3])
            page = int(parts[4])
            
            card = db_v2.get_card_by_id(card_id)
            if not card:
                await callback.answer("❌ Карточка не найдена", show_alert=True)
                await _render_queue_page(callback.message, callback.from_user.id, page=page, edit=True)
                return
                
            text = _build_card_view_text(card)
            try:
                await callback.message.edit_text(
                    text, 
                    reply_markup=_build_card_view_kb(card_id, page)
                )
            except Exception as e:
                logger.warning(f"Failed to edit message, sending new one: {e}")
                await callback.message.answer(
                    text, 
                    reply_markup=_build_card_view_kb(card_id, page)
                )
            
            await callback.answer()
            
        except (IndexError, ValueError) as e:
            logger.error(f"Invalid callback data format: {callback.data}")
            await callback.answer("❌ Ошибка формата данных", show_alert=True)
            
    except Exception as e:
        logger.error(f"Error in admin_queue_approve: {e}", exc_info=True)
        await callback.answer(
            "❌ Произошла ошибка при одобрении карточки. Пожалуйста, попробуйте ещё раз.", 
            show_alert=True
        )


@router.callback_query(F.data.startswith("adm:q:approve:"))
async def admin_queue_approve(callback: CallbackQuery, bot: Bot) -> None:
    """Одобрение карточки: adm:q:approve:<card_id>:<page>."""
    try:
        if not await admins_service.is_admin(callback.from_user.id):
            await callback.answer("❌ Доступ запрещён")
            return
        parts = callback.data.split(":")
        if len(parts) < 5:
            await callback.answer("❌ Неверный запрос", show_alert=True)
            return
        card_id = int(parts[3]); page = int(parts[4])
        ok = db_v2.update_card_status(card_id, 'published')
        
        # Логировать действие модерации
        log_admin_action_direct(
            event=callback,
            action="card_approve",
            target=f"card_id:{card_id}",
            details={"card_id": card_id, "page": page},
            result="success" if ok else "error"
        )
        
        await callback.answer("✅ Одобрено" if ok else "⚠️ Не удалось")
        if ok:
            # Уведомим партнёра об одобрении (best-effort)
            try:
                await _notify_partner_about_approval(bot, card_id)
            except Exception:
                pass
            # Try update status in Odoo mirror card if present (best-effort)
            try:
                from core.services import odoo_api
                if odoo_api.is_configured:
                    card = db_v2.get_card_by_id(card_id)
                    ocid = int(card.get('odoo_card_id') or 0) if card else 0
                    if ocid:
                        await odoo_api.update_partner_card_status(card_id=ocid, status='published')
            except Exception:
                pass
        await _render_queue_page(callback.message, callback.from_user.id, page=page, edit=True)
    except Exception as e:
        logger.exception("admin_queue_approve failed: %s", e)
        await callback.answer("❌ Ошибка", show_alert=False)


@router.callback_query(F.data.startswith("adm:q:reject:"))
async def admin_queue_reject(callback: CallbackQuery) -> None:
    """Отклонение карточки: adm:q:reject:<card_id>:<page>."""
    try:
        if not await admins_service.is_admin(callback.from_user.id):
            await callback.answer("❌ Доступ запрещён")
            return
        parts = callback.data.split(":")
        if len(parts) < 5:
            await callback.answer("❌ Неверный запрос", show_alert=True)
            return
        card_id = int(parts[3]); page = int(parts[4])
        ok = db_v2.update_card_status(card_id, 'rejected')
        
        # Логировать действие модерации
        log_admin_action_direct(
            event=callback,
            action="card_reject",
            target=f"card_id:{card_id}",
            details={"card_id": card_id, "page": page},
            result="success" if ok else "error"
        )
        
        await callback.answer("🛑 Отклонено" if ok else "⚠️ Не удалось")
        if ok:
            # Best-effort sync to Odoo
            try:
                from core.services import odoo_api
                if odoo_api.is_configured:
                    card = db_v2.get_card_by_id(card_id)
                    ocid = int(card.get('odoo_card_id') or 0) if card else 0
                    if ocid:
                        await odoo_api.update_partner_card_status(card_id=ocid, status='rejected')
            except Exception:
                pass
        await _render_queue_page(callback.message, callback.from_user.id, page=page, edit=True)
    except Exception as e:
        logger.exception("admin_queue_reject failed: %s", e)
        await callback.answer("❌ Ошибка", show_alert=False)


@router.callback_query(F.data.startswith("adm:q:revise:"))
async def admin_queue_revise(callback: CallbackQuery) -> None:
    """На доработку: вернуть в pending и обновить очередь."""
    try:
        if not await admins_service.is_admin(callback.from_user.id):
            await callback.answer("❌ Доступ запрещён")
            return
        parts = callback.data.split(":")
        if len(parts) < 5:
            await callback.answer("❌ Неверный запрос", show_alert=True)
            return
        card_id = int(parts[3]); page = int(parts[4])
        ok = db_v2.update_card_status(card_id, 'pending')
        
        # Логировать действие модерации
        log_admin_action_direct(
            event=callback,
            action="card_revise",
            target=f"card_id:{card_id}",
            details={"card_id": card_id, "page": page},
            result="success" if ok else "error"
        )
        
        await callback.answer("✏️ На доработку" if ok else "⚠️ Не удалось")
        if ok:
            # Best-effort sync to Odoo back to 'pending'
            try:
                from core.services import odoo_api
                if odoo_api.is_configured:
                    card = db_v2.get_card_by_id(card_id)
                    ocid = int(card.get('odoo_card_id') or 0) if card else 0
                    if ocid:
                        await odoo_api.update_partner_card_status(card_id=ocid, status='pending')
            except Exception:
                pass
        await _render_queue_page(callback.message, callback.from_user.id, page=page, edit=True)
    except Exception as e:
        logger.exception("admin_queue_revise failed: %s", e)
        await callback.answer("❌ Ошибка", show_alert=False)


@router.callback_query(F.data.startswith("adm:q:hist:"))
async def admin_queue_history(callback: CallbackQuery) -> None:
    """История изменений карточки (заглушка)."""
    try:
        if not await admins_service.is_admin(callback.from_user.id):
            await callback.answer("❌ Доступ запрещён")
            return
        parts = callback.data.split(":")
        if len(parts) < 5:
            await callback.answer("❌ Неверный запрос", show_alert=True)
            return
        card_id = int(parts[3]); page = int(parts[4])
        await callback.message.answer(f"📜 История изменений карточки #{card_id}: пока пусто")
        await callback.answer()
    except Exception as e:
        logger.exception("admin_queue_history failed: %s", e)
        await callback.answer("❌ Ошибка", show_alert=False)


async def _notify_partner_about_approval(bot: Bot, card_id: int) -> None:
    """Отправляет уведомление партнёру об одобрении карточки."""
    try:
        with db_v2.get_connection() as conn:
            cur = conn.execute("""
                SELECT c.title, p.tg_user_id
                FROM cards_v2 c 
                JOIN partners_v2 p ON c.partner_id = p.id
                WHERE c.id = ?
            """, (card_id,))
            row = cur.fetchone()
            
            if row and row['tg_user_id'] and str(row['tg_user_id']).isdigit():
                try:
                    await bot.send_message(
                        int(row['tg_user_id']), 
                        f"✅ Ваша карточка одобрена!\n#{card_id} — {row['title']}"
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to send notification to partner {row['tg_user_id']} "
                        f"about approval of card {card_id}: {e}"
                    )
    except Exception as e:
        logger.error(f"Error in _notify_partner_about_approval for card {card_id}: {e}")

@router.callback_query(F.data.startswith("adm:q:del:confirm:"))
async def admin_queue_delete(callback: CallbackQuery) -> None:
    """
    Удаление карточки из очереди модерации после подтверждения.
    
    Args:
        callback: Callback запрос, содержащий ID карточки и номер страницы
    """
    try:
        if not await admins_service.is_admin(callback.from_user.id):
            await callback.answer("❌ Доступ запрещён")
            return
            
        if not settings.features.moderation:
            await callback.answer("🚧 Модуль модерации отключён.")
            return
            
        try:
            parts = callback.data.split(":")
            if len(parts) < 6:
                raise ValueError("Неверный формат callback данных")
                
            card_id = int(parts[4])
            page = int(parts[5])
            
            # Удаляем карточку
            ok = db_v2.delete_card(card_id)
            logger.info(
                "admin.delete: moderator=%s card=%s ok=%s", 
                callback.from_user.id, 
                card_id, 
                ok
            )
            
            # Возвращаемся к очереди
            await _render_queue_page(callback.message, callback.from_user.id, page=page, edit=True)
            await callback.answer("🗑 Карточка удалена", show_alert=False)
            
        except (IndexError, ValueError) as e:
            logger.error(f"Invalid callback data format: {callback.data}")
            await callback.answer("❌ Ошибка формата данных", show_alert=True)
            
    except Exception as e:
        logger.error(f"Error in admin_queue_delete: {e}", exc_info=True)
        await callback.answer(
            "❌ Произошла ошибка при удалении карточки. Пожалуйста, попробуйте ещё раз.", 
            show_alert=True
        )


@router.callback_query(F.data == "adm:search")
async def admin_search(callback: CallbackQuery) -> None:
    """
    Отображает меню поиска в админ-панели.
    
    Args:
        callback: Callback запрос
    """
    try:
        if not await admins_service.is_admin(callback.from_user.id):
            await callback.answer("❌ Доступ запрещён")
            return
            
        if not settings.features.moderation:
            await callback.answer("🚧 Модуль модерации отключён.")
            return
            
        lang = await profile_service.get_lang(callback.from_user.id)
        text = (
            f"{get_text('admin_cabinet_title', lang)}\n\n"
            f"{get_text('admin_hint_search', lang)}"
        )
        
        # Показываем клавиатуру с фильтрами поиска
        try:
            await callback.message.edit_text(
                text, 
                reply_markup=_search_keyboard()
            )
        except Exception as e:
            logger.warning(f"Failed to edit message, sending new one: {e}")
            await callback.message.answer(
                text, 
                reply_markup=_search_keyboard()
            )
            
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in admin_search: {e}", exc_info=True)
        await callback.answer(
            "❌ Произошла ошибка при загрузке поиска. Пожалуйста, попробуйте ещё раз.", 
            show_alert=True
        )


@router.callback_query(F.data.startswith("adm:search:status:"))
async def admin_search_by_status(callback: CallbackQuery) -> None:
    """
    Поиск карточек по статусу.
    
    Args:
        callback: Callback запрос, содержащий статус для поиска
    """
    try:
        if not await admins_service.is_admin(callback.from_user.id):
            await callback.answer("❌ Доступ запрещён")
            return
            
        if not settings.features.moderation:
            await callback.answer("🚧 Модуль модерации отключён.")
            return
            
        if not _search_allowed(callback.from_user.id):
            await callback.answer("⏳ Подождите немного перед следующим поиском…", show_alert=False)
            return
            
        try:
            status = callback.data.split(":")[-1]
            if not status:
                raise ValueError("Не указан статус для поиска")
                
            with db_v2.get_connection() as conn:
                cur = conn.execute(
                    """
                    SELECT c.id, c.title, c.status, cat.name as category_name
                    FROM cards_v2 c
                    JOIN categories_v2 cat ON c.category_id = cat.id
                    WHERE c.status = ?
                    ORDER BY c.updated_at DESC
                    LIMIT 20
                    """,
                    (status,)
                )
                rows = [dict(r) for r in cur.fetchall()]
                
            if not rows:
                text = f"🔍 Карточек со статусом '{status}' не найдено"
            else:
                text = _format_cards_rows(rows)
                
            try:
                await callback.message.edit_text(
                    text, 
                    reply_markup=_search_keyboard()
                )
            except Exception as e:
                logger.warning(f"Failed to edit message, sending new one: {e}")
                await callback.message.answer(
                    text, 
                    reply_markup=_search_keyboard()
                )
                
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Error in admin_search_by_status: {e}", exc_info=True)
            await callback.answer("❌ Ошибка при выполнении поиска", show_alert=True)
            
    except Exception as e:
        logger.error(f"Unexpected error in admin_search_by_status: {e}", exc_info=True)
        await callback.answer(
            "❌ Произошла непредвиденная ошибка. Пожалуйста, попробуйте ещё раз.", 
            show_alert=True
        )


@router.callback_query(F.data == "adm:search:recent")
async def admin_search_recent(callback: CallbackQuery) -> None:
    """
    Поиск недавно созданных карточек.
    
    Args:
        callback: Callback запрос
    """
    try:
        if not await admins_service.is_admin(callback.from_user.id):
            await callback.answer("❌ Доступ запрещён")
            return
            
        if not settings.features.moderation:
            await callback.answer("🚧 Модуль модерации отключён.")
            return
            
        if not _search_allowed(callback.from_user.id):
            await callback.answer("⏳ Подождите немного перед следующим поиском…", show_alert=False)
            return
            
        try:
            with db_v2.get_connection() as conn:
                cur = conn.execute(
                    """
                    SELECT c.id, c.title, c.status, cat.name as category_name
                    FROM cards_v2 c
                    JOIN categories_v2 cat ON c.category_id = cat.id
                    ORDER BY c.created_at DESC
                    LIMIT 20
                    """
                )
                rows = [dict(r) for r in cur.fetchall()]
                
            if not rows:
                text = "🔍 Недавно созданных карточек не найдено"
            else:
                text = _format_cards_rows(rows)
                
            try:
                await callback.message.edit_text(
                    text, 
                    reply_markup=_search_keyboard()
                )
            except Exception as e:
                logger.warning(f"Failed to edit message, sending new one: {e}")
                await callback.message.answer(
                    text, 
                    reply_markup=_search_keyboard()
                )
                
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Error in admin_search_recent: {e}", exc_info=True)
            await callback.answer("❌ Ошибка при выполнении поиска", show_alert=True)
            
    except Exception as e:
        logger.error(f"Unexpected error in admin_search_recent: {e}", exc_info=True)
        await callback.answer(
            "❌ Произошла непредвиденная ошибка. Пожалуйста, попробуйте ещё раз.", 
            show_alert=True
        )


@router.callback_query(F.data == "adm:reports")
async def admin_reports(callback: CallbackQuery) -> None:
    """
    Показывает отчёт по статистике системы.
    
    Args:
        callback: Callback запрос
    """
    try:
        if not await admins_service.is_admin(callback.from_user.id):
            await callback.answer("❌ Доступ запрещён")
            return
            
        lang = await profile_service.get_lang(callback.from_user.id)
        
        try:
            with db_v2.get_connection() as conn:
                # Cards by status
                cur = conn.execute("""
                    SELECT status, COUNT(*) as cnt
                    FROM cards_v2
                    GROUP BY status
                """)
                by_status = {row[0] or 'unknown': int(row[1]) for row in cur.fetchall()}

                # Totals
                cur = conn.execute("SELECT COUNT(*) FROM cards_v2")
                total_cards = int(cur.fetchone()[0])

                cur = conn.execute("SELECT COUNT(*) FROM partners_v2")
                total_partners = int(cur.fetchone()[0])

                # Recent moderation actions (7 days)
                try:
                    cur = conn.execute(
                        """
                        SELECT action, COUNT(*) as cnt
                        FROM moderation_log
                        WHERE created_at >= datetime('now','-7 days')
                        GROUP BY action
                        """
                    )
                    recent_actions = {row[0]: int(row[1]) for row in cur.fetchall()}
                except Exception as e:
                    logger.warning(f"Failed to get recent actions: {e}")
                    recent_actions = {}

            # Формируем текст отчёта
            lines = [
                "📊 <b>Отчёт по системе</b>",
                "",
                f"<b>Всего карточек:</b> {total_cards}",
                f"<b>Всего партнёров:</b> {total_partners}",
                "",
                "<b>По статусам:</b>",
                f"⏳ Ожидают модерации: {by_status.get('pending', 0)}",
                f"✅ Опубликовано: {by_status.get('published', 0)}",
                f"❌ Отклонено: {by_status.get('rejected', 0)}",
                f"🗂️ В архиве: {by_status.get('archived', 0)}",
                f"📝 Черновики: {by_status.get('draft', 0)}",
            ]
            
            if recent_actions:
                lines += [
                    "",
                    "<b>Действия за 7 дней:</b>",
                    *[f"• {k}: {v}" for k, v in recent_actions.items()],
                ]
                
            text = "\n".join(lines)
            
            try:
                await callback.message.edit_text(
                    text, 
                    reply_markup=get_admin_cabinet_inline(lang),
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.warning(f"Failed to edit message, sending new one: {e}")
                await callback.message.answer(
                    text, 
                    reply_markup=get_admin_cabinet_inline(lang),
                    parse_mode="HTML"
                )
                
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Error generating reports: {e}", exc_info=True)
            await callback.answer("❌ Ошибка при формировании отчёта", show_alert=True)
            
    except Exception as e:
        logger.error(f"Unexpected error in admin_reports: {e}", exc_info=True)
        await callback.answer(
            "❌ Произошла непредвиденная ошибка. Пожалуйста, попробуйте ещё раз.", 
            show_alert=True
        )


def get_admin_cabinet_router() -> Router:
    """Return admin cabinet router (enabled with moderation feature)."""
    if settings.features.moderation:
        return router
    return Router()


# --- Superadmin inline UI & flows (no slash commands) ---
def _is_super_admin(user_id: int) -> bool:
    return int(user_id) == int(settings.bots.admin_id)


@router.callback_query(F.data == "adm:su")
async def su_menu(callback: CallbackQuery):
    if not _is_super_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён")
        return
    lang = await profile_service.get_lang(callback.from_user.id)
    try:
        await callback.message.edit_text("👑 Суперадмин: выберите действие", reply_markup=get_superadmin_inline(lang))
    except Exception:
        await callback.message.answer("👑 Суперадмин: выберите действие", reply_markup=get_superadmin_inline(lang))
    await callback.answer()


# Simple in-memory state for prompt flows
_su_pending: dict[int, dict] = {}


def _su_set(uid: int, action: str):
    _su_pending[uid] = {"action": action, "ts": time.time()}


def _su_pop(uid: int) -> dict | None:
    return _su_pending.pop(uid, None)


@router.callback_query(F.data.startswith("adm:su:"))
async def su_action(callback: CallbackQuery):
    if not _is_super_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён")
        return
    # Simple anti-spam window for opening prompt
    if not _su_allowed(callback.from_user.id):
        await callback.answer("⏳ Подождите немного…", show_alert=False)
        return
    action = callback.data.split(":", 2)[-1]
    prompts = {
        "ban": "Введите: <tg_id> [причина]",
        "unban": "Введите: <tg_id>",
        "deluser": "Опасно! Введите: <tg_id> ДА",
        "delcard": "Опасно! Введите: <card_id> ДА",
        "delcards_by_tg": "Опасно! Введите: <partner_tg_id> ДА",
        "delallcards": "Опасно! Это удалит ВСЕ карточки. Для подтверждения введите: ДА",
        "addcard": "Введите: <partner_tg_id> <category_slug> <title> [описание]",
    }
    if action not in prompts:
        await callback.answer("Неизвестное действие", show_alert=False)
        return
    _su_set(callback.from_user.id, action)
    await callback.message.answer("✍️ " + prompts[action])
    await callback.answer()


@router.message(F.text.startswith("su:"))
async def su_message_prompt_handler(message: Message):
    # Handle only pending superadmin prompts
    st = _su_pop(message.from_user.id)
    if not st:
        return  # not for us
    if not _is_super_admin(message.from_user.id):
        await message.answer("❌ Только главный админ")
        return
    # Simple anti-spam window for submitting prompt
    if not _su_allowed(message.from_user.id):
        await message.answer("⏳ Подождите немного перед следующей командой…")
        return
    action = st.get("action")
    text = (message.text or "").strip()
    try:
        if action == "ban":
            parts = text.split(maxsplit=1)
            if not parts or not parts[0].isdigit():
                await message.answer("Неверный формат. Ожидается: <tg_id> [причина]")
                return
            uid = int(parts[0])
            reason = parts[1] if len(parts) > 1 else ""
            db_v2.ban_user(uid, reason)
            await message.answer(f"🚫 Забанен: {uid}. {('Причина: '+reason) if reason else ''}")
        elif action == "unban":
            if not text.isdigit():
                await message.answer("Неверный формат. Ожидается: <tg_id>")
                return
            uid = int(text)
            db_v2.unban_user(uid)
            await message.answer(f"✅ Разбанен: {uid}")
        elif action == "deluser":
            parts = text.split()
            if len(parts) < 2 or not parts[0].isdigit() or parts[-1].upper() != "ДА":
                await message.answer("Неверный формат. Ожидается: <tg_id> ДА")
                return
            uid = int(parts[0])
            stats = db_v2.delete_user_cascade_by_tg_id(uid)
            await message.answer(
                "🗑 Удаление пользователя завершено.\n"
                f"partners_v2: {stats.get('partners_v2',0)}, cards_v2: {stats.get('cards_v2',0)}, qr_codes_v2: {stats.get('qr_codes_v2',0)}, moderation_log: {stats.get('moderation_log',0)}\n"
                f"loyalty_wallets: {stats.get('loyalty_wallets',0)}, loy_spend_intents: {stats.get('loy_spend_intents',0)}, user_cards: {stats.get('user_cards',0)}, loyalty_transactions: {stats.get('loyalty_transactions',0)}"
            )
        elif action == "delcard":
            parts = text.split()
            if len(parts) < 2 or not parts[0].isdigit() or parts[-1].upper() != "ДА":
                await message.answer("Неверный формат. Ожидается: <card_id> ДА")
                return
            cid = int(parts[0])
            ok = db_v2.delete_card(cid)
            await message.answer("🗑 Карточка удалена" if ok else "❌ Карточка не найдена")
        elif action == "delcards_by_tg":
            parts = text.split()
            if len(parts) < 2 or not parts[0].isdigit() or parts[-1].upper() != "ДА":
                await message.answer("Неверный формат. Ожидается: <partner_tg_id> ДА")
                return
            pid = int(parts[0])
            n = db_v2.delete_cards_by_partner_tg(pid)
            await message.answer(f"🗑 Удалено карточек: {n}")
        elif action == "delallcards":
            if text.strip().upper() != "ДА":
                await message.answer("Операция отменена. Для подтверждения нужно ввести: ДА")
                return
            n = db_v2.delete_all_cards()
            await message.answer(f"🗑 Удалены ВСЕ карточки. Количество: {n}")
        elif action == "addcard":
            parts = text.split(maxsplit=3)
            if len(parts) < 3 or not parts[0].isdigit():
                await message.answer("Неверный формат. Ожидается: <partner_tg_id> <category_slug> <title> [описание]")
                return
            partner_tg = int(parts[0])
            cat = parts[1]
            title = parts[2]
            desc = parts[3] if len(parts) > 3 else None
            new_id = db_v2.admin_add_card(partner_tg, cat, title, description=desc, status="draft")
            if new_id:
                await message.answer(f"✅ Карточка создана ID={new_id} (draft)")
            else:
                await message.answer("❌ Не удалось создать карточку (проверьте категорию)")
    except Exception as e:
        logger.error(f"su_message_prompt_handler error: {e}")
        await message.answer("❌ Ошибка выполнения действия")
