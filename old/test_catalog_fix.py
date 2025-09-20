#!/usr/bin/env python3
"""
Тест исправления проблем с каталогом и личным кабинетом
"""
import os
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_catalog_functions():
    """Тест функций каталога"""
    logger.info("🔍 Тестируем функции каталога...")
    
    try:
        # Проверяем импорты
        from core.handlers.category_handlers_v2 import on_restaurants, on_spa, on_transport
        from core.keyboards.reply_v2 import get_categories_keyboard, get_restaurants_reply_keyboard
        from core.utils.telemetry import log_event
        
        logger.info("✅ Все импорты каталога работают")
        
        # Проверяем клавиатуры
        keyboard = get_categories_keyboard('ru')
        logger.info(f"✅ Клавиатура категорий создана: {len(keyboard.keyboard)} рядов")
        
        restaurants_keyboard = get_restaurants_reply_keyboard('ru')
        logger.info(f"✅ Клавиатура ресторанов создана: {len(restaurants_keyboard.keyboard)} рядов")
        
        # Проверяем функцию log_event
        await log_event("test_event", user=None, test_field="test_value")
        logger.info("✅ Функция log_event работает")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка в функциях каталога: {e}")
        return False

async def test_cabinet_functions():
    """Тест функций личного кабинета"""
    logger.info("🔍 Тестируем функции личного кабинета...")
    
    try:
        # Проверяем импорты
        from core.keyboards.unified_menu import get_user_cabinet_keyboard
        from core.handlers.cabinet_router import view_history_handler
        from core.handlers.profile import on_my_cards
        
        logger.info("✅ Все импорты личного кабинета работают")
        
        # Проверяем клавиатуру
        keyboard = get_user_cabinet_keyboard('ru')
        logger.info(f"✅ Клавиатура личного кабинета создана: {len(keyboard.keyboard)} рядов")
        
        # Проверяем что обработчики существуют
        logger.info("✅ Обработчики личного кабинета существуют")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка в функциях личного кабинета: {e}")
        return False

async def test_database_queries():
    """Тест запросов к базе данных"""
    logger.info("🔍 Тестируем запросы к базе данных...")
    
    try:
        from core.database.db_v2 import db_v2
        
        # Проверяем получение категорий
        categories = db_v2.get_categories()
        logger.info(f"✅ Категории получены: {len(categories)} штук")
        
        # Проверяем получение карточек
        cards = db_v2.get_cards_by_category(1)  # Рестораны
        logger.info(f"✅ Карточки ресторанов получены: {len(cards)} штук")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка в запросах к базе данных: {e}")
        return False

async def main():
    """Главная функция тестирования"""
    logger.info("🚀 Начинаем тестирование исправлений...")
    
    tests = [
        ("Функции каталога", test_catalog_functions),
        ("Функции личного кабинета", test_cabinet_functions),
        ("Запросы к базе данных", test_database_queries),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"🧪 ТЕСТ: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            result = await test_func()
            results[test_name] = result
        except Exception as e:
            logger.error(f"❌ Критическая ошибка в тесте {test_name}: {e}")
            results[test_name] = False
    
    # Итоговый отчет
    logger.info(f"\n{'='*50}")
    logger.info("📊 ИТОГОВЫЙ ОТЧЕТ")
    logger.info(f"{'='*50}")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\n🎯 РЕЗУЛЬТАТ: {passed}/{total} тестов пройдено")
    
    if passed == total:
        logger.info("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Проблемы исправлены!")
    else:
        logger.warning("⚠️ Есть проблемы, требующие исправления")
    
    return passed == total

if __name__ == "__main__":
    asyncio.run(main())
