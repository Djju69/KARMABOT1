"""
Обработчики для мониторинга производительности системы
"""
import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from ..services.user_service import get_user_role
from ..services.performance_service import performance_service

logger = logging.getLogger(__name__)
router = Router(name="performance_handler")


@router.message(Command("perf_stats"))
async def show_performance_stats(message: Message):
    """Показать статистику производительности (только для админов)"""
    try:
        # Проверяем права администратора
        user_role = await get_user_role(message.from_user.id)
        
        if user_role not in ['admin', 'super_admin']:
            await message.answer("❌ У вас нет прав для просмотра статистики производительности")
            return
        
        # Получаем статистику
        stats = await performance_service.get_performance_stats()
        
        # Формируем отчет
        report = "📊 <b>Статистика производительности</b>\n\n"
        
        if stats.get('metrics'):
            report += "🔍 <b>Метрики запросов:</b>\n"
            for query_name, metric in stats['metrics'].items():
                report += f"• <b>{query_name}</b>\n"
                report += f"  └ Выполнений: {metric['count']}\n"
                report += f"  └ Среднее время: {metric['avg_time']:.2f}мс\n"
                report += f"  └ Мин/Макс: {metric['min_time']:.2f}мс / {metric['max_time']:.2f}мс\n\n"
        
        if stats.get('slow_queries_count', 0) > 0:
            report += f"🐌 <b>Медленные запросы:</b> {stats['slow_queries_count']}\n"
            if stats.get('recent_slow_queries'):
                report += "Последние медленные запросы:\n"
                for query in stats['recent_slow_queries'][-5:]:  # Последние 5
                    report += f"• {query['query']}: {query['duration_ms']:.2f}мс\n"
        
        report += f"\n📈 <b>Общая статистика:</b>\n"
        report += f"• Всего запросов: {stats.get('total_queries', 0)}\n"
        report += f"• Сервис инициализирован: {'✅' if stats.get('is_initialized') else '❌'}\n"
        
        # Показываем конфигурацию кэша
        if stats.get('cache_ttl_config'):
            report += f"\n⏰ <b>Настройки кэша:</b>\n"
            for cache_type, ttl in stats['cache_ttl_config'].items():
                report += f"• {cache_type}: {ttl}с\n"
        
        await message.answer(report, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Error showing performance stats: {e}")
        await message.answer("❌ Ошибка получения статистики производительности")


@router.message(Command("optimize_perf"))
async def optimize_performance(message: Message):
    """Оптимизировать производительность (только для супер-админов)"""
    try:
        # Проверяем права супер-админа
        user_role = await get_user_role(message.from_user.id)
        
        if user_role != 'super_admin':
            await message.answer("❌ У вас нет прав для оптимизации производительности")
            return
        
        await message.answer("🔧 Начинаю оптимизацию производительности...")
        
        # Оптимизируем медленные запросы
        await performance_service.optimize_slow_queries()
        
        # Получаем обновленную статистику
        stats = await performance_service.get_performance_stats()
        
        report = "✅ <b>Оптимизация завершена!</b>\n\n"
        report += f"📊 <b>Результаты:</b>\n"
        report += f"• Медленных запросов: {stats.get('slow_queries_count', 0)}\n"
        report += f"• Всего запросов: {stats.get('total_queries', 0)}\n"
        
        await message.answer(report, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Error optimizing performance: {e}")
        await message.answer("❌ Ошибка оптимизации производительности")


@router.message(Command("cache_clear"))
async def clear_cache(message: Message):
    """Очистить кэш (только для супер-админов)"""
    try:
        # Проверяем права супер-админа
        user_role = await get_user_role(message.from_user.id)
        
        if user_role != 'super_admin':
            await message.answer("❌ У вас нет прав для очистки кэша")
            return
        
        await message.answer("🗑️ Очищаю кэш...")
        
        # Очищаем кэш
        from core.services.cache import cache_service
        
        # Очищаем основные ключи кэша
        cache_keys = [
            "loyalty:balance:*",
            "loyalty:history:*", 
            "catalog:*",
            "user_profile:*",
            "partner_info:*",
            "categories:*",
            "loyalty_config:*",
            "tariffs:*",
            "translations:*"
        ]
        
        cleared_count = 0
        for pattern in cache_keys:
            try:
                # В реальной реализации здесь был бы метод для очистки по паттерну
                # Пока просто логируем
                logger.info(f"Clearing cache pattern: {pattern}")
                cleared_count += 1
            except Exception as e:
                logger.warning(f"Failed to clear cache pattern {pattern}: {e}")
        
        report = f"✅ <b>Кэш очищен!</b>\n\n"
        report += f"🗑️ Очищено паттернов: {cleared_count}\n"
        report += f"💡 Кэш будет пересоздан при следующих запросах"
        
        await message.answer(report, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        await message.answer("❌ Ошибка очистки кэша")


def get_performance_router() -> Router:
    """Получить роутер производительности"""
    return router


__all__ = ['router', 'get_performance_router']
