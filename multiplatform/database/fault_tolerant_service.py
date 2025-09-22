"""
Отказоустойчивый сервис для мульти-платформенной экосистемы
БЕЗ операций с файлами - только в памяти
"""
import asyncio
import logging
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class SystemMode(Enum):
    """Режимы работы системы"""
    NORMAL = "normal"           # Все БД работают
    DEGRADED = "degraded"       # Одна БД недоступна
    EMERGENCY = "emergency"     # Все БД недоступны, только кеш

@dataclass
class Operation:
    """Операция для очереди"""
    id: str
    operation_type: str
    data: Dict[str, Any]
    timestamp: datetime
    retry_count: int = 0
    max_retries: int = 3

class DatabaseHealthMonitor:
    """Мониторинг здоровья баз данных"""
    
    def __init__(self):
        self.health_status = {
            'postgresql': {'status': 'unknown', 'last_check': None, 'response_time': None},
            'supabase': {'status': 'unknown', 'last_check': None, 'response_time': None}
        }
        self.overall_health = True
    
    async def check_postgresql_health(self) -> Dict[str, Any]:
        """Проверка здоровья PostgreSQL"""
        try:
            start_time = datetime.now()
            # Здесь должна быть реальная проверка PostgreSQL
            # Пока заглушка
            response_time = (datetime.now() - start_time).total_seconds()
            
            self.health_status['postgresql'] = {
                'status': 'healthy',
                'last_check': datetime.now().isoformat(),
                'response_time': response_time
            }
            return {'status': 'healthy', 'response_time': response_time}
        except Exception as e:
            logger.error(f"PostgreSQL health check failed: {e}")
            self.health_status['postgresql'] = {
                'status': 'unhealthy',
                'last_check': datetime.now().isoformat(),
                'error': str(e)
            }
            return {'status': 'unhealthy', 'error': str(e)}
    
    async def check_supabase_health(self) -> Dict[str, Any]:
        """Проверка здоровья Supabase"""
        try:
            start_time = datetime.now()
            # Здесь должна быть реальная проверка Supabase
            # Пока заглушка
            response_time = (datetime.now() - start_time).total_seconds()
            
            self.health_status['supabase'] = {
                'status': 'healthy',
                'last_check': datetime.now().isoformat(),
                'response_time': response_time
            }
            return {'status': 'healthy', 'response_time': response_time}
        except Exception as e:
            logger.error(f"Supabase health check failed: {e}")
            self.health_status['supabase'] = {
                'status': 'unhealthy',
                'last_check': datetime.now().isoformat(),
                'error': str(e)
            }
            return {'status': 'unhealthy', 'error': str(e)}
    
    async def check_all_databases(self) -> Dict[str, Any]:
        """Проверка всех баз данных"""
        postgresql_status = await self.check_postgresql_health()
        supabase_status = await self.check_supabase_health()
        
        # Определяем общее состояние
        healthy_count = sum([
            1 for status in [postgresql_status, supabase_status] 
            if status.get('status') == 'healthy'
        ])
        
        self.overall_health = healthy_count > 0
        
        return {
            'overall': self.overall_health,
            'postgresql': postgresql_status,
            'supabase': supabase_status,
            'healthy_databases': healthy_count,
            'total_databases': 2
        }

class OperationQueue:
    """Очередь операций для отложенного выполнения"""
    
    def __init__(self):
        self.queue: List[Operation] = []
        self.max_queue_size = 1000
        self.processing = False
    
    def add_operation(self, operation_type: str, data: Dict[str, Any]) -> str:
        """Добавление операции в очередь"""
        if len(self.queue) >= self.max_queue_size:
            # Удаляем старые операции
            self.queue = self.queue[-500:]
            logger.warning("Queue size limit reached, removing old operations")
        
        operation_id = str(uuid.uuid4())
        operation = Operation(
            id=operation_id,
            operation_type=operation_type,
            data=data,
            timestamp=datetime.now()
        )
        
        self.queue.append(operation)
        logger.info(f"Added operation {operation_type} to queue: {operation_id}")
        return operation_id
    
    def get_pending_operations(self) -> List[Operation]:
        """Получение всех ожидающих операций"""
        return [op for op in self.queue if op.retry_count < op.max_retries]
    
    def mark_operation_completed(self, operation_id: str):
        """Отметка операции как выполненной"""
        self.queue = [op for op in self.queue if op.id != operation_id]
        logger.info(f"Operation {operation_id} marked as completed")
    
    def mark_operation_failed(self, operation_id: str):
        """Отметка операции как неудачной"""
        for op in self.queue:
            if op.id == operation_id:
                op.retry_count += 1
                logger.warning(f"Operation {operation_id} failed, retry count: {op.retry_count}")
                break

class LocalCache:
    """Локальный кеш в памяти"""
    
    def __init__(self):
        self.cache: Dict[str, Any] = {}
        self.max_cache_size = 10000
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0
        }
    
    def get(self, key: str) -> Optional[Any]:
        """Получение значения из кеша"""
        if key in self.cache:
            self.cache_stats['hits'] += 1
            return self.cache[key]
        else:
            self.cache_stats['misses'] += 1
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Установка значения в кеш"""
        if len(self.cache) >= self.max_cache_size:
            # Удаляем 20% старых записей
            keys_to_remove = list(self.cache.keys())[:self.max_cache_size // 5]
            for key_to_remove in keys_to_remove:
                del self.cache[key_to_remove]
            logger.warning("Cache size limit reached, removing old entries")
        
        self.cache[key] = {
            'value': value,
            'timestamp': datetime.now().isoformat(),
            'ttl': ttl
        }
        self.cache_stats['sets'] += 1
    
    def delete(self, key: str):
        """Удаление значения из кеша"""
        if key in self.cache:
            del self.cache[key]
            self.cache_stats['deletes'] += 1
    
    def clear(self):
        """Очистка всего кеша"""
        self.cache.clear()
        logger.info("Local cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Получение статистики кеша"""
        total_requests = self.cache_stats['hits'] + self.cache_stats['misses']
        hit_rate = (self.cache_stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'total_items': len(self.cache),
            'max_size': self.max_cache_size,
            'hit_rate': round(hit_rate, 2),
            'stats': self.cache_stats
        }

