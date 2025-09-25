#!/usr/bin/env python3
"""
Скрипт для очистки Redis блокировок бота
"""
import os
import redis
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clear_redis_locks():
    """Очистить все блокировки бота в Redis"""
    try:
        # Подключаемся к Redis
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        r = redis.from_url(redis_url)
        
        # Проверяем подключение
        r.ping()
        logger.info("✅ Подключение к Redis успешно")
        
        # Ищем все ключи блокировок
        lock_keys = r.keys('*:bot:*:polling:leader')
        logger.info(f"🔍 Найдено блокировок: {len(lock_keys)}")
        
        # Удаляем все блокировки
        if lock_keys:
            deleted = r.delete(*lock_keys)
            logger.info(f"🗑️ Удалено блокировок: {deleted}")
        else:
            logger.info("ℹ️ Блокировок не найдено")
            
        # Также очищаем другие возможные блокировки
        other_locks = r.keys('*lock*')
        if other_locks:
            deleted = r.delete(*other_locks)
            logger.info(f"🗑️ Удалено других блокировок: {deleted}")
            
        logger.info("✅ Очистка Redis блокировок завершена")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка очистки Redis: {e}")
        return False

if __name__ == "__main__":
    success = clear_redis_locks()
    if success:
        print("✅ Redis блокировки очищены успешно")
    else:
        print("❌ Ошибка очистки Redis блокировок")
