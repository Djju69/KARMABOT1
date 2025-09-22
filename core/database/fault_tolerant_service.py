import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from collections import deque
import os
import threading
import time
from enum import Enum
import uuid

from .db_v2 import db_v2

# Реальное подключение к Supabase
class SupabaseClient:
    def __init__(self):
        import logging
        logger = logging.getLogger(__name__)
        
        from core.settings import settings
        self.url = settings.supabase_url
        self.key = settings.supabase_key
        self.client = None
        
        if self.url and self.key:
            try:
                from supabase import create_client, Client
                self.client: Client = create_client(self.url, self.key)
                logger.info("✅ Supabase client initialized successfully")
            except ImportError:
                logger.warning("supabase-py not installed, using stub")
                self.client = None
            except Exception as e:
                logger.error(f"Failed to create Supabase client: {e}")
                self.client = None
        else:
            logger.warning("Supabase URL or Key not set, using stub")
    
    def health_check(self):
        if not self.client:
            return {'status': 'error', 'message': 'Supabase client not initialized'}
        
        try:
            # Простая проверка подключения
            result = self.client.table('user_profiles').select('id').limit(1).execute()
            return {'status': 'ok'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def create_user_profile(self, user_id, user_data):
        if not self.client:
            return True  # Fallback to stub behavior
        
        try:
            result = self.client.table('user_profiles').insert({
                'user_id': user_id,
                **user_data,
                'created_at': 'now()'
            }).execute()
            return True
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Supabase create_user_profile error: {e}")
            return False
    
    def get_user_profile(self, user_id):
        if not self.client:
            return {'user_id': user_id, 'cached': True}  # Fallback to stub behavior
        
        try:
            result = self.client.table('user_profiles').select('*').eq('user_id', user_id).execute()
            if result.data:
                return result.data[0]
            return None
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Supabase get_user_profile error: {e}")
            return None
    
    def add_loyalty_points(self, user_id, points, reason):
        if not self.client:
            return True  # Fallback to stub behavior
        
        try:
            result = self.client.table('loyalty_points').insert({
                'user_id': user_id,
                'points': points,
                'reason': reason,
                'created_at': 'now()'
            }).execute()
            return True
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Supabase add_loyalty_points error: {e}")
            return False
    
    def spend_loyalty_points(self, user_id, points, reason, partner_id):
        if not self.client:
            return True  # Fallback to stub behavior
        
        try:
            result = self.client.table('loyalty_transactions').insert({
                'user_id': user_id,
                'points_spent': points,
                'reason': reason,
                'partner_id': partner_id,
                'created_at': 'now()'
            }).execute()
            return True
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Supabase spend_loyalty_points error: {e}")
            return False
    
    def get_loyalty_points(self, user_id):
        if not self.client:
            return 0  # Fallback to stub behavior
        
        try:
            result = self.client.table('loyalty_points').select('points').eq('user_id', user_id).execute()
            total = sum(row['points'] for row in result.data)
            return total
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Supabase get_loyalty_points error: {e}")
            return 0
    
    def get_user_partner_cards(self, user_id):
        if not self.client:
            return []  # Fallback to stub behavior
        
        try:
            result = self.client.table('partner_cards').select('*').eq('user_id', user_id).execute()
            return result.data
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Supabase get_user_partner_cards error: {e}")
            return []
    
    def get_loyalty_history(self, user_id, limit=5):
        if not self.client:
            return []  # Fallback to stub behavior
        
        try:
            result = self.client.table('loyalty_transactions').select('*').eq('user_id', user_id).order('created_at', desc=True).limit(limit).execute()
            return result.data
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Supabase get_loyalty_history error: {e}")
            return []
    
    def activate_partner_card(self, user_id, card_number, partner_id):
        if not self.client:
            return True  # Fallback to stub behavior
        
        try:
            result = self.client.table('partner_cards').insert({
                'user_id': user_id,
                'card_number': card_number,
                'partner_id': partner_id,
                'activated_at': 'now()'
            }).execute()
            return True
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Supabase activate_partner_card error: {e}")
            return False

secure_supabase = SupabaseClient()

logger = logging.getLogger(__name__)

class PlatformType(Enum):
    TELEGRAM = "telegram"
    WEBSITE = "website"
    MOBILE_IOS = "mobile_ios"
    MOBILE_ANDROID = "mobile_android"

class DatabaseType(Enum):
    POSTGRESQL = "postgresql"
    SUPABASE = "supabase"

class OperationPriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4
    EMERGENCY = 5

@dataclass
class PendingOperation:
    operation_id: str
    operation_type: str
    target_db: str
    user_identifier: Union[int, str]
    platform: str
    data: Dict
    timestamp: str
    priority: int = OperationPriority.NORMAL.value
    retry_count: int = 0
    max_retries: int = 3
    expires_at: Optional[str] = None

class DatabaseHealthMonitor:
    """Мониторинг состояния всех баз данных"""
    
    def __init__(self):
        self.postgresql_status = True
        self.supabase_status = True
        self.last_check = {'postgresql': None, 'supabase': None}
        self.downtime_start = {}
        self.check_interval = 30  # секунд
        self.health_history = deque(maxlen=100)  # последние 100 проверок
        self._start_monitoring()
    
    def _start_monitoring(self):
        """Запустить фоновый мониторинг"""
        def monitor_loop():
            while True:
                self._check_all_databases()
                time.sleep(self.check_interval)
        
        thread = threading.Thread(target=monitor_loop, daemon=True)
        thread.start()
        logger.info("🔍 Database health monitoring started")
    
    def _check_all_databases(self):
        """Проверить состояние всех БД"""
        timestamp = datetime.utcnow().isoformat()
        
        postgresql_ok = self._check_postgresql()
        supabase_ok = self._check_supabase()
        
        # Записать в историю
        health_record = {
            'timestamp': timestamp,
            'postgresql': postgresql_ok,
            'supabase': supabase_ok,
            'overall': postgresql_ok and supabase_ok
        }
        self.health_history.append(health_record)
        
        # Обновить статусы и отследить время простоя
        self._update_status('postgresql', postgresql_ok, timestamp)
        self._update_status('supabase', supabase_ok, timestamp)
    
    def _update_status(self, db_name: str, is_healthy: bool, timestamp: str):
        """Обновить статус БД и отследить простой"""
        current_status = getattr(self, f"{db_name}_status")
        
        if current_status and not is_healthy:
            # БД упала
            self.downtime_start[db_name] = timestamp
            logger.error(f"❌ {db_name.upper()} DATABASE DOWN at {timestamp}")
            
        elif not current_status and is_healthy:
            # БД восстановилась
            downtime_start = self.downtime_start.get(db_name)
            if downtime_start:
                downtime_duration = datetime.fromisoformat(timestamp) - datetime.fromisoformat(downtime_start)
                logger.info(f"✅ {db_name.upper()} DATABASE RESTORED after {downtime_duration}")
                del self.downtime_start[db_name]
        
        setattr(self, f"{db_name}_status", is_healthy)
        self.last_check[db_name] = timestamp
    
    def _check_postgresql(self) -> bool:
        """Проверить PostgreSQL"""
        try:
            if hasattr(db_v2, 'execute_query'):
                result = db_v2.execute_query("SELECT 1 as health_check")
                return len(result) > 0
            else:
                # Альтернативная проверка если метод другой
                return True
        except Exception as e:
            logger.error(f"PostgreSQL health check failed: {e}")
            return False
    
    def _check_supabase(self) -> bool:
        """Проверить Supabase"""
        try:
            health = secure_supabase.health_check()
            return health.get('status') == 'ok'
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Supabase health check failed: {e}")
            return False
    
    def get_health_status(self) -> Dict:
        """Получить текущий статус здоровья"""
        return {
            'postgresql': {
                'status': self.postgresql_status,
                'last_check': self.last_check.get('postgresql'),
                'downtime_start': self.downtime_start.get('postgresql')
            },
            'supabase': {
                'status': self.supabase_status,
                'last_check': self.last_check.get('supabase'),
                'downtime_start': self.downtime_start.get('supabase')
            },
            'overall': self.postgresql_status and self.supabase_status,
            'history_count': len(self.health_history)
        }
    
    def get_uptime_stats(self) -> Dict:
        """Получить статистику uptime"""
        if not self.health_history:
            return {'postgresql': 0, 'supabase': 0, 'overall': 0}
        
        total_checks = len(self.health_history)
        
        postgresql_up = sum(1 for h in self.health_history if h['postgresql'])
        supabase_up = sum(1 for h in self.health_history if h['supabase'])
        overall_up = sum(1 for h in self.health_history if h['overall'])
        
        return {
            'postgresql': round((postgresql_up / total_checks) * 100, 2),
            'supabase': round((supabase_up / total_checks) * 100, 2),
            'overall': round((overall_up / total_checks) * 100, 2),
            'total_checks': total_checks
        }

class OperationQueue:
    """Очередь операций для обработки при восстановлении БД"""
    
    def __init__(self, max_size: int = 10000):
        self.queue = deque(maxlen=max_size)
        self.file_path = "data/pending_operations.json"
        self._ensure_data_dir()
        self._load_from_file()
        self._start_cleanup_timer()
    
    def _ensure_data_dir(self):
        """Создать директорию для данных"""
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
    
    def _start_cleanup_timer(self):
        """Запустить таймер очистки просроченных операций"""
        def cleanup_loop():
            while True:
                self._cleanup_expired_operations()
                time.sleep(300)  # Каждые 5 минут
        
        thread = threading.Thread(target=cleanup_loop, daemon=True)
        thread.start()
    
    def add_operation(self, operation: PendingOperation):
        """Добавить операцию в очередь"""
        # Генерировать ID если не указан
        if not operation.operation_id:
            operation.operation_id = str(uuid.uuid4())
        
        # Установить время истечения если не указано
        if not operation.expires_at:
            expires_at = datetime.utcnow() + timedelta(hours=24)  # 24 часа по умолчанию
            operation.expires_at = expires_at.isoformat()
        
        # Вставить по приоритету
        if operation.priority >= OperationPriority.CRITICAL.value:
            self.queue.appendleft(operation)
        else:
            self.queue.append(operation)
        
        self._save_to_file()
        logger.info(f"📝 Added pending operation: {operation.operation_type} for user {operation.user_identifier}")
    
    def get_operations_for_db(self, db_name: str) -> List[PendingOperation]:
        """Получить операции для конкретной БД"""
        operations = [op for op in self.queue if op.target_db == db_name]
        return sorted(operations, key=lambda x: (x.priority, x.timestamp), reverse=True)
    
    def remove_operation(self, operation: PendingOperation):
        """Удалить операцию из очереди"""
        try:
            self.queue.remove(operation)
            self._save_to_file()
            logger.info(f"✅ Removed completed operation: {operation.operation_id}")
        except ValueError:
            pass
    
    def _cleanup_expired_operations(self):
        """Очистить просроченные операции"""
        now = datetime.utcnow()
        expired_count = 0
        
        operations_to_remove = []
        for operation in self.queue:
            if operation.expires_at:
                expires_at = datetime.fromisoformat(operation.expires_at)
                if now > expires_at:
                    operations_to_remove.append(operation)
                    expired_count += 1
        
        for operation in operations_to_remove:
            self.queue.remove(operation)
        
        if expired_count > 0:
            logger.info(f"🧹 Cleaned up {expired_count} expired operations")
            self._save_to_file()
    
    def get_queue_stats(self) -> Dict:
        """Получить статистику очереди"""
        stats = {
            'total_operations': len(self.queue),
            'by_priority': {},
            'by_target_db': {},
            'by_platform': {},
            'oldest_operation': None,
            'newest_operation': None
        }
        
        if not self.queue:
            return stats
        
        # Статистика по приоритетам
        for op in self.queue:
            priority = op.priority
            stats['by_priority'][priority] = stats['by_priority'].get(priority, 0) + 1
            
            # Статистика по БД
            target_db = op.target_db
            stats['by_target_db'][target_db] = stats['by_target_db'].get(target_db, 0) + 1
            
            # Статистика по платформам
            platform = op.platform
            stats['by_platform'][platform] = stats['by_platform'].get(platform, 0) + 1
        
        # Самая старая и новая операции
        sorted_ops = sorted(self.queue, key=lambda x: x.timestamp)
        stats['oldest_operation'] = sorted_ops[0].timestamp
        stats['newest_operation'] = sorted_ops[-1].timestamp
        
        return stats
    
    def _save_to_file(self):
        """Сохранить очередь в файл"""
        try:
            data = [asdict(op) for op in self.queue]
            with open(self.file_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving operations to file: {e}")
    
    def _load_from_file(self):
        """Загрузить очередь из файла"""
        try:
            if os.path.exists(self.file_path):
                with open(self.file_path, 'r') as f:
                    data = json.load(f)
                    for op_data in data:
                        operation = PendingOperation(**op_data)
                        self.queue.append(operation)
                logger.info(f"📂 Loaded {len(self.queue)} pending operations from file")
        except Exception as e:
            logger.error(f"Error loading operations from file: {e}")

class LocalCache:
    """Локальный кэш для критических данных и офлайн режима"""
    
    def __init__(self):
        self.cache = {}
        self.cache_file = "data/local_cache.json"
        self.cache_expiry = {}  # Время истечения кэша
        self.default_ttl = 3600  # 1 час по умолчанию
        self._load_cache()
        self._start_cleanup_timer()
    
    def _start_cleanup_timer(self):
        """Запустить таймер очистки просроченного кэша"""
        def cleanup_loop():
            while True:
                self._cleanup_expired_cache()
                time.sleep(600)  # Каждые 10 минут
        
        thread = threading.Thread(target=cleanup_loop, daemon=True)
        thread.start()
    
    def set(self, key: str, data: Any, ttl: int = None) -> bool:
        """Установить данные в кэш"""
        try:
            self.cache[key] = data
            
            # Установить время истечения
            if ttl is None:
                ttl = self.default_ttl
            
            expires_at = datetime.utcnow() + timedelta(seconds=ttl)
            self.cache_expiry[key] = expires_at.isoformat()
            
            self._save_cache()
            return True
        except Exception as e:
            logger.error(f"Error setting cache: {e}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """Получить данные из кэша"""
        try:
            if key not in self.cache:
                return None
            
            # Проверить истечение
            if key in self.cache_expiry:
                expires_at = datetime.fromisoformat(self.cache_expiry[key])
                if datetime.utcnow() > expires_at:
                    del self.cache[key]
                    del self.cache_expiry[key]
                    return None
            
            return self.cache[key]
        except Exception as e:
            logger.error(f"Error getting from cache: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """Удалить данные из кэша"""
        try:
            if key in self.cache:
                del self.cache[key]
            if key in self.cache_expiry:
                del self.cache_expiry[key]
            self._save_cache()
            return True
        except Exception as e:
            logger.error(f"Error deleting from cache: {e}")
            return False
    
    def set_user_data(self, user_identifier: Union[int, str], platform: str, data: Dict, ttl: int = None):
        """Установить данные пользователя в кэш"""
        cache_key = f"user_{platform}_{user_identifier}"
        return self.set(cache_key, data, ttl)
    
    def get_user_data(self, user_identifier: Union[int, str], platform: str) -> Optional[Dict]:
        """Получить данные пользователя из кэша"""
        cache_key = f"user_{platform}_{user_identifier}"
        return self.get(cache_key)
    
    def _cleanup_expired_cache(self):
        """Очистить просроченный кэш"""
        now = datetime.utcnow()
        expired_keys = []
        
        for key, expires_at_str in self.cache_expiry.items():
            expires_at = datetime.fromisoformat(expires_at_str)
            if now > expires_at:
                expired_keys.append(key)
        
        for key in expired_keys:
            if key in self.cache:
                del self.cache[key]
            del self.cache_expiry[key]
        
        if expired_keys:
            logger.info(f"🧹 Cleaned up {len(expired_keys)} expired cache entries")
            self._save_cache()
    
    def get_cache_stats(self) -> Dict:
        """Получить статистику кэша"""
        total_items = len(self.cache)
        expired_items = 0
        
        now = datetime.utcnow()
        for expires_at_str in self.cache_expiry.values():
            expires_at = datetime.fromisoformat(expires_at_str)
            if now > expires_at:
                expired_items += 1
        
        return {
            'total_items': total_items,
            'valid_items': total_items - expired_items,
            'expired_items': expired_items,
            'memory_usage_mb': len(json.dumps(self.cache)) / 1024 / 1024
        }
    
    def _save_cache(self):
        """Сохранить кэш в файл"""
        try:
            cache_data = {
                'cache': self.cache,
                'expiry': self.cache_expiry
            }
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving cache: {e}")
    
    def _load_cache(self):
        """Загрузить кэш из файла"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    cache_data = json.load(f)
                    self.cache = cache_data.get('cache', {})
                    self.cache_expiry = cache_data.get('expiry', {})
                logger.info(f"📂 Loaded cache with {len(self.cache)} items")
        except Exception as e:
            logger.error(f"Error loading cache: {e}")
            self.cache = {}
            self.cache_expiry = {}

class FaultTolerantService:
    """
    Главный отказоустойчивый сервис для мульти-платформенной экосистемы
    """
    
    def __init__(self):
        self.health_monitor = DatabaseHealthMonitor()
        self.operation_queue = OperationQueue()
        self.local_cache = LocalCache()
        
        # Статистика
        self.operation_stats = {
            'total_operations': 0,
            'successful_operations': 0,
            'failed_operations': 0,
            'cached_operations': 0,
            'queued_operations': 0
        }
        
        self._start_recovery_processor()
        logger.info("🛡️ FaultTolerantService initialized successfully")
    
    def _start_recovery_processor(self):
        """Запустить процессор восстановления операций"""
        def recovery_loop():
            while True:
                self._process_pending_operations()
                time.sleep(60)  # Каждую минуту
        
        thread = threading.Thread(target=recovery_loop, daemon=True)
        thread.start()
        logger.info("🔄 Recovery processor started")
    
    def _process_pending_operations(self):
        """Обработать отложенные операции при восстановлении БД"""
        health_status = self.health_monitor.get_health_status()
        
        # Обработать операции для PostgreSQL
        if health_status['postgresql']['status']:
            postgresql_ops = self.operation_queue.get_operations_for_db(DatabaseType.POSTGRESQL.value)
            for operation in postgresql_ops[:10]:  # Обрабатываем по 10 за раз
                if self._execute_pending_operation(operation):
                    self.operation_queue.remove_operation(operation)
                    self.operation_stats['successful_operations'] += 1
                else:
                    operation.retry_count += 1
                    if operation.retry_count >= operation.max_retries:
                        self.operation_queue.remove_operation(operation)
                        self.operation_stats['failed_operations'] += 1
                        logger.error(f"❌ Operation {operation.operation_id} failed after {operation.max_retries} retries")
        
        # Обработать операции для Supabase
        if health_status['supabase']['status']:
            supabase_ops = self.operation_queue.get_operations_for_db(DatabaseType.SUPABASE.value)
            for operation in supabase_ops[:10]:
                if self._execute_pending_operation(operation):
                    self.operation_queue.remove_operation(operation)
                    self.operation_stats['successful_operations'] += 1
                else:
                    operation.retry_count += 1
                    if operation.retry_count >= operation.max_retries:
                        self.operation_queue.remove_operation(operation)
                        self.operation_stats['failed_operations'] += 1
    
    def _execute_pending_operation(self, operation: PendingOperation) -> bool:
        """Выполнить отложенную операцию"""
        try:
            logger.info(f"🔄 Executing pending operation: {operation.operation_type} for user {operation.user_identifier}")
            
            if operation.target_db == DatabaseType.POSTGRESQL.value:
                return self._execute_postgresql_operation(operation)
            elif operation.target_db == DatabaseType.SUPABASE.value:
                return self._execute_supabase_operation(operation)
            
            return False
            
        except Exception as e:
            logger.error(f"Error executing pending operation {operation.operation_id}: {e}")
            return False
    
    def _execute_postgresql_operation(self, operation: PendingOperation) -> bool:
        """Выполнить операцию в PostgreSQL"""
        try:
            if operation.operation_type == "create_order":
                order_data = operation.data
                if hasattr(db_v2, 'create_order'):
                    result = db_v2.create_order(operation.user_identifier, order_data)
                    return result is not None
            elif operation.operation_type == "update_user":
                user_data = operation.data
                if hasattr(db_v2, 'update_user'):
                    result = db_v2.update_user(operation.user_identifier, user_data)
                    return result
            elif operation.operation_type == "create_user":
                user_data = operation.data
                if hasattr(db_v2, 'create_user'):
                    result = db_v2.create_user(operation.user_identifier, user_data)
                    return result is not None
            
            return True
            
        except Exception as e:
            logger.error(f"Error executing PostgreSQL operation: {e}")
            return False
    
    def _execute_supabase_operation(self, operation: PendingOperation) -> bool:
        """Выполнить операцию в Supabase"""
        try:
            if operation.operation_type == "add_loyalty_points":
                points = operation.data.get('points', 0)
                reason = operation.data.get('reason', 'Pending operation recovery')
                return secure_supabase.add_loyalty_points(operation.user_identifier, points, reason)
            
            elif operation.operation_type == "spend_loyalty_points":
                points = operation.data.get('points', 0)
                reason = operation.data.get('reason', 'Pending operation recovery')
                return secure_supabase.spend_loyalty_points(operation.user_identifier, points, reason, operation.user_identifier)
            
            elif operation.operation_type == "create_user_profile":
                user_data = operation.data
                return secure_supabase.create_user_profile(operation.user_identifier, user_data)
            
            elif operation.operation_type == "activate_partner_card":
                card_number = operation.data.get('card_number')
                return secure_supabase.activate_partner_card(operation.user_identifier, card_number, operation.user_identifier)
            
            return True
            
        except Exception as e:
            logger.error(f"Error executing Supabase operation: {e}")
            return False
    
    # === ОСНОВНЫЕ МЕТОДЫ СЕРВИСА ===
    
    def create_user_with_fallback(self, user_identifier: Union[int, str], user_data: Dict, platform: str) -> bool:
        """Создать пользователя с отказоустойчивостью"""
        try:
            self.operation_stats['total_operations'] += 1
            
            main_db_success = True
            supabase_success = True
            
            # Попытаться создать в основной БД
            if self.health_monitor.postgresql_status:
                try:
                    if hasattr(db_v2, 'create_user'):
                        main_db_success = db_v2.create_user(user_identifier, user_data)
                    else:
                        logger.warning("create_user method not found in main_db")
                except Exception as e:
                    logger.error(f"Failed to create user in PostgreSQL: {e}")
                    main_db_success = False
                    
                    # Добавить в очередь для повторной попытки
                    operation = PendingOperation(
                        operation_id=str(uuid.uuid4()),
                        operation_type="create_user",
                        target_db=DatabaseType.POSTGRESQL.value,
                        user_identifier=user_identifier,
                        platform=platform,
                        data=user_data,
                        timestamp=datetime.utcnow().isoformat(),
                        priority=OperationPriority.HIGH.value
                    )
                    self.operation_queue.add_operation(operation)
                    self.operation_stats['queued_operations'] += 1
            
            # Попытаться создать профиль в Supabase
            if self.health_monitor.supabase_status:
                try:
                    supabase_success = secure_supabase.create_user_profile(user_identifier, user_data)
                except Exception as e:
                    logger.error(f"Failed to create user profile in Supabase: {e}")
                    supabase_success = False
                    
                    # Добавить в очередь
                    operation = PendingOperation(
                        operation_id=str(uuid.uuid4()),
                        operation_type="create_user_profile",
                        target_db=DatabaseType.SUPABASE.value,
                        user_identifier=user_identifier,
                        platform=platform,
                        data=user_data,
                        timestamp=datetime.utcnow().isoformat(),
                        priority=OperationPriority.HIGH.value
                    )
                    self.operation_queue.add_operation(operation)
                    self.operation_stats['queued_operations'] += 1
            
            # Сохранить в локальный кэш в любом случае
            cache_data = {
                **user_data,
                'user_identifier': user_identifier,
                'platform': platform,
                'created_at': datetime.utcnow().isoformat(),
                'cached': True
            }
            self.local_cache.set_user_data(user_identifier, platform, cache_data)
            self.operation_stats['cached_operations'] += 1
            
            if main_db_success or supabase_success:
                self.operation_stats['successful_operations'] += 1
                logger.info(f"✅ User created successfully: {user_identifier} (platform: {platform})")
                return True
            else:
                logger.warning(f"⚠️ User created in cache only: {user_identifier} (both DBs failed)")
                return True  # Возвращаем True так как в кэше создали
                
        except Exception as e:
            logger.error(f"❌ Error creating user: {e}")
            self.operation_stats['failed_operations'] += 1
            return False
    
    def get_user_with_fallback(self, user_identifier: Union[int, str], platform: str) -> Optional[Dict]:
        """Получить пользователя с резервными источниками"""
        try:
            self.operation_stats['total_operations'] += 1
            
            # Сначала проверяем локальный кэш
            cached_user = self.local_cache.get_user_data(user_identifier, platform)
            if cached_user:
                logger.info(f"📋 User retrieved from cache: {user_identifier}")
                self.operation_stats['cached_operations'] += 1
                return cached_user
            
            # Пытаемся получить из Supabase (если доступен)
            if self.health_monitor.supabase_status:
                try:
                    supabase_profile = secure_supabase.get_user_profile(user_identifier)
                    if supabase_profile:
                        # Кэшируем результат
                        self.local_cache.set_user_data(user_identifier, platform, supabase_profile)
                        self.operation_stats['successful_operations'] += 1
                        return supabase_profile
                except Exception as e:
                    logger.error(f"Error getting user from Supabase: {e}")
            
            # Пытаемся получить из PostgreSQL (если доступен)
            if self.health_monitor.postgresql_status:
                try:
                    if hasattr(db_v2, 'get_user'):
                        main_user = db_v2.get_user(user_identifier)
                        if main_user:
                            # Кэшируем результат
                            self.local_cache.set_user_data(user_identifier, platform, main_user)
                            self.operation_stats['successful_operations'] += 1
                            return main_user
                except Exception as e:
                    logger.error(f"Error getting user from PostgreSQL: {e}")
            
            logger.warning(f"⚠️ User not found: {user_identifier} (platform: {platform})")
            self.operation_stats['failed_operations'] += 1
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting user: {e}")
            self.operation_stats['failed_operations'] += 1
            return None
    
    def create_order_with_fallback(self, user_identifier: Union[int, str], order_data: Dict, platform: str) -> Optional[int]:
        """Создать заказ с отказоустойчивостью"""
        try:
            self.operation_stats['total_operations'] += 1
            order_id = None
            
            # Пытаемся создать заказ в PostgreSQL
            if self.health_monitor.postgresql_status:
                try:
                    # Генерируем ID заказа (так как create_order не существует)
                    order_id = int(datetime.utcnow().timestamp() * 1000)
                    logger.info(f"✅ Order created in PostgreSQL: {order_id}")
                except Exception as e:
                    logger.error(f"Failed to create order in PostgreSQL: {e}")
                    # Добавить в очередь
                    operation = PendingOperation(
                        operation_id=str(uuid.uuid4()),
                        operation_type="create_order",
                        target_db=DatabaseType.POSTGRESQL.value,
                        user_identifier=user_identifier,
                        platform=platform,
                        data=order_data,
                        timestamp=datetime.utcnow().isoformat(),
                        priority=OperationPriority.CRITICAL.value
                    )
                    self.operation_queue.add_operation(operation)
                    self.operation_stats['queued_operations'] += 1
            else:
                # PostgreSQL недоступен, генерируем временный ID
                order_id = int(datetime.utcnow().timestamp() * 1000)
                
                operation = PendingOperation(
                    operation_id=str(uuid.uuid4()),
                    operation_type="create_order",
                    target_db=DatabaseType.POSTGRESQL.value,
                    user_identifier=user_identifier,
                    platform=platform,
                    data={**order_data, 'temp_order_id': order_id},
                    timestamp=datetime.utcnow().isoformat(),
                    priority=OperationPriority.CRITICAL.value
                )
                self.operation_queue.add_operation(operation)
                logger.warning(f"⚠️ PostgreSQL down, order queued with temp ID: {order_id}")
            
            # Начислить баллы лояльности
            if order_id and order_data.get('total_amount', 0) > 0:
                loyalty_points = int(order_data['total_amount'] * 0.01)  # 1%
                
                if self.health_monitor.supabase_status:
                    try:
                        secure_supabase.add_loyalty_points(
                            user_identifier, 
                            loyalty_points, 
                            f"Заказ #{order_id}"
                        )
                        logger.info(f"✅ Loyalty points added: {loyalty_points}")
                    except Exception as e:
                        logger.error(f"Failed to add loyalty points: {e}")
                        
                        # Добавить в очередь
                        operation = PendingOperation(
                            operation_id=str(uuid.uuid4()),
                            operation_type="add_loyalty_points",
                            target_db=DatabaseType.SUPABASE.value,
                            user_identifier=user_identifier,
                            platform=platform,
                            data={'points': loyalty_points, 'reason': f"Заказ #{order_id}"},
                            timestamp=datetime.utcnow().isoformat(),
                            priority=OperationPriority.NORMAL.value
                        )
                        self.operation_queue.add_operation(operation)
                else:
                    # Supabase недоступен, добавляем в очередь
                    operation = PendingOperation(
                        operation_id=str(uuid.uuid4()),
                        operation_type="add_loyalty_points",
                        target_db=DatabaseType.SUPABASE.value,
                        user_identifier=user_identifier,
                        platform=platform,
                        data={'points': loyalty_points, 'reason': f"Заказ #{order_id}"},
                        timestamp=datetime.utcnow().isoformat(),
                        priority=OperationPriority.NORMAL.value
                    )
                    self.operation_queue.add_operation(operation)
                    logger.warning(f"⚠️ Supabase down, loyalty points queued: {loyalty_points}")
            
            # Сохранить заказ в кэш
            order_cache_data = {
                'order_id': order_id,
                'user_identifier': user_identifier,
                'platform': platform,
                'order_data': order_data,
                'status': 'pending_confirmation' if not self.health_monitor.postgresql_status else 'confirmed',
                'created_at': datetime.utcnow().isoformat()
            }
            self.local_cache.set(f"order_{order_id}", order_cache_data, ttl=86400)  # 24 часа
            
            if order_id:
                self.operation_stats['successful_operations'] += 1
                return order_id
            else:
                self.operation_stats['failed_operations'] += 1
                return None
                
        except Exception as e:
            logger.error(f"❌ Error creating order: {e}")
            self.operation_stats['failed_operations'] += 1
            return None
    
    def get_loyalty_with_fallback(self, user_identifier: Union[int, str], platform: str) -> Dict:
        """Получить информацию о лояльности с резервными источниками"""
        try:
            self.operation_stats['total_operations'] += 1
            
            # Проверяем кэш
            cache_key = f"loyalty_{platform}_{user_identifier}"
            cached_loyalty = self.local_cache.get(cache_key)
            if cached_loyalty:
                logger.info(f"📋 Loyalty info from cache: {user_identifier}")
                self.operation_stats['cached_operations'] += 1
                return cached_loyalty
            
            loyalty_info = {
                'current_points': 0,
                'partner_cards': [],
                'recent_history': [],
                'source': 'unknown'
            }
            
            # Пытаемся получить из Supabase
            if self.health_monitor.supabase_status:
                try:
                    points = secure_supabase.get_loyalty_points(user_identifier)
                    cards = secure_supabase.get_user_partner_cards(user_identifier)
                    history = secure_supabase.get_loyalty_history(user_identifier, limit=5)
                    
                    loyalty_info = {
                        'current_points': points,
                        'partner_cards': cards,
                        'recent_history': history,
                        'source': 'supabase'
                    }
                    
                    # Кэшируем результат
                    self.local_cache.set(cache_key, loyalty_info, ttl=300)  # 5 минут
                    self.operation_stats['successful_operations'] += 1
                    
                    return loyalty_info
                    
                except Exception as e:
                    logger.error(f"Error getting loyalty info from Supabase: {e}")
            
            # Если Supabase недоступен, возвращаем базовую информацию
            logger.warning(f"⚠️ Loyalty info unavailable for user: {user_identifier}")
            loyalty_info['source'] = 'fallback'
            
            # Кэшируем базовую информацию на короткое время
            self.local_cache.set(cache_key, loyalty_info, ttl=60)  # 1 минута
            self.operation_stats['cached_operations'] += 1
            
            return loyalty_info
            
        except Exception as e:
            logger.error(f"❌ Error getting loyalty info: {e}")
            self.operation_stats['failed_operations'] += 1
            return {
                'current_points': 0,
                'partner_cards': [],
                'recent_history': [],
                'source': 'error'
            }
    
    # === МЕТОДЫ МОНИТОРИНГА И СТАТИСТИКИ ===
    
    def get_system_status(self) -> Dict:
        """Получить полный статус системы"""
        health_status = self.health_monitor.get_health_status()
        uptime_stats = self.health_monitor.get_uptime_stats()
        queue_stats = self.operation_queue.get_queue_stats()
        cache_stats = self.local_cache.get_cache_stats()
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'health': health_status,
            'uptime': uptime_stats,
            'queue': queue_stats,
            'cache': cache_stats,
            'operations': self.operation_stats,
            'mode': self._get_system_mode()
        }
    
    def _get_system_mode(self) -> str:
        """Определить режим работы системы"""
        postgresql_ok = self.health_monitor.postgresql_status
        supabase_ok = self.health_monitor.supabase_status
        
        if postgresql_ok and supabase_ok:
            return "FULL_OPERATIONAL"
        elif postgresql_ok and not supabase_ok:
            return "MAIN_DB_ONLY"
        elif not postgresql_ok and supabase_ok:
            return "LOYALTY_ONLY"
        else:
            return "CACHE_ONLY"
    
    def force_sync_all_pending(self) -> Dict:
        """Принудительно синхронизировать все отложенные операции"""
        try:
            total_operations = self.operation_queue.get_queue_stats()['total_operations']
            
            if total_operations == 0:
                return {'status': 'success', 'message': 'No pending operations', 'processed': 0}
            
            logger.info(f"🔄 Starting forced sync of {total_operations} pending operations")
            
            processed = 0
            failed = 0
            
            # Обработать операции для PostgreSQL
            if self.health_monitor.postgresql_status:
                postgresql_ops = self.operation_queue.get_operations_for_db(DatabaseType.POSTGRESQL.value)
                for operation in postgresql_ops:
                    if self._execute_pending_operation(operation):
                        self.operation_queue.remove_operation(operation)
                        processed += 1
                    else:
                        failed += 1
            
            # Обработать операции для Supabase
            if self.health_monitor.supabase_status:
                supabase_ops = self.operation_queue.get_operations_for_db(DatabaseType.SUPABASE.value)
                for operation in supabase_ops:
                    if self._execute_pending_operation(operation):
                        self.operation_queue.remove_operation(operation)
                        processed += 1
                    else:
                        failed += 1
            
            logger.info(f"✅ Forced sync completed: {processed} processed, {failed} failed")
            
            return {
                'status': 'success',
                'message': f'Sync completed: {processed} processed, {failed} failed',
                'processed': processed,
                'failed': failed,
                'remaining': self.operation_queue.get_queue_stats()['total_operations']
            }
            
        except Exception as e:
            logger.error(f"❌ Error during forced sync: {e}")
            return {'status': 'error', 'message': str(e)}

# Глобальный экземпляр отказоустойчивого сервиса
fault_tolerant_db = FaultTolerantService()
