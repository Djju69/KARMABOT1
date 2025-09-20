"""
Сервис расширенной аналитики для KARMABOT1
Включает метрики пользователей, партнеров, транзакций и бизнес-аналитику
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import json

from .cache import cache_service

logger = logging.getLogger(__name__)


@dataclass
class UserMetrics:
    """Метрики пользователя"""
    total_users: int
    active_users_7d: int
    active_users_30d: int
    new_users_today: int
    new_users_7d: int
    new_users_30d: int
    avg_points_per_user: float
    top_users_by_points: List[Dict[str, Any]]


@dataclass
class PartnerMetrics:
    """Метрики партнеров"""
    total_partners: int
    active_partners: int
    pending_partners: int
    approved_partners: int
    rejected_partners: int
    avg_cards_per_partner: float
    top_partners_by_cards: List[Dict[str, Any]]


@dataclass
class TransactionMetrics:
    """Метрики транзакций"""
    total_transactions: int
    transactions_today: int
    transactions_7d: int
    transactions_30d: int
    total_points_earned: int
    total_points_spent: int
    avg_transaction_value: float
    top_transaction_types: List[Dict[str, Any]]


@dataclass
class BusinessMetrics:
    """Бизнес-метрики"""
    revenue_today: float
    revenue_7d: float
    revenue_30d: float
    conversion_rate: float
    retention_rate_7d: float
    retention_rate_30d: float
    avg_session_duration: float
    top_categories: List[Dict[str, Any]]


class AnalyticsService:
    """Сервис аналитики"""
    
    def __init__(self):
        self.cache_ttl = 300  # 5 минут для аналитики
        self.is_initialized = False
    
    async def initialize(self):
        """Инициализация сервиса аналитики"""
        if self.is_initialized:
            return
        
        try:
            # Создаем базовые индексы для аналитики
            await self._create_analytics_indexes()
            self.is_initialized = True
            logger.info("📊 Analytics service initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize analytics service: {e}")
    
    async def _create_analytics_indexes(self):
        """Создание индексов для аналитики"""
        try:
            from core.database.db_v2 import get_connection
            
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at)",
                "CREATE INDEX IF NOT EXISTS idx_users_last_active ON users(last_active)",
                "CREATE INDEX IF NOT EXISTS idx_partners_status ON partners_v2(status)",
                "CREATE INDEX IF NOT EXISTS idx_points_history_type ON points_history(transaction_type)",
                "CREATE INDEX IF NOT EXISTS idx_cards_category_status ON cards_v2(category_id, status)",
            ]
            
            with get_connection() as conn:
                for index_sql in indexes:
                    conn.execute(index_sql)
                conn.commit()
                logger.info("📊 Analytics indexes created")
                
        except Exception as e:
            logger.error(f"❌ Failed to create analytics indexes: {e}")
    
    async def get_user_metrics(self, days: int = 30) -> UserMetrics:
        """Получить метрики пользователей"""
        cache_key = f"analytics:user_metrics:{days}"
        
        # Проверяем кэш
        cached = await cache_service.get(cache_key)
        if cached:
            data = json.loads(cached)
            return UserMetrics(**data)
        
        try:
            from core.database.db_v2 import get_connection
            
            with get_connection() as conn:
                # Общее количество пользователей
                cursor = conn.execute("SELECT COUNT(*) FROM users")
                total_users = cursor.fetchone()[0]
                
                # Активные пользователи за последние N дней
                active_date = datetime.now() - timedelta(days=days)
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM users WHERE last_active >= ?",
                    (active_date.isoformat(),)
                )
                active_users = cursor.fetchone()[0]
                
                # Новые пользователи за период
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM users WHERE created_at >= ?",
                    (active_date.isoformat(),)
                )
                new_users = cursor.fetchone()[0]
                
                # Средние баллы на пользователя
                cursor = conn.execute("SELECT AVG(points_balance) FROM users")
                avg_points = cursor.fetchone()[0] or 0
                
                # Топ пользователи по баллам
                cursor = conn.execute("""
                    SELECT telegram_id, username, first_name, points_balance 
                    FROM users 
                    ORDER BY points_balance DESC 
                    LIMIT 10
                """)
                top_users = [
                    {
                        'telegram_id': row[0],
                        'username': row[1],
                        'first_name': row[2],
                        'points_balance': row[3]
                    }
                    for row in cursor.fetchall()
                ]
                
                # Метрики за разные периоды
                today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                week_ago = datetime.now() - timedelta(days=7)
                month_ago = datetime.now() - timedelta(days=30)
                
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM users WHERE created_at >= ?",
                    (today.isoformat(),)
                )
                new_users_today = cursor.fetchone()[0]
                
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM users WHERE created_at >= ?",
                    (week_ago.isoformat(),)
                )
                new_users_7d = cursor.fetchone()[0]
                
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM users WHERE last_active >= ?",
                    (week_ago.isoformat(),)
                )
                active_users_7d = cursor.fetchone()[0]
                
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM users WHERE last_active >= ?",
                    (month_ago.isoformat(),)
                )
                active_users_30d = cursor.fetchone()[0]
                
                metrics = UserMetrics(
                    total_users=total_users,
                    active_users_7d=active_users_7d,
                    active_users_30d=active_users_30d,
                    new_users_today=new_users_today,
                    new_users_7d=new_users_7d,
                    new_users_30d=new_users,
                    avg_points_per_user=float(avg_points),
                    top_users_by_points=top_users
                )
                
                # Кэшируем результат
                await cache_service.set(cache_key, json.dumps(metrics.__dict__), ex=self.cache_ttl)
                
                return metrics
                
        except Exception as e:
            logger.error(f"❌ Error getting user metrics: {e}")
            return UserMetrics(0, 0, 0, 0, 0, 0, 0.0, [])
    
    async def get_partner_metrics(self) -> PartnerMetrics:
        """Получить метрики партнеров"""
        cache_key = "analytics:partner_metrics"
        
        # Проверяем кэш
        cached = await cache_service.get(cache_key)
        if cached:
            data = json.loads(cached)
            return PartnerMetrics(**data)
        
        try:
            from core.database.db_v2 import get_connection
            
            with get_connection() as conn:
                # Общее количество партнеров
                cursor = conn.execute("SELECT COUNT(*) FROM partners_v2")
                total_partners = cursor.fetchone()[0]
                
                # Партнеры по статусам
                cursor = conn.execute("SELECT status, COUNT(*) FROM partners_v2 GROUP BY status")
                status_counts = dict(cursor.fetchall())
                
                active_partners = status_counts.get('approved', 0)
                pending_partners = status_counts.get('pending', 0)
                rejected_partners = status_counts.get('rejected', 0)
                
                # Среднее количество карт на партнера
                cursor = conn.execute("""
                    SELECT AVG(card_count) FROM (
                        SELECT partner_id, COUNT(*) as card_count 
                        FROM cards_v2 
                        GROUP BY partner_id
                    )
                """)
                avg_cards = cursor.fetchone()[0] or 0
                
                # Топ партнеры по количеству карт
                cursor = conn.execute("""
                    SELECT p.display_name, p.tg_user_id, COUNT(c.id) as card_count
                    FROM partners_v2 p
                    LEFT JOIN cards_v2 c ON p.id = c.partner_id
                    GROUP BY p.id
                    ORDER BY card_count DESC
                    LIMIT 10
                """)
                top_partners = [
                    {
                        'display_name': row[0],
                        'tg_user_id': row[1],
                        'card_count': row[2]
                    }
                    for row in cursor.fetchall()
                ]
                
                metrics = PartnerMetrics(
                    total_partners=total_partners,
                    active_partners=active_partners,
                    pending_partners=pending_partners,
                    approved_partners=active_partners,
                    rejected_partners=rejected_partners,
                    avg_cards_per_partner=float(avg_cards),
                    top_partners_by_cards=top_partners
                )
                
                # Кэшируем результат
                await cache_service.set(cache_key, json.dumps(metrics.__dict__), ex=self.cache_ttl)
                
                return metrics
                
        except Exception as e:
            logger.error(f"❌ Error getting partner metrics: {e}")
            return PartnerMetrics(0, 0, 0, 0, 0, 0.0, [])
    
    async def get_transaction_metrics(self, days: int = 30) -> TransactionMetrics:
        """Получить метрики транзакций"""
        cache_key = f"analytics:transaction_metrics:{days}"
        
        # Проверяем кэш
        cached = await cache_service.get(cache_key)
        if cached:
            data = json.loads(cached)
            return TransactionMetrics(**data)
        
        try:
            from core.database.db_v2 import get_connection
            
            with get_connection() as conn:
                # Общее количество транзакций
                cursor = conn.execute("SELECT COUNT(*) FROM points_history")
                total_transactions = cursor.fetchone()[0]
                
                # Транзакции за период
                period_start = datetime.now() - timedelta(days=days)
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM points_history WHERE created_at >= ?",
                    (period_start.isoformat(),)
                )
                period_transactions = cursor.fetchone()[0]
                
                # Транзакции за сегодня
                today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM points_history WHERE created_at >= ?",
                    (today.isoformat(),)
                )
                transactions_today = cursor.fetchone()[0]
                
                # Транзакции за неделю
                week_ago = datetime.now() - timedelta(days=7)
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM points_history WHERE created_at >= ?",
                    (week_ago.isoformat(),)
                )
                transactions_7d = cursor.fetchone()[0]
                
                # Общие баллы
                cursor = conn.execute("""
                    SELECT 
                        SUM(CASE WHEN change_amount > 0 THEN change_amount ELSE 0 END) as earned,
                        SUM(CASE WHEN change_amount < 0 THEN ABS(change_amount) ELSE 0 END) as spent
                    FROM points_history
                """)
                row = cursor.fetchone()
                total_points_earned = row[0] or 0
                total_points_spent = row[1] or 0
                
                # Среднее значение транзакции
                cursor = conn.execute("SELECT AVG(ABS(change_amount)) FROM points_history")
                avg_transaction_value = cursor.fetchone()[0] or 0
                
                # Топ типы транзакций
                cursor = conn.execute("""
                    SELECT transaction_type, COUNT(*) as count
                    FROM points_history
                    GROUP BY transaction_type
                    ORDER BY count DESC
                    LIMIT 10
                """)
                top_transaction_types = [
                    {'type': row[0], 'count': row[1]}
                    for row in cursor.fetchall()
                ]
                
                metrics = TransactionMetrics(
                    total_transactions=total_transactions,
                    transactions_today=transactions_today,
                    transactions_7d=transactions_7d,
                    transactions_30d=period_transactions,
                    total_points_earned=total_points_earned,
                    total_points_spent=total_points_spent,
                    avg_transaction_value=float(avg_transaction_value),
                    top_transaction_types=top_transaction_types
                )
                
                # Кэшируем результат
                await cache_service.set(cache_key, json.dumps(metrics.__dict__), ex=self.cache_ttl)
                
                return metrics
                
        except Exception as e:
            logger.error(f"❌ Error getting transaction metrics: {e}")
            return TransactionMetrics(0, 0, 0, 0, 0, 0, 0.0, [])
    
    async def get_business_metrics(self, days: int = 30) -> BusinessMetrics:
        """Получить бизнес-метрики"""
        cache_key = f"analytics:business_metrics:{days}"
        
        # Проверяем кэш
        cached = await cache_service.get(cache_key)
        if cached:
            data = json.loads(cached)
            return BusinessMetrics(**data)
        
        try:
            from core.database.db_v2 import get_connection
            
            with get_connection() as conn:
                # Топ категории по количеству карт
                cursor = conn.execute("""
                    SELECT c.name, COUNT(cards.id) as card_count
                    FROM categories_v2 c
                    LEFT JOIN cards_v2 cards ON c.id = cards.category_id
                    WHERE c.is_active = 1
                    GROUP BY c.id
                    ORDER BY card_count DESC
                    LIMIT 10
                """)
                top_categories = [
                    {'name': row[0], 'card_count': row[1]}
                    for row in cursor.fetchall()
                ]
                
                # Базовые метрики (заглушки для демонстрации)
                metrics = BusinessMetrics(
                    revenue_today=0.0,  # TODO: Реализовать расчет выручки
                    revenue_7d=0.0,
                    revenue_30d=0.0,
                    conversion_rate=0.0,  # TODO: Реализовать расчет конверсии
                    retention_rate_7d=0.0,  # TODO: Реализовать расчет удержания
                    retention_rate_30d=0.0,
                    avg_session_duration=0.0,  # TODO: Реализовать расчет времени сессии
                    top_categories=top_categories
                )
                
                # Кэшируем результат
                await cache_service.set(cache_key, json.dumps(metrics.__dict__), ex=self.cache_ttl)
                
                return metrics
                
        except Exception as e:
            logger.error(f"❌ Error getting business metrics: {e}")
            return BusinessMetrics(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, [])
    
    async def get_dashboard_data(self) -> Dict[str, Any]:
        """Получить данные для дашборда"""
        try:
            # Получаем все метрики параллельно
            user_metrics, partner_metrics, transaction_metrics, business_metrics = await asyncio.gather(
                self.get_user_metrics(),
                self.get_partner_metrics(),
                self.get_transaction_metrics(),
                self.get_business_metrics()
            )
            
            return {
                'users': user_metrics.__dict__,
                'partners': partner_metrics.__dict__,
                'transactions': transaction_metrics.__dict__,
                'business': business_metrics.__dict__,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting dashboard data: {e}")
            return {}


# Глобальный экземпляр сервиса
analytics_service = AnalyticsService()


__all__ = [
    'AnalyticsService',
    'analytics_service',
    'UserMetrics',
    'PartnerMetrics', 
    'TransactionMetrics',
    'BusinessMetrics'
]
