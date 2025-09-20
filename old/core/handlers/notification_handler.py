"""
Обработчики для системы уведомлений и алертов
"""
import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from ..services.user_service import get_user_role
from ..services.notification_service import notification_service, NotificationType, AlertLevel

logger = logging.getLogger(__name__)
router = Router(name="notification_handler")


@router.message(Command("notifications"))
async def show_notifications(message: Message):
    """Показать уведомления пользователя"""
    try:
        user_id = message.from_user.id
        
        # Получаем уведомления пользователя
        notifications = await notification_service.get_user_notifications(user_id)
        
        if not notifications:
            await message.answer("📱 У вас нет новых уведомлений")
            return
        
        report = "📱 <b>ВАШИ УВЕДОМЛЕНИЯ</b>\n\n"
        
        for i, notif in enumerate(notifications[:10], 1):
            status = "✅" if notif.read else "🔔"
            report += f"{status} <b>{notif.title}</b>\n"
            report += f"   {notif.message}\n"
            report += f"   <i>{notif.created_at.strftime('%d.%m.%Y %H:%M')}</i>\n\n"
        
        if len(notifications) > 10:
            report += f"... и еще {len(notifications) - 10} уведомлений"
        
        await message.answer(report, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Error showing notifications: {e}")
        await message.answer("❌ Ошибка загрузки уведомлений")


@router.message(Command("alerts"))
async def show_alerts(message: Message):
    """Показать системные алерты (только для админов)"""
    try:
        # Проверяем права администратора
        user_role = await get_user_role(message.from_user.id)
        
        if user_role not in ['admin', 'super_admin']:
            await message.answer("❌ У вас нет прав для просмотра алертов")
            return
        
        # Получаем активные алерты
        alerts = await notification_service.get_active_alerts()
        
        if not alerts:
            await message.answer("✅ Активных алертов нет")
            return
        
        report = "🚨 <b>СИСТЕМНЫЕ АЛЕРТЫ</b>\n\n"
        
        for i, alert in enumerate(alerts[:10], 1):
            level_emoji = {
                AlertLevel.CRITICAL: "🔴",
                AlertLevel.HIGH: "🟠", 
                AlertLevel.MEDIUM: "🟡",
                AlertLevel.LOW: "🔵"
            }.get(alert.level, "⚪")
            
            report += f"{level_emoji} <b>{alert.title}</b>\n"
            report += f"   [{alert.level.value.upper()}] {alert.message}\n"
            report += f"   Категория: {alert.category}\n"
            report += f"   <i>{alert.created_at.strftime('%d.%m.%Y %H:%M')}</i>\n\n"
        
        if len(alerts) > 10:
            report += f"... и еще {len(alerts) - 10} алертов"
        
        await message.answer(report, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Error showing alerts: {e}")
        await message.answer("❌ Ошибка загрузки алертов")


@router.message(Command("alert_stats"))
async def show_alert_statistics(message: Message):
    """Показать статистику уведомлений и алертов (только для админов)"""
    try:
        # Проверяем права администратора
        user_role = await get_user_role(message.from_user.id)
        
        if user_role not in ['admin', 'super_admin']:
            await message.answer("❌ У вас нет прав для просмотра статистики уведомлений")
            return
        
        # Получаем статистику
        stats = await notification_service.get_notification_stats()
        
        report = "📊 <b>СТАТИСТИКА УВЕДОМЛЕНИЙ</b>\n\n"
        
        report += f"📱 <b>Уведомления:</b>\n"
        report += f"• Всего: {stats.get('total_notifications', 0)}\n"
        report += f"• Непрочитанных: {stats.get('unread_notifications', 0)}\n\n"
        
        report += f"🚨 <b>Алерты:</b>\n"
        report += f"• Всего: {stats.get('total_alerts', 0)}\n"
        report += f"• Активных: {stats.get('active_alerts', 0)}\n\n"
        
        report += f"👥 <b>Подписчики:</b>\n"
        report += f"• Всего подписок: {stats.get('subscribers_count', 0)}\n\n"
        
        # Статистика по типам уведомлений
        type_stats = stats.get('type_stats', {})
        if type_stats:
            report += f"📈 <b>По типам:</b>\n"
            for ntype, count in type_stats.items():
                emoji = {
                    'info': 'ℹ️',
                    'warning': '⚠️',
                    'error': '❌',
                    'success': '✅',
                    'system': '🔧'
                }.get(ntype, '📱')
                report += f"• {emoji} {ntype}: {count}\n"
        
        await message.answer(report, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Error showing alert statistics: {e}")
        await message.answer("❌ Ошибка получения статистики уведомлений")


@router.message(Command("subscribe_alerts"))
async def subscribe_to_alerts(message: Message):
    """Подписаться на алерты"""
    try:
        user_id = message.from_user.id
        
        # Подписываем на алерты среднего и высокого уровня
        await notification_service.subscribe_to_alerts(user_id, AlertLevel.MEDIUM)
        await notification_service.subscribe_to_alerts(user_id, AlertLevel.HIGH)
        
        await message.answer(
            "📧 <b>Подписка на алерты активирована</b>\n\n"
            "Вы будете получать уведомления о:\n"
            "• 🟡 Средних алертах\n"
            "• 🟠 Высоких алертах\n\n"
            "Используйте /unsubscribe_alerts для отмены подписки",
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Error subscribing to alerts: {e}")
        await message.answer("❌ Ошибка подписки на алерты")


@router.message(Command("unsubscribe_alerts"))
async def unsubscribe_from_alerts(message: Message):
    """Отписаться от алертов"""
    try:
        user_id = message.from_user.id
        
        # Отписываем от всех алертов
        for level in [AlertLevel.LOW, AlertLevel.MEDIUM, AlertLevel.HIGH, AlertLevel.CRITICAL]:
            await notification_service.unsubscribe_from_alerts(user_id, level)
        
        await message.answer(
            "📧 <b>Подписка на алерты отменена</b>\n\n"
            "Вы больше не будете получать системные алерты.\n"
            "Используйте /subscribe_alerts для возобновления подписки",
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Error unsubscribing from alerts: {e}")
        await message.answer("❌ Ошибка отписки от алертов")


@router.message(Command("send_alert"))
async def send_test_alert(message: Message):
    """Отправить тестовый алерт (только для супер-админов)"""
    try:
        # Проверяем права супер-админа
        user_role = await get_user_role(message.from_user.id)
        
        if user_role != 'super_admin':
            await message.answer("❌ У вас нет прав для отправки алертов")
            return
        
        # Создаем тестовый алерт
        alert_id = await notification_service.create_alert(
            title="Тестовый алерт",
            message="Это тестовое уведомление для проверки системы алертов",
            level=AlertLevel.MEDIUM,
            category="test"
        )
        
        if alert_id:
            await message.answer(
                f"✅ <b>Тестовый алерт отправлен</b>\n\n"
                f"ID алерта: {alert_id}\n"
                f"Уровень: MEDIUM\n"
                f"Категория: test",
                parse_mode="HTML"
            )
        else:
            await message.answer("❌ Ошибка отправки тестового алерта")
        
    except Exception as e:
        logger.error(f"Error sending test alert: {e}")
        await message.answer("❌ Ошибка отправки тестового алерта")


def get_notification_router() -> Router:
    """Получить роутер уведомлений"""
    return router


__all__ = ['router', 'get_notification_router']