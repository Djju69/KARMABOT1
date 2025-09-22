"""
Сервис уведомлений и алертов для KARMABOT1
Включает push-уведомления, email-алерты и системные уведомления
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json

from .cache import cache_service

logger = logging.getLogger(__name__)


class NotificationType(Enum):
    """Типы уведомлений"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"
    SYSTEM = "system"


class AlertLevel(Enum):
    """Уровни алертов"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Notification:
    """Уведомление"""
    id: str
    user_id: int
    title: str
    message: str
    notification_type: NotificationType
    created_at: datetime
    read: bool = False
    data: Optional[Dict[str, Any]] = None


@dataclass
class Alert:
    """Алерт"""
    id: str
    title: str
    message: str
    level: AlertLevel
    category: str
    created_at: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    data: Optional[Dict[str, Any]] = None


class NotificationService:
    """Сервис уведомлений"""
    
    def __init__(self):
        self.notifications = {}  # В реальной системе это будет БД
        self.alerts = {}
        self.subscribers = {}  # Подписчики на алерты
        self.is_initialized = False
    
    async def initialize(self):
        """Инициализация сервиса уведомлений"""
        if self.is_initialized:
            return
        
        try:
            # Загружаем настройки уведомлений
            await self._load_notification_settings()
            self.is_initialized = True
            logger.info("🔔 Notification service initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize notification service: {e}")
    
    async def _load_notification_settings(self):
        """Загрузка настроек уведомлений"""
        try:
            from core.database.db_v2 import get_connection
            
            with get_connection() as conn:
                # Проверяем наличие таблицы настроек уведомлений
                cursor = conn.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='notification_settings'
                """)
                
                if not cursor.fetchone():
                    # Создаем таблицу настроек уведомлений
                    conn.execute("""
                        CREATE TABLE notification_settings (
                            id INTEGER PRIMARY KEY,
                            user_id INTEGER,
                            email_notifications BOOLEAN DEFAULT 1,
                            push_notifications BOOLEAN DEFAULT 1,
                            system_alerts BOOLEAN DEFAULT 1,
                            partner_updates BOOLEAN DEFAULT 1,
                            loyalty_updates BOOLEAN DEFAULT 1,
                            created_at TEXT,
                            updated_at TEXT
                        )
                    """)
                    conn.commit()
                    logger.info("📋 Notification settings table created")
                    
        except Exception as e:
            logger.error(f"❌ Failed to load notification settings: {e}")
    
    async def send_notification(self, 
                              user_id: int, 
                              title: str, 
                              message: str, 
                              notification_type: NotificationType = NotificationType.INFO,
                              data: Optional[Dict[str, Any]] = None) -> bool:
        """Отправить уведомление пользователю"""
        try:
            notification_id = f"notif_{user_id}_{int(datetime.now().timestamp())}"
            
            notification = Notification(
                id=notification_id,
                user_id=user_id,
                title=title,
                message=message,
                notification_type=notification_type,
                created_at=datetime.now(),
                data=data
            )
            
            # Сохраняем уведомление
            self.notifications[notification_id] = notification
            
            # Отправляем через Telegram (если доступен)
            await self._send_telegram_notification(notification)
            
            # Кэшируем для быстрого доступа
            cache_key = f"notifications:{user_id}"
            await cache_service.set(cache_key, json.dumps(notification.__dict__), ex=3600)
            
            logger.info(f"📱 Notification sent to user {user_id}: {title}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send notification to user {user_id}: {e}")
            return False
    
    async def _send_telegram_notification(self, notification: Notification):
        """Отправить уведомление через Telegram"""
        try:
            # В реальной системе здесь будет отправка через Telegram Bot API
            # Пока просто логируем
            logger.info(f"📱 Telegram notification: {notification.title} - {notification.message}")
            
        except Exception as e:
            logger.error(f"❌ Failed to send Telegram notification: {e}")
    
    async def get_user_notifications(self, user_id: int, limit: int = 20) -> List[Notification]:
        """Получить уведомления пользователя"""
        try:
            # Получаем из кэша
            cache_key = f"notifications:{user_id}"
            cached = await cache_service.get(cache_key)
            
            if cached:
                notification_data = json.loads(cached)
                return [Notification(**notification_data)]
            
            # Получаем из хранилища
            user_notifications = [
                notif for notif in self.notifications.values()
                if notif.user_id == user_id
            ]
            
            # Сортируем по дате создания (новые первыми)
            user_notifications.sort(key=lambda x: x.created_at, reverse=True)
            
            return user_notifications[:limit]
            
        except Exception as e:
            logger.error(f"❌ Failed to get notifications for user {user_id}: {e}")
            return []
    
    async def mark_notification_read(self, notification_id: str) -> bool:
        """Отметить уведомление как прочитанное"""
        try:
            if notification_id in self.notifications:
                self.notifications[notification_id].read = True
                logger.info(f"✅ Notification {notification_id} marked as read")
                return True
            return False
            
        except Exception as e:
            logger.error(f"❌ Failed to mark notification {notification_id} as read: {e}")
            return False
    
    async def create_alert(self, 
                          title: str, 
                          message: str, 
                          level: AlertLevel, 
                          category: str,
                          data: Optional[Dict[str, Any]] = None) -> str:
        """Создать системный алерт"""
        try:
            alert_id = f"alert_{int(datetime.now().timestamp())}"
            
            alert = Alert(
                id=alert_id,
                title=title,
                message=message,
                level=level,
                category=category,
                created_at=datetime.now(),
                data=data
            )
            
            # Сохраняем алерт
            self.alerts[alert_id] = alert
            
            # Уведомляем подписчиков
            await self._notify_alert_subscribers(alert)
            
            # Логируем алерт
            logger.warning(f"🚨 ALERT [{level.value.upper()}] {category}: {title} - {message}")
            
            return alert_id
            
        except Exception as e:
            logger.error(f"❌ Failed to create alert: {e}")
            return ""
    
    async def _notify_alert_subscribers(self, alert: Alert):
        """Уведомить подписчиков об алерте"""
        try:
            # Получаем подписчиков на алерты данного уровня
            subscribers = self.subscribers.get(alert.level.value, [])
            
            for subscriber_id in subscribers:
                await self.send_notification(
                    user_id=subscriber_id,
                    title=f"🚨 Алерт: {alert.title}",
                    message=f"[{alert.level.value.upper()}] {alert.message}",
                    notification_type=NotificationType.WARNING,
                    data={'alert_id': alert.id, 'category': alert.category}
                )
                
        except Exception as e:
            logger.error(f"❌ Failed to notify alert subscribers: {e}")
    
    async def resolve_alert(self, alert_id: str) -> bool:
        """Разрешить алерт"""
        try:
            if alert_id in self.alerts:
                self.alerts[alert_id].resolved = True
                self.alerts[alert_id].resolved_at = datetime.now()
                logger.info(f"✅ Alert {alert_id} resolved")
                return True
            return False
            
        except Exception as e:
            logger.error(f"❌ Failed to resolve alert {alert_id}: {e}")
            return False
    
    async def get_active_alerts(self) -> List[Alert]:
        """Получить активные алерты"""
        try:
            active_alerts = [
                alert for alert in self.alerts.values()
                if not alert.resolved
            ]
            
            # Сортируем по уровню критичности
            level_order = {
                AlertLevel.CRITICAL: 0,
                AlertLevel.HIGH: 1,
                AlertLevel.MEDIUM: 2,
                AlertLevel.LOW: 3
            }
            
            active_alerts.sort(key=lambda x: level_order.get(x.level, 4))
            return active_alerts
            
        except Exception as e:
            logger.error(f"❌ Failed to get active alerts: {e}")
            return []
    
    async def subscribe_to_alerts(self, user_id: int, alert_level: AlertLevel):
        """Подписать пользователя на алерты определенного уровня"""
        try:
            if alert_level.value not in self.subscribers:
                self.subscribers[alert_level.value] = []
            
            if user_id not in self.subscribers[alert_level.value]:
                self.subscribers[alert_level.value].append(user_id)
                logger.info(f"📧 User {user_id} subscribed to {alert_level.value} alerts")
                
        except Exception as e:
            logger.error(f"❌ Failed to subscribe user {user_id} to alerts: {e}")
    
    async def unsubscribe_from_alerts(self, user_id: int, alert_level: AlertLevel):
        """Отписать пользователя от алертов"""
        try:
            if alert_level.value in self.subscribers:
                if user_id in self.subscribers[alert_level.value]:
                    self.subscribers[alert_level.value].remove(user_id)
                    logger.info(f"📧 User {user_id} unsubscribed from {alert_level.value} alerts")
                    
        except Exception as e:
            logger.error(f"❌ Failed to unsubscribe user {user_id} from alerts: {e}")
    
    async def send_bulk_notification(self, 
                                   user_ids: List[int], 
                                   title: str, 
                                   message: str,
                                   notification_type: NotificationType = NotificationType.INFO) -> int:
        """Отправить массовое уведомление"""
        try:
            sent_count = 0
            
            for user_id in user_ids:
                success = await self.send_notification(
                    user_id=user_id,
                    title=title,
                    message=message,
                    notification_type=notification_type
                )
                if success:
                    sent_count += 1
            
            logger.info(f"📢 Bulk notification sent to {sent_count}/{len(user_ids)} users")
            return sent_count
            
        except Exception as e:
            logger.error(f"❌ Failed to send bulk notification: {e}")
            return 0
    
    async def get_notification_stats(self) -> Dict[str, Any]:
        """Получить статистику уведомлений"""
        try:
            total_notifications = len(self.notifications)
            unread_notifications = len([
                n for n in self.notifications.values() if not n.read
            ])
            
            total_alerts = len(self.alerts)
            active_alerts = len([
                a for a in self.alerts.values() if not a.resolved
            ])
            
            # Статистика по типам
            type_stats = {}
            for notification in self.notifications.values():
                ntype = notification.notification_type.value
                type_stats[ntype] = type_stats.get(ntype, 0) + 1
            
            return {
                'total_notifications': total_notifications,
                'unread_notifications': unread_notifications,
                'total_alerts': total_alerts,
                'active_alerts': active_alerts,
                'type_stats': type_stats,
                'subscribers_count': sum(len(subs) for subs in self.subscribers.values())
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get notification stats: {e}")
            return {}


# Глобальный экземпляр сервиса
notification_service = NotificationService()


__all__ = [
    'NotificationService',
    'notification_service',
    'Notification',
    'Alert',
    'NotificationType',
    'AlertLevel'
]