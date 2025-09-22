"""
Сервис для живых дашбордов с автообновлением
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)


@dataclass
class DashboardMetric:
    """Метрика дашборда"""
    name: str
    value: int
    change: int  # Изменение за последний период
    status: str  # 'good', 'warning', 'error'
    last_updated: datetime
    description: str


@dataclass
class DashboardData:
    """Данные дашборда"""
    title: str
    metrics: List[DashboardMetric]
    last_updated: datetime
    auto_refresh_seconds: int


class LiveDashboardService:
    """Сервис для живых дашбордов"""
    
    def __init__(self):
        self.cache = {}
        self.cache_ttl = 30  # Кэш на 30 секунд
        self.refresh_tasks = {}
    
    async def get_moderation_dashboard(self) -> DashboardData:
        """Дашборд модерации"""
        try:
            # Получить данные из БД
            from core.database.db_v2 import db_v2
            
            # Подсчитать карточки по статусам
            total_cards = db_v2.get_cards_count()
            pending_cards = db_v2.get_cards_count(status='pending')
            approved_cards = db_v2.get_cards_count(status='approved')
            rejected_cards = db_v2.get_cards_count(status='rejected')
            published_cards = db_v2.get_cards_count(status='published')
            
            # Подсчитать изменения за последние 24 часа
            yesterday = datetime.now() - timedelta(days=1)
            recent_pending = db_v2.get_cards_count(status='pending', since=yesterday)
            recent_approved = db_v2.get_cards_count(status='approved', since=yesterday)
            recent_rejected = db_v2.get_cards_count(status='rejected', since=yesterday)
            
            # Создать метрики
            metrics = [
                DashboardMetric(
                    name="📝 На модерации",
                    value=pending_cards,
                    change=recent_pending,
                    status="warning" if pending_cards > 10 else "good",
                    last_updated=datetime.now(),
                    description="Карточки ожидающие модерации"
                ),
                DashboardMetric(
                    name="✅ Одобрено",
                    value=approved_cards,
                    change=recent_approved,
                    status="good",
                    last_updated=datetime.now(),
                    description="Карточки одобренные модераторами"
                ),
                DashboardMetric(
                    name="❌ Отклонено",
                    value=rejected_cards,
                    change=recent_rejected,
                    status="warning" if rejected_cards > 5 else "good",
                    last_updated=datetime.now(),
                    description="Карточки отклоненные модераторами"
                ),
                DashboardMetric(
                    name="🎉 Опубликовано",
                    value=published_cards,
                    change=0,  # Опубликованные не считаем как изменения
                    status="good",
                    last_updated=datetime.now(),
                    description="Карточки опубликованные для пользователей"
                ),
                DashboardMetric(
                    name="📊 Всего карточек",
                    value=total_cards,
                    change=recent_pending + recent_approved + recent_rejected,
                    status="good",
                    last_updated=datetime.now(),
                    description="Общее количество карточек в системе"
                )
            ]
            
            return DashboardData(
                title="📊 Дашборд модерации",
                metrics=metrics,
                last_updated=datetime.now(),
                auto_refresh_seconds=60
            )
            
        except Exception as e:
            logger.error(f"Error getting moderation dashboard: {e}")
            return self._get_error_dashboard("Ошибка загрузки дашборда модерации")
    
    async def get_notifications_dashboard(self) -> DashboardData:
        """Дашборд уведомлений"""
        try:
            # Получить данные из БД
            from core.database.db_v2 import db_v2
            
            # Подсчитать уведомления
            total_notifications = db_v2.get_notifications_count()
            unread_notifications = db_v2.get_notifications_count(read=False)
            sms_queue = db_v2.get_sms_queue_count()
            failed_sms = db_v2.get_sms_failed_count()
            
            # Подсчитать изменения за последние 24 часа
            yesterday = datetime.now() - timedelta(days=1)
            recent_notifications = db_v2.get_notifications_count(since=yesterday)
            recent_sms = db_v2.get_sms_sent_count(since=yesterday)
            
            # Создать метрики
            metrics = [
                DashboardMetric(
                    name="🔔 Всего уведомлений",
                    value=total_notifications,
                    change=recent_notifications,
                    status="good",
                    last_updated=datetime.now(),
                    description="Общее количество уведомлений"
                ),
                DashboardMetric(
                    name="📬 Непрочитанные",
                    value=unread_notifications,
                    change=0,  # Не считаем как изменения
                    status="warning" if unread_notifications > 20 else "good",
                    last_updated=datetime.now(),
                    description="Непрочитанные уведомления"
                ),
                DashboardMetric(
                    name="📱 SMS в очереди",
                    value=sms_queue,
                    change=0,  # Не считаем как изменения
                    status="warning" if sms_queue > 50 else "good",
                    last_updated=datetime.now(),
                    description="SMS сообщения в очереди на отправку"
                ),
                DashboardMetric(
                    name="❌ Неудачные SMS",
                    value=failed_sms,
                    change=0,  # Не считаем как изменения
                    status="error" if failed_sms > 10 else "good",
                    last_updated=datetime.now(),
                    description="SMS сообщения с ошибкой отправки"
                ),
                DashboardMetric(
                    name="📤 Отправлено SMS",
                    value=recent_sms,
                    change=recent_sms,
                    status="good",
                    last_updated=datetime.now(),
                    description="SMS отправленные за последние 24 часа"
                )
            ]
            
            return DashboardData(
                title="🔔 Дашборд уведомлений",
                metrics=metrics,
                last_updated=datetime.now(),
                auto_refresh_seconds=30
            )
            
        except Exception as e:
            logger.error(f"Error getting notifications dashboard: {e}")
            return self._get_error_dashboard("Ошибка загрузки дашборда уведомлений")
    
    async def get_system_dashboard(self) -> DashboardData:
        """Дашборд системы"""
        try:
            # Проверить статус компонентов
            db_status = await self._check_database_status()
            redis_status = await self._check_redis_status()
            odoo_status = await self._check_odoo_status()
            
            # Получить системные метрики
            active_connections = await self._get_active_connections()
            memory_usage = await self._get_memory_usage()
            disk_usage = await self._get_disk_usage()
            
            # Создать метрики
            metrics = [
                DashboardMetric(
                    name="🗄️ База данных",
                    value=1 if db_status else 0,
                    change=0,
                    status="good" if db_status else "error",
                    last_updated=datetime.now(),
                    description="Статус подключения к базе данных"
                ),
                DashboardMetric(
                    name="🔴 Redis",
                    value=1 if redis_status else 0,
                    change=0,
                    status="good" if redis_status else "error",
                    last_updated=datetime.now(),
                    description="Статус подключения к Redis"
                ),
                DashboardMetric(
                    name="🌐 Odoo",
                    value=1 if odoo_status else 0,
                    change=0,
                    status="good" if odoo_status else "error",
                    last_updated=datetime.now(),
                    description="Статус подключения к Odoo"
                ),
                DashboardMetric(
                    name="🔗 Активные соединения",
                    value=active_connections,
                    change=0,
                    status="warning" if active_connections > 100 else "good",
                    last_updated=datetime.now(),
                    description="Количество активных соединений"
                ),
                DashboardMetric(
                    name="💾 Использование памяти",
                    value=memory_usage,
                    change=0,
                    status="warning" if memory_usage > 80 else "good",
                    last_updated=datetime.now(),
                    description="Процент использования памяти"
                ),
                DashboardMetric(
                    name="💿 Использование диска",
                    value=disk_usage,
                    change=0,
                    status="warning" if disk_usage > 80 else "good",
                    last_updated=datetime.now(),
                    description="Процент использования диска"
                )
            ]
            
            return DashboardData(
                title="⚙️ Дашборд системы",
                metrics=metrics,
                last_updated=datetime.now(),
                auto_refresh_seconds=120
            )
            
        except Exception as e:
            logger.error(f"Error getting system dashboard: {e}")
            return self._get_error_dashboard("Ошибка загрузки дашборда системы")
    
    async def _check_database_status(self) -> bool:
        """Проверить статус базы данных"""
        try:
            from core.database.db_v2 import db_v2
            # Простой запрос для проверки соединения
            db_v2.get_cards_count()
            return True
        except Exception as e:
            logger.error(f"Database status check failed: {e}")
            return False
    
    async def _check_redis_status(self) -> bool:
        """Проверить статус Redis"""
        try:
            import redis.asyncio as aioredis
            redis_url = os.getenv('REDIS_URL')
            if not redis_url:
                return False
            
            redis_client = aioredis.from_url(redis_url)
            await redis_client.ping()
            await redis_client.close()
            return True
        except Exception as e:
            logger.error(f"Redis status check failed: {e}")
            return False
    
    async def _check_odoo_status(self) -> bool:
        """Проверить статус Odoo"""
        try:
            from core.services.odoo_api import odoo_api
            if not odoo_api.is_configured:
                return False
            
            # Простой запрос для проверки соединения
            await odoo_api.get_partner_count()
            return True
        except Exception as e:
            logger.error(f"Odoo status check failed: {e}")
            return False
    
    async def _get_active_connections(self) -> int:
        """Получить количество активных соединений"""
        try:
            # Здесь должна быть логика подсчета активных соединений
            # Пока возвращаем заглушку
            return 45
        except Exception as e:
            logger.error(f"Error getting active connections: {e}")
            return 0
    
    async def _get_memory_usage(self) -> int:
        """Получить использование памяти в процентах"""
        try:
            import psutil
            return int(psutil.virtual_memory().percent)
        except Exception as e:
            logger.error(f"Error getting memory usage: {e}")
            return 0
    
    async def _get_disk_usage(self) -> int:
        """Получить использование диска в процентах"""
        try:
            import psutil
            return int(psutil.disk_usage('/').percent)
        except Exception as e:
            logger.error(f"Error getting disk usage: {e}")
            return 0
    
    def _get_error_dashboard(self, error_message: str) -> DashboardData:
        """Создать дашборд с ошибкой"""
        return DashboardData(
            title="❌ Ошибка дашборда",
            metrics=[
                DashboardMetric(
                    name="❌ Ошибка",
                    value=0,
                    change=0,
                    status="error",
                    last_updated=datetime.now(),
                    description=error_message
                )
            ],
            last_updated=datetime.now(),
            auto_refresh_seconds=60
        )
    
    def format_dashboard_message(self, dashboard: DashboardData) -> str:
        """Форматировать дашборд в сообщение"""
        try:
            message = f"{dashboard.title}\n\n"
            
            for metric in dashboard.metrics:
                # Эмодзи статуса
                status_emoji = {
                    "good": "✅",
                    "warning": "⚠️",
                    "error": "❌"
                }.get(metric.status, "❓")
                
                # Знак изменения
                change_sign = "+" if metric.change > 0 else "" if metric.change == 0 else ""
                change_text = f" ({change_sign}{metric.change})" if metric.change != 0 else ""
                
                message += f"{status_emoji} {metric.name}: <b>{metric.value}</b>{change_text}\n"
                message += f"   <i>{metric.description}</i>\n\n"
            
            # Время обновления
            message += f"🕐 <i>Обновлено: {dashboard.last_updated.strftime('%H:%M:%S')}</i>\n"
            message += f"🔄 <i>Автообновление: каждые {dashboard.auto_refresh_seconds} сек</i>"
            
            return message
            
        except Exception as e:
            logger.error(f"Error formatting dashboard message: {e}")
            return f"❌ Ошибка форматирования дашборда: {str(e)}"
    
    async def start_auto_refresh(self, dashboard_type: str, callback_func, user_id: int):
        """Запустить автообновление дашборда"""
        try:
            if dashboard_type in self.refresh_tasks:
                await self.stop_auto_refresh(dashboard_type)
            
            async def refresh_loop():
                while True:
                    try:
                        # Получить данные дашборда
                        if dashboard_type == "moderation":
                            dashboard = await self.get_moderation_dashboard()
                        elif dashboard_type == "notifications":
                            dashboard = await self.get_notifications_dashboard()
                        elif dashboard_type == "system":
                            dashboard = await self.get_system_dashboard()
                        else:
                            break
                        
                        # Обновить сообщение
                        message = self.format_dashboard_message(dashboard)
                        await callback_func(user_id, message)
                        
                        # Ждать до следующего обновления
                        await asyncio.sleep(dashboard.auto_refresh_seconds)
                        
                    except Exception as e:
                        logger.error(f"Error in refresh loop: {e}")
                        await asyncio.sleep(60)  # Ждать минуту при ошибке
            
            # Запустить задачу
            task = asyncio.create_task(refresh_loop())
            self.refresh_tasks[dashboard_type] = task
            
            logger.info(f"Auto-refresh started for {dashboard_type} dashboard")
            
        except Exception as e:
            logger.error(f"Error starting auto-refresh: {e}")
    
    async def stop_auto_refresh(self, dashboard_type: str):
        """Остановить автообновление дашборда"""
        try:
            if dashboard_type in self.refresh_tasks:
                task = self.refresh_tasks[dashboard_type]
                task.cancel()
                del self.refresh_tasks[dashboard_type]
                logger.info(f"Auto-refresh stopped for {dashboard_type} dashboard")
        except Exception as e:
            logger.error(f"Error stopping auto-refresh: {e}")


# Глобальный экземпляр сервиса
live_dashboard = LiveDashboardService()


# Утилитарные функции для удобства
async def get_moderation_dashboard() -> DashboardData:
    """Получить дашборд модерации"""
    return await live_dashboard.get_moderation_dashboard()

async def get_notifications_dashboard() -> DashboardData:
    """Получить дашборд уведомлений"""
    return await live_dashboard.get_notifications_dashboard()

async def get_system_dashboard() -> DashboardData:
    """Получить дашборд системы"""
    return await live_dashboard.get_system_dashboard()

def format_dashboard(dashboard: DashboardData) -> str:
    """Форматировать дашборд в сообщение"""
    return live_dashboard.format_dashboard_message(dashboard)
