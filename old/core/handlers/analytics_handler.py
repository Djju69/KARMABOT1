"""
Обработчики для расширенной аналитики системы
"""
import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from ..services.user_service import get_user_role
from ..services.analytics_service import analytics_service

logger = logging.getLogger(__name__)
router = Router(name="analytics_handler")


@router.message(Command("analytics"))
async def show_analytics_dashboard(message: Message):
    """Показать дашборд аналитики (только для админов)"""
    try:
        # Проверяем права администратора
        user_role = await get_user_role(message.from_user.id)
        
        if user_role not in ['admin', 'super_admin']:
            await message.answer("❌ У вас нет прав для просмотра аналитики")
            return
        
        await message.answer("📊 Загружаю аналитику...")
        
        # Получаем данные дашборда
        dashboard_data = await analytics_service.get_dashboard_data()
        
        if not dashboard_data:
            await message.answer("❌ Ошибка загрузки аналитики")
            return
        
        # Формируем отчет
        report = "📊 <b>ДАШБОРД АНАЛИТИКИ</b>\n\n"
        
        # Метрики пользователей
        users = dashboard_data.get('users', {})
        report += "👥 <b>ПОЛЬЗОВАТЕЛИ</b>\n"
        report += f"• Всего: {users.get('total_users', 0)}\n"
        report += f"• Активных за 7 дней: {users.get('active_users_7d', 0)}\n"
        report += f"• Активных за 30 дней: {users.get('active_users_30d', 0)}\n"
        report += f"• Новых сегодня: {users.get('new_users_today', 0)}\n"
        report += f"• Новых за неделю: {users.get('new_users_7d', 0)}\n"
        report += f"• Средние баллы: {users.get('avg_points_per_user', 0):.1f}\n\n"
        
        # Метрики партнеров
        partners = dashboard_data.get('partners', {})
        report += "🤝 <b>ПАРТНЕРЫ</b>\n"
        report += f"• Всего: {partners.get('total_partners', 0)}\n"
        report += f"• Активных: {partners.get('active_partners', 0)}\n"
        report += f"• На модерации: {partners.get('pending_partners', 0)}\n"
        report += f"• Отклоненных: {partners.get('rejected_partners', 0)}\n"
        report += f"• Среднее карт на партнера: {partners.get('avg_cards_per_partner', 0):.1f}\n\n"
        
        # Метрики транзакций
        transactions = dashboard_data.get('transactions', {})
        report += "💰 <b>ТРАНЗАКЦИИ</b>\n"
        report += f"• Всего: {transactions.get('total_transactions', 0)}\n"
        report += f"• Сегодня: {transactions.get('transactions_today', 0)}\n"
        report += f"• За неделю: {transactions.get('transactions_7d', 0)}\n"
        report += f"• За месяц: {transactions.get('transactions_30d', 0)}\n"
        report += f"• Заработано баллов: {transactions.get('total_points_earned', 0)}\n"
        report += f"• Потрачено баллов: {transactions.get('total_points_spent', 0)}\n"
        report += f"• Средняя транзакция: {transactions.get('avg_transaction_value', 0):.1f}\n\n"
        
        # Топ категории
        business = dashboard_data.get('business', {})
        top_categories = business.get('top_categories', [])
        if top_categories:
            report += "🏆 <b>ТОП КАТЕГОРИИ</b>\n"
            for i, cat in enumerate(top_categories[:5], 1):
                report += f"{i}. {cat.get('name', 'Неизвестно')}: {cat.get('card_count', 0)} карт\n"
        
        report += f"\n🕒 Обновлено: {dashboard_data.get('generated_at', 'Неизвестно')[:19]}"
        
        await message.answer(report, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Error showing analytics dashboard: {e}")
        await message.answer("❌ Ошибка получения аналитики")


@router.message(Command("user_stats"))
async def show_user_statistics(message: Message):
    """Показать детальную статистику пользователей"""
    try:
        # Проверяем права администратора
        user_role = await get_user_role(message.from_user.id)
        
        if user_role not in ['admin', 'super_admin']:
            await message.answer("❌ У вас нет прав для просмотра статистики пользователей")
            return
        
        await message.answer("👥 Загружаю статистику пользователей...")
        
        # Получаем метрики пользователей
        user_metrics = await analytics_service.get_user_metrics()
        
        report = "👥 <b>СТАТИСТИКА ПОЛЬЗОВАТЕЛЕЙ</b>\n\n"
        
        report += f"📊 <b>Общие показатели:</b>\n"
        report += f"• Всего пользователей: {user_metrics.total_users}\n"
        report += f"• Активных за 7 дней: {user_metrics.active_users_7d}\n"
        report += f"• Активных за 30 дней: {user_metrics.active_users_30d}\n"
        report += f"• Средние баллы: {user_metrics.avg_points_per_user:.1f}\n\n"
        
        report += f"📈 <b>Новые пользователи:</b>\n"
        report += f"• Сегодня: {user_metrics.new_users_today}\n"
        report += f"• За неделю: {user_metrics.new_users_7d}\n"
        report += f"• За месяц: {user_metrics.new_users_30d}\n\n"
        
        # Топ пользователи
        if user_metrics.top_users_by_points:
            report += "🏆 <b>ТОП ПОЛЬЗОВАТЕЛИ ПО БАЛЛАМ</b>\n"
            for i, user in enumerate(user_metrics.top_users_by_points[:10], 1):
                name = user.get('first_name', 'Пользователь')
                username = f"@{user.get('username', '')}" if user.get('username') else ""
                points = user.get('points_balance', 0)
                report += f"{i}. {name} {username}: {points} баллов\n"
        
        await message.answer(report, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Error showing user statistics: {e}")
        await message.answer("❌ Ошибка получения статистики пользователей")


@router.message(Command("partner_stats"))
async def show_partner_statistics(message: Message):
    """Показать детальную статистику партнеров"""
    try:
        # Проверяем права администратора
        user_role = await get_user_role(message.from_user.id)
        
        if user_role not in ['admin', 'super_admin']:
            await message.answer("❌ У вас нет прав для просмотра статистики партнеров")
            return
        
        await message.answer("🤝 Загружаю статистику партнеров...")
        
        # Получаем метрики партнеров
        partner_metrics = await analytics_service.get_partner_metrics()
        
        report = "🤝 <b>СТАТИСТИКА ПАРТНЕРОВ</b>\n\n"
        
        report += f"📊 <b>Общие показатели:</b>\n"
        report += f"• Всего партнеров: {partner_metrics.total_partners}\n"
        report += f"• Активных: {partner_metrics.active_partners}\n"
        report += f"• На модерации: {partner_metrics.pending_partners}\n"
        report += f"• Отклоненных: {partner_metrics.rejected_partners}\n"
        report += f"• Среднее карт на партнера: {partner_metrics.avg_cards_per_partner:.1f}\n\n"
        
        # Топ партнеры
        if partner_metrics.top_partners_by_cards:
            report += "🏆 <b>ТОП ПАРТНЕРЫ ПО КАРТАМ</b>\n"
            for i, partner in enumerate(partner_metrics.top_partners_by_cards[:10], 1):
                name = partner.get('display_name', 'Партнер')
                cards = partner.get('card_count', 0)
                report += f"{i}. {name}: {cards} карт\n"
        
        await message.answer(report, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Error showing partner statistics: {e}")
        await message.answer("❌ Ошибка получения статистики партнеров")


@router.message(Command("transaction_stats"))
async def show_transaction_statistics(message: Message):
    """Показать детальную статистику транзакций"""
    try:
        # Проверяем права администратора
        user_role = await get_user_role(message.from_user.id)
        
        if user_role not in ['admin', 'super_admin']:
            await message.answer("❌ У вас нет прав для просмотра статистики транзакций")
            return
        
        await message.answer("💰 Загружаю статистику транзакций...")
        
        # Получаем метрики транзакций
        transaction_metrics = await analytics_service.get_transaction_metrics()
        
        report = "💰 <b>СТАТИСТИКА ТРАНЗАКЦИЙ</b>\n\n"
        
        report += f"📊 <b>Общие показатели:</b>\n"
        report += f"• Всего транзакций: {transaction_metrics.total_transactions}\n"
        report += f"• Сегодня: {transaction_metrics.transactions_today}\n"
        report += f"• За неделю: {transaction_metrics.transactions_7d}\n"
        report += f"• За месяц: {transaction_metrics.transactions_30d}\n"
        report += f"• Средняя транзакция: {transaction_metrics.avg_transaction_value:.1f} баллов\n\n"
        
        report += f"💎 <b>Баллы:</b>\n"
        report += f"• Заработано всего: {transaction_metrics.total_points_earned}\n"
        report += f"• Потрачено всего: {transaction_metrics.total_points_spent}\n"
        report += f"• Чистый баланс: {transaction_metrics.total_points_earned - transaction_metrics.total_points_spent}\n\n"
        
        # Топ типы транзакций
        if transaction_metrics.top_transaction_types:
            report += "🏆 <b>ТОП ТИПЫ ТРАНЗАКЦИЙ</b>\n"
            for i, tx_type in enumerate(transaction_metrics.top_transaction_types[:10], 1):
                tx_name = tx_type.get('type', 'Неизвестно')
                count = tx_type.get('count', 0)
                report += f"{i}. {tx_name}: {count} транзакций\n"
        
        await message.answer(report, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Error showing transaction statistics: {e}")
        await message.answer("❌ Ошибка получения статистики транзакций")


def get_analytics_router() -> Router:
    """Получить роутер аналитики"""
    return router


__all__ = ['router', 'get_analytics_router']
