"""
Rate Limiting Middleware для защиты от спама и злоупотреблений
"""
import time
import asyncio
from typing import Dict, Any
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class RateLimitMiddleware(BaseMiddleware):
    """
    Middleware для ограничения частоты запросов по ролям пользователей
    """
    
    def __init__(self, redis_client=None):
        """
        Инициализация middleware
        
        Args:
            redis_client: Redis клиент для распределенного rate limiting (опционально)
        """
        self.redis_client = redis_client
        self.local_cache = defaultdict(list)  # Для локального кэширования
        self.cleanup_task = None
        
        # Лимиты по ролям (запросов в час)
        self.rate_limits = {
            'user': 60,           # 60 запросов/час для обычных пользователей
            'partner': 120,       # 120 запросов/час для партнеров
            'admin': 300,         # 300 запросов/час для админов
            'super_admin': 600    # 600 запросов/час для супер-админов
        }
        
        # Запустить задачу очистки кэша
        self._start_cleanup_task()
    
    def _start_cleanup_task(self):
        """Запустить задачу периодической очистки кэша"""
        if self.cleanup_task is None or self.cleanup_task.done():
            self.cleanup_task = asyncio.create_task(self._cleanup_cache())
    
    async def _cleanup_cache(self):
        """Периодическая очистка устаревших записей из кэша"""
        while True:
            try:
                await asyncio.sleep(300)  # Очистка каждые 5 минут
                current_time = time.time()
                
                # Очистить локальный кэш от записей старше часа
                for user_id in list(self.local_cache.keys()):
                    user_requests = self.local_cache[user_id]
                    self.local_cache[user_id] = [
                        req_time for req_time in user_requests 
                        if current_time - req_time < 3600
                    ]
                    
                    # Удалить пустые записи
                    if not self.local_cache[user_id]:
                        del self.local_cache[user_id]
                        
            except Exception as e:
                logger.error(f"Ошибка очистки кэша rate limiting: {e}")
    
    async def _get_user_role(self, user_id: int) -> str:
        """
        Получить роль пользователя для определения лимитов
        
        Args:
            user_id: ID пользователя Telegram
            
        Returns:
            str: Роль пользователя (user, partner, admin, super_admin)
        """
        try:
            # Проверить супер-админа
            from core.settings import settings
            if int(user_id) == int(settings.bots.admin_id):
                return 'super_admin'
            
            # Проверить админов
            from core.services.admins import admins_service
            if await admins_service.is_admin(user_id):
                return 'admin'
            
            # Проверить партнеров
            from core.database.db_v2 import db_v2
            partner = await db_v2.get_partner_by_telegram_id(user_id)
            if partner:
                return 'partner'
            
            # По умолчанию - обычный пользователь
            return 'user'
            
        except Exception as e:
            logger.error(f"Ошибка определения роли пользователя {user_id}: {e}")
            return 'user'  # Безопасное значение по умолчанию
    
    async def _check_rate_limit(self, user_id: int, role: str) -> bool:
        """
        Проверить превышение лимита запросов
        
        Args:
            user_id: ID пользователя
            role: Роль пользователя
            
        Returns:
            bool: True если лимит не превышен, False если превышен
        """
        try:
            current_time = time.time()
            limit = self.rate_limits.get(role, self.rate_limits['user'])
            
            if self.redis_client:
                # Использовать Redis для распределенного rate limiting
                return await self._check_redis_rate_limit(user_id, limit, current_time)
            else:
                # Использовать локальный кэш
                return self._check_local_rate_limit(user_id, limit, current_time)
                
        except Exception as e:
            logger.error(f"Ошибка проверки rate limit для пользователя {user_id}: {e}")
            return True  # В случае ошибки разрешить запрос
    
    async def _check_redis_rate_limit(self, user_id: int, limit: int, current_time: float) -> bool:
        """Проверить лимит через Redis"""
        try:
            key = f"rate_limit:{user_id}"
            
            # Получить текущее количество запросов
            current_count = await self.redis_client.get(key)
            current_count = int(current_count) if current_count else 0
            
            if current_count >= limit:
                return False
            
            # Увеличить счетчик
            pipe = self.redis_client.pipeline()
            pipe.incr(key)
            pipe.expire(key, 3600)  # TTL 1 час
            await pipe.execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка Redis rate limiting: {e}")
            return True
    
    def _check_local_rate_limit(self, user_id: int, limit: int, current_time: float) -> bool:
        """Проверить лимит через локальный кэш"""
        try:
            user_requests = self.local_cache[user_id]
            
            # Удалить старые запросы (старше часа)
            user_requests[:] = [
                req_time for req_time in user_requests 
                if current_time - req_time < 3600
            ]
            
            # Проверить лимит
            if len(user_requests) >= limit:
                return False
            
            # Добавить текущий запрос
            user_requests.append(current_time)
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка локального rate limiting: {e}")
            return True
    
    async def __call__(self, handler, event, data):
        """
        Основной метод middleware
        
        Args:
            handler: Следующий обработчик в цепочке
            event: Событие (Message, CallbackQuery и т.д.)
            data: Данные события
        """
        try:
            # Проверить есть ли информация о пользователе
            if not hasattr(event, 'from_user') or not event.from_user:
                return await handler(event, data)
            
            user_id = event.from_user.id
            
            # Получить роль пользователя
            role = await self._get_user_role(user_id)
            
            # Проверить rate limit
            if not await self._check_rate_limit(user_id, role):
                # Лимит превышен
                await self._handle_rate_limit_exceeded(event, role)
                return
            
            # Лимит не превышен, продолжить обработку
            return await handler(event, data)
            
        except Exception as e:
            logger.error(f"Ошибка в RateLimitMiddleware: {e}")
            # В случае ошибки разрешить запрос
            return await handler(event, data)
    
    async def _handle_rate_limit_exceeded(self, event, role: str):
        """
        Обработать превышение лимита запросов
        
        Args:
            event: Событие от пользователя
            role: Роль пользователя
        """
        try:
            # Определить лимит для роли
            limit = self.rate_limits.get(role, self.rate_limits['user'])
            
            # Сообщения об ошибке по ролям
            messages = {
                'user': f"⚠️ Превышен лимит запросов ({limit}/час). Попробуйте позже.",
                'partner': f"⚠️ Превышен лимит запросов ({limit}/час). Попробуйте позже.",
                'admin': f"⚠️ Превышен лимит запросов ({limit}/час). Попробуйте позже.",
                'super_admin': f"⚠️ Превышен лимит запросов ({limit}/час). Попробуйте позже."
            }
            
            message_text = messages.get(role, messages['user'])
            
            # Отправить сообщение об ошибке
            if isinstance(event, Message):
                await event.answer(message_text)
            elif isinstance(event, CallbackQuery):
                await event.answer(message_text, show_alert=True)
            
            # Логировать превышение лимита
            logger.warning(f"Rate limit exceeded for user {event.from_user.id} (role: {role})")
            
        except Exception as e:
            logger.error(f"Ошибка обработки превышения rate limit: {e}")


# Функция для создания middleware с Redis (если доступен)
def create_rate_limit_middleware(redis_url: str = None):
    """
    Создать RateLimitMiddleware с опциональной поддержкой Redis
    
    Args:
        redis_url: URL Redis для распределенного rate limiting
        
    Returns:
        RateLimitMiddleware: Настроенный middleware
    """
    redis_client = None
    
    if redis_url:
        try:
            import redis.asyncio as redis
            redis_client = redis.from_url(redis_url)
            logger.info("Rate limiting с Redis подключен")
        except ImportError:
            logger.warning("Redis не доступен, используется локальный кэш")
        except Exception as e:
            logger.error(f"Ошибка подключения к Redis: {e}")
    
    return RateLimitMiddleware(redis_client=redis_client)