class FaultTolerantService:
    """Главный отказоустойчивый сервис для мульти-платформенной экосистемы"""
    
    def __init__(self):
        self.health_monitor = DatabaseHealthMonitor()
        self.operation_queue = OperationQueue()
        self.local_cache = LocalCache()
        self.system_mode = SystemMode.NORMAL
        self.operation_stats = {
            'total_operations': 0,
            'successful_operations': 0,
            'failed_operations': 0,
            'queued_operations': 0
        }
        self.start_time = datetime.now()
        self._start_recovery_processor()
        logger.info("🛡️ FaultTolerantService initialized successfully")
    
    def _start_recovery_processor(self):
        """Запуск процессора восстановления"""
        async def recovery_processor():
            while True:
                try:
                    await self._process_pending_operations()
                    await asyncio.sleep(30)  # Проверяем каждые 30 секунд
                except Exception as e:
                    logger.error(f"Recovery processor error: {e}")
                    await asyncio.sleep(60)  # При ошибке ждем минуту
        
        # Запускаем в фоне
        asyncio.create_task(recovery_processor())
    
    async def _process_pending_operations(self):
        """Обработка ожидающих операций"""
        pending_ops = self.operation_queue.get_pending_operations()
        if not pending_ops:
            return
        
        logger.info(f"Processing {len(pending_ops)} pending operations")
        
        for operation in pending_ops:
            try:
                await self._execute_operation(operation)
                self.operation_queue.mark_operation_completed(operation.id)
                self.operation_stats['successful_operations'] += 1
            except Exception as e:
                logger.error(f"Failed to execute operation {operation.id}: {e}")
                self.operation_queue.mark_operation_failed(operation.id)
                self.operation_stats['failed_operations'] += 1
    
    async def _execute_operation(self, operation: Operation):
        """Выполнение операции"""
        # Здесь должна быть логика выполнения операций
        # Пока заглушка
        logger.info(f"Executing operation {operation.operation_type}: {operation.id}")
        await asyncio.sleep(0.1)  # Имитация работы
    
    async def create_user_with_fallback(self, user_id: str, user_data: Dict[str, Any], platform: str) -> bool:
        """Создание пользователя с отказоустойчивостью"""
        self.operation_stats['total_operations'] += 1
        
        try:
            # Попытка создать пользователя в основной БД
            # Здесь должна быть реальная логика создания пользователя
            logger.info(f"Creating user {user_id} on platform {platform}")
            
            # Кешируем данные пользователя
            cache_key = f"user:{platform}:{user_id}"
            self.local_cache.set(cache_key, user_data)
            
            self.operation_stats['successful_operations'] += 1
            return True
            
        except Exception as e:
            logger.error(f"Failed to create user {user_id}: {e}")
            
            # Добавляем в очередь для повторной попытки
            self.operation_queue.add_operation("create_user", {
                'user_id': user_id,
                'user_data': user_data,
                'platform': platform
            })
            self.operation_stats['queued_operations'] += 1
            
            return False
    
    async def get_user_with_fallback(self, user_id: str, platform: str) -> Optional[Dict[str, Any]]:
        """Получение пользователя с отказоустойчивостью"""
        try:
            # Сначала проверяем кеш
            cache_key = f"user:{platform}:{user_id}"
            cached_user = self.local_cache.get(cache_key)
            if cached_user:
                return cached_user['value']
            
            # Здесь должна быть логика получения из БД
            # Пока возвращаем заглушку
            return None
            
        except Exception as e:
            logger.error(f"Failed to get user {user_id}: {e}")
            return None
    
    def get_system_status(self) -> Dict[str, Any]:
        """Получение статуса системы"""
        health_status = asyncio.run(self.health_monitor.check_all_databases())
        
        return {
            'mode': self.system_mode.value,
            'health': health_status,
            'cache': self.local_cache.get_stats(),
            'queue': {
                'total_operations': len(self.operation_queue.queue),
                'pending_operations': len(self.operation_queue.get_pending_operations())
            },
            'stats': self.operation_stats,
            'uptime': str(datetime.now() - self.start_time),
            'timestamp': datetime.now().isoformat()
        }
    
    async def force_sync_all_pending(self) -> Dict[str, Any]:
        """Принудительная синхронизация всех ожидающих операций"""
        pending_ops = self.operation_queue.get_pending_operations()
        processed = 0
        failed = 0
        
        for operation in pending_ops:
            try:
                await self._execute_operation(operation)
                self.operation_queue.mark_operation_completed(operation.id)
                processed += 1
            except Exception as e:
                logger.error(f"Failed to sync operation {operation.id}: {e}")
                self.operation_queue.mark_operation_failed(operation.id)
                failed += 1
        
        return {
            'processed': processed,
            'failed': failed,
            'total': len(pending_ops)
        }

# Глобальный экземпляр сервиса
fault_tolerant_db = FaultTolerantService()
