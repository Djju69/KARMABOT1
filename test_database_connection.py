#!/usr/bin/env python3
"""
Тестовый скрипт для проверки подключения к базе данных
и доступности всех необходимых таблиц
"""
import os
import sys
import logging
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent))

# Настраиваем логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_database_connection():
    """Тестирует подключение к базе данных"""
    try:
        logger.info("🔍 Тестирование подключения к базе данных...")
        
        # Проверяем переменные окружения
        database_url = os.getenv('DATABASE_URL')
        app_env = os.getenv('APP_ENV', 'development')
        railway_env = os.getenv('RAILWAY_ENVIRONMENT')
        
        logger.info(f"📊 DATABASE_URL: {'Установлен' if database_url else 'Не установлен'}")
        logger.info(f"📊 APP_ENV: {app_env}")
        logger.info(f"📊 RAILWAY_ENVIRONMENT: {railway_env}")
        
        # Импортируем адаптер базы данных
        from core.database.db_adapter import db_v2
        logger.info("✅ Адаптер базы данных импортирован успешно")
        
        # Тестируем подключение
        try:
            # Проверяем категории
            categories = db_v2.get_categories()
            logger.info(f"✅ Категории получены: {len(categories)} записей")
            
            # Проверяем пользователей
            users_count = db_v2.get_users_count()
            logger.info(f"✅ Пользователи: {users_count} записей")
            
            # Проверяем партнеров
            partners_count = db_v2.get_partners_count()
            logger.info(f"✅ Партнеры: {partners_count} записей")
            
            # Проверяем карты
            cards_count = db_v2.get_cards_count()
            logger.info(f"✅ Карты: {cards_count} записей")
            
            logger.info("🎉 Все тесты базы данных прошли успешно!")
            return True
            
        except Exception as db_error:
            logger.error(f"❌ Ошибка при тестировании базы данных: {db_error}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        return False

def test_loyalty_service():
    """Тестирует сервис лояльности"""
    try:
        logger.info("🔍 Тестирование сервиса лояльности...")
        
        from core.services.loyalty_service import loyalty_service
        
        # Тестируем получение баланса (для тестового пользователя)
        test_user_id = 12345
        balance = loyalty_service.get_user_points_balance(test_user_id)
        logger.info(f"✅ Баланс тестового пользователя: {balance} баллов")
        
        logger.info("🎉 Тест сервиса лояльности прошел успешно!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка в сервисе лояльности: {e}")
        return False

def test_imports():
    """Тестирует импорты всех необходимых модулей"""
    try:
        logger.info("🔍 Тестирование импортов...")
        
        # Основные модули
        from core.handlers.loyalty_settings_router import router as loyalty_router
        logger.info("✅ Loyalty settings router импортирован")
        
        from core.fsm.loyalty_settings import LoyaltySettingsStates
        logger.info("✅ Loyalty settings FSM импортирован")
        
        from core.handlers.admin_cabinet import get_admin_cabinet_router
        logger.info("✅ Admin cabinet router импортирован")
        
        from core.handlers.cabinet_router import get_cabinet_router
        logger.info("✅ Cabinet router импортирован")
        
        from core.handlers.profile import get_profile_router
        logger.info("✅ Profile router импортирован")
        
        logger.info("🎉 Все импорты прошли успешно!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка импорта: {e}")
        return False

def main():
    """Основная функция тестирования"""
    logger.info("🚀 Начинаем тестирование системы...")
    
    tests = [
        ("Импорты", test_imports),
        ("База данных", test_database_connection),
        ("Сервис лояльности", test_loyalty_service),
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"🧪 Тест: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"❌ Тест {test_name} завершился с ошибкой: {e}")
            results.append((test_name, False))
    
    # Итоговый отчет
    logger.info(f"\n{'='*50}")
    logger.info("📊 ИТОГОВЫЙ ОТЧЕТ")
    logger.info(f"{'='*50}")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
    
    logger.info(f"\nРезультат: {passed}/{total} тестов пройдено")
    
    if passed == total:
        logger.info("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Система готова к работе.")
        return True
    else:
        logger.warning(f"⚠️ {total - passed} тестов провалено. Требуется исправление.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
