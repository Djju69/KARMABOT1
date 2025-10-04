"""
Сервис оптимизации производительности
Включает кэширование запросов, пулы соединений и мониторинг производительности
"""
import asyncio
import time
import logging
from typing import Dict, Any, Optional, List, Callable
from functools import wraps
from datetime import datetime, timedelta
import json

from .cache import cache_service

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """Мониторинг производительности запросов"""
    
    def __init__(self):
        self.metrics = {}
        self.slow_queries = []
        self.threshold_ms = 1000  # Порог медленных запросов в мс
    
    def record_query(self, query_name: str, duration_ms: float, params: Dict = None):
        """Записать метрику запроса"""
        if query_name not in self.metrics:
            self.metrics[query_name] = {
                'count': 0,
                'total_time': 0,
                'avg_time': 0,
                'min_time': float('inf'),
                'max_time': 0,
                'last_executed': None
            }
        
        metric = self.metrics[query_name]
        metric['count'] += 1
        metric['total_time'] += duration_ms
        metric['avg_time'] = metric['total_time'] / metric['count']
        metric['min_time'] = min(metric['min_time'], duration_ms)
        metric['max_time'] = max(metric['max_time'], duration_ms)
        metric['last_executed'] = datetime.now()
        
        # Записываем медленные запросы
        if duration_ms > self.threshold_ms:
            self.slow_queries.append({
                'query': query_name,
                'duration_ms': duration_ms,
                'params': params,
                'timestamp': datetime.now()
            })
            logger.warning(f"🐌 Медленный запрос: {query_name} - {duration_ms:.2f}ms")
    
    def get_stats(self) -> Dict[str, Any]:
        """Получить статистику производительности"""
        return {
            'metrics': self.metrics,
            'slow_queries_count': len(self.slow_queries),
            'recent_slow_queries': self.slow_queries[-10:],  # Последние 10 медленных запросов
            'total_queries': sum(m['count'] for m in self.metrics.values())
        }


class QueryOptimizer:
    """Оптимизатор запросов с кэшированием"""
    
    def __init__(self):
        self.monitor = PerformanceMonitor()
        self.cache_ttl = {
            'user_profile': 300,      # 5 минут
            'partner_info': 600,       # 10 минут
            'categories': 1800,        # 30 минут
            'loyalty_config': 900,     # 15 минут
            'tariffs': 3600,          # 1 час
            'translations': 7200,     # 2 часа
            'catalog': 30,            # 30 секунд для каталога
        }
    
    def cached_query(self, cache_key: str, ttl: int = 300):
        """Декоратор для кэширования запросов"""
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Создаем уникальный ключ на основе параметров
                if cache_key == "catalog":
                    # Для каталога создаем ключ на основе параметров
                    # Получаем параметры из args и kwargs
                    import inspect
                    sig = inspect.signature(func)
                    bound_args = sig.bind(*args, **kwargs)
                    bound_args.apply_defaults()
                    
                    slug = bound_args.arguments.get('slug', 'all')
                    sub_slug = bound_args.arguments.get('sub_slug', 'all')
                    page = bound_args.arguments.get('page', 1)
                    city_id = bound_args.arguments.get('city_id', 'none')
                    unique_key = f"catalog:{slug}:{sub_slug}:{page}:{city_id}"
                    # Используем короткий TTL для каталога
                    ttl = self.cache_ttl.get('catalog', 30)
                else:
                    unique_key = cache_key
                
                # Проверяем кэш
                cached_result = await cache_service.get(unique_key)
                if cached_result:
                    logger.warning(f"🔧 CACHE HIT: {unique_key} - возвращаем кэшированный результат")
                    return json.loads(cached_result)
                
                # Выполняем запрос
                logger.warning(f"🔧 CACHE MISS: {unique_key} - выполняем функцию")
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    duration_ms = (time.time() - start_time) * 1000
                    
                    # Записываем метрику
                    self.monitor.record_query(func.__name__, duration_ms, kwargs)
                    
                    # Сохраняем в кэш
                    await cache_service.set(unique_key, json.dumps(result), ex=ttl)
                    logger.debug(f"💾 Cached: {unique_key} (TTL: {ttl}s)")
                    
                    return result
                except Exception as e:
                    duration_ms = (time.time() - start_time) * 1000
                    self.monitor.record_query(func.__name__, duration_ms, {'error': str(e)})
                    raise
            
            return wrapper
        return decorator
    
    def batch_query(self, queries: List[Callable], batch_size: int = 10):
        """Выполнение запросов батчами для оптимизации"""
        async def execute_batch():
            results = []
            for i in range(0, len(queries), batch_size):
                batch = queries[i:i + batch_size]
                batch_results = await asyncio.gather(*batch, return_exceptions=True)
                results.extend(batch_results)
            return results
        return execute_batch


