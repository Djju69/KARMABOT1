"""
Утилита для ограничения частоты запросов к AI-ассистенту
"""
import time
from typing import Dict, List
from collections import defaultdict, deque
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """Класс для ограничения частоты запросов"""
    
    def __init__(self):
        # Хранилище запросов по пользователям
        self.user_requests: Dict[int, deque] = defaultdict(lambda: deque())
        self.user_voice_requests: Dict[int, deque] = defaultdict(lambda: deque())
        
        # Лимиты
        self.ai_messages_limit = 10  # сообщений в минуту
        self.ai_messages_window = 60  # секунд
        self.voice_limit = 5  # голосовых в минуту
        self.voice_window = 60  # секунд
        self.reports_limit = 3  # отчётов в 5 минут
        self.reports_window = 300  # секунд
    
    def is_allowed_ai_message(self, user_id: int) -> bool:
        """Проверяет, можно ли отправить AI-сообщение"""
        now = time.time()
        user_requests = self.user_requests[user_id]
        
        # Удаляем старые запросы
        while user_requests and user_requests[0] < now - self.ai_messages_window:
            user_requests.popleft()
        
        # Проверяем лимит
        if len(user_requests) >= self.ai_messages_limit:
            logger.warning(f"Rate limit exceeded for user {user_id} (AI messages)")
            return False
        
        # Добавляем текущий запрос
        user_requests.append(now)
        return True
    
    def is_allowed_voice(self, user_id: int) -> bool:
        """Проверяет, можно ли отправить голосовое сообщение"""
        now = time.time()
        user_requests = self.user_voice_requests[user_id]
        
        # Удаляем старые запросы
        while user_requests and user_requests[0] < now - self.voice_window:
            user_requests.popleft()
        
        # Проверяем лимит
        if len(user_requests) >= self.voice_limit:
            logger.warning(f"Rate limit exceeded for user {user_id} (voice)")
            return False
        
        # Добавляем текущий запрос
        user_requests.append(now)
        return True
    
    def is_allowed_report(self, user_id: int) -> bool:
        """Проверяет, можно ли создать отчёт"""
        now = time.time()
        user_requests = self.user_requests[user_id]
        
        # Удаляем старые запросы (отчёты)
        report_requests = [req for req in user_requests if req > now - self.reports_window]
        
        # Проверяем лимит
        if len(report_requests) >= self.reports_limit:
            logger.warning(f"Rate limit exceeded for user {user_id} (reports)")
            return False
        
        return True
    
    def get_remaining_ai_messages(self, user_id: int) -> int:
        """Возвращает количество оставшихся AI-сообщений"""
        now = time.time()
        user_requests = self.user_requests[user_id]
        
        # Удаляем старые запросы
        while user_requests and user_requests[0] < now - self.ai_messages_window:
            user_requests.popleft()
        
        return max(0, self.ai_messages_limit - len(user_requests))
    
    def get_remaining_voice(self, user_id: int) -> int:
        """Возвращает количество оставшихся голосовых сообщений"""
        now = time.time()
        user_requests = self.user_voice_requests[user_id]
        
        # Удаляем старые запросы
        while user_requests and user_requests[0] < now - self.voice_window:
            user_requests.popleft()
        
        return max(0, self.voice_limit - len(user_requests))
    
    def reset_user_limits(self, user_id: int):
        """Сбрасывает лимиты для пользователя"""
        if user_id in self.user_requests:
            del self.user_requests[user_id]
        if user_id in self.user_voice_requests:
            del self.user_voice_requests[user_id]
        logger.info(f"Rate limits reset for user {user_id}")


# Глобальный экземпляр
rate_limiter = RateLimiter()