class DatabaseOptimizer:
    """Оптимизатор базы данных"""
    
    def __init__(self):
        self.connection_pools = {}
        self.query_cache = {}
    
    async def optimize_connection_pool(self, service_name: str, max_connections: int = 20):
        """Оптимизация пула соединений"""
        try:
            if service_name == 'postgresql':
                from core.database.postgresql_service import get_postgresql_service
                service = get_postgresql_service()
                await service.init_pool()
                logger.info(f"🔧 Optimized PostgreSQL connection pool: max_connections={max_connections}")
            
            elif service_name == 'redis':
                from core.services.cache import get_cache_service
                cache = await get_cache_service()
                await cache.ping()
                logger.info(f"🔧 Optimized Redis connection")
            
        except Exception as e:
            logger.error(f"❌ Failed to optimize {service_name} connection pool: {e}")
    
    def create_indexes(self):
        """Создание индексов для оптимизации запросов"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id)",
            "CREATE INDEX IF NOT EXISTS idx_partners_tg_user_id ON partners_v2(tg_user_id)",
            "CREATE INDEX IF NOT EXISTS idx_cards_category_id ON cards_v2(category_id)",
            "CREATE INDEX IF NOT EXISTS idx_cards_status ON cards_v2(status)",
            "CREATE INDEX IF NOT EXISTS idx_points_history_user_id ON points_history(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_points_history_created_at ON points_history(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_categories_active ON categories_v2(is_active)",
            "CREATE INDEX IF NOT EXISTS idx_tariffs_active ON tariffs(is_active)",
        ]
        
        try:
            from core.database.db_adapter import db_v2
            
            # Используем правильный способ получения соединения
            if db_v2.use_postgresql:
                # Для PostgreSQL используем синхронные методы
                for index_sql in indexes:
                    db_v2.postgresql_service.execute_sync(index_sql)
                logger.info("🔧 Database indexes created successfully")
            else:
                # Для SQLite используем обычное соединение
                conn = db_v2.sqlite_service.get_connection()
                for index_sql in indexes:
                    conn.execute(index_sql)
                conn.commit()
                logger.info("🔧 Database indexes created successfully")
        except Exception as e:
            logger.error(f"❌ Failed to create database indexes: {e}")
    
    async def analyze_query_performance(self):
        """Анализ производительности запросов"""
        try:
            from core.database.db_adapter import db_v2
            
            # Получаем статистику таблиц
            if db_v2.use_postgresql:
                # Для PostgreSQL используем синхронные методы
                tables_query = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
                tables_result = db_v2.postgresql_service.fetch_all_sync(tables_query)
                tables = [row['table_name'] for row in tables_result]
                
                analysis = {}
                for table in tables:
                    count_result = db_v2.postgresql_service.fetch_one_sync(f"SELECT COUNT(*) FROM {table}")
                    count = count_result['count'] if count_result else 0
                    analysis[table] = {'rows': count}
                
                logger.info(f"📊 Database analysis: {analysis}")
                return analysis
            else:
                # Для SQLite используем обычное соединение
                conn = db_v2.sqlite_service.get_connection()
                cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                analysis = {}
                for table in tables:
                    cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    analysis[table] = {'rows': count}
                
                logger.info(f"📊 Database analysis: {analysis}")
                return analysis
                
        except Exception as e:
            logger.error(f"❌ Failed to analyze database performance: {e}")
            return {}


class PerformanceService:
    """Главный сервис оптимизации производительности"""
    
    def __init__(self):
        self.optimizer = QueryOptimizer()
        self.db_optimizer = DatabaseOptimizer()
        self.monitor = PerformanceMonitor()
        self.is_initialized = False
    
    async def initialize(self):
        """Инициализация сервиса оптимизации"""
        if self.is_initialized:
            return
        
        try:
            # Оптимизируем соединения
            await self.db_optimizer.optimize_connection_pool('postgresql')
            await self.db_optimizer.optimize_connection_pool('redis')
            
            # Создаем индексы
            self.db_optimizer.create_indexes()
            
            # Анализируем производительность
            await self.db_optimizer.analyze_query_performance()
            
            self.is_initialized = True
            logger.info("🚀 Performance service initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize performance service: {e}")
    
    async def get_performance_stats(self) -> Dict[str, Any]:
        """Получить статистику производительности"""
        stats = self.monitor.get_stats()
        stats['is_initialized'] = self.is_initialized
        stats['cache_ttl_config'] = self.optimizer.cache_ttl
        return stats
    
    async def optimize_slow_queries(self):
        """Оптимизация медленных запросов"""
        slow_queries = self.monitor.slow_queries
        if not slow_queries:
            logger.info("✅ No slow queries found")
            return
        
        logger.warning(f"🐌 Found {len(slow_queries)} slow queries, optimizing...")
        
        # Здесь можно добавить автоматическую оптимизацию
        # Например, создание дополнительных индексов или изменение запросов
        
        # Очищаем список медленных запросов после оптимизации
        self.monitor.slow_queries.clear()
        logger.info("✅ Slow queries optimized")


# Глобальный экземпляр сервиса
performance_service = PerformanceService()


# Декораторы для удобного использования
def cached_query(cache_key: str, ttl: int = 300):
    """Декоратор для кэширования запросов"""
    return performance_service.optimizer.cached_query(cache_key, ttl)


def monitor_performance(func_name: str = None):
    """Декоратор для мониторинга производительности"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                performance_service.monitor.record_query(
                    func_name or func.__name__, 
                    duration_ms, 
                    kwargs
                )
                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                performance_service.monitor.record_query(
                    func_name or func.__name__, 
                    duration_ms, 
                    {'error': str(e)}
                )
                raise
        return wrapper
    return decorator


__all__ = [
    'PerformanceService',
    'performance_service',
    'cached_query',
    'monitor_performance',
    'QueryOptimizer',
    'DatabaseOptimizer',
    'PerformanceMonitor'
]
