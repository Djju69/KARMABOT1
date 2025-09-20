#!/usr/bin/env python3
"""
Тест подключения к Supabase и функций создания карточек/партнерства
"""
import os
import asyncio
import logging
from typing import Dict, Any

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_database_connection():
    """Тест подключения к базе данных"""
    logger.info("🔍 Тестируем подключение к базе данных...")
    
    try:
        from core.database.db_v2 import db_v2
        
        # Простой тест подключения
        cards_count = db_v2.get_cards_count()
        logger.info(f"✅ База данных работает! Карточек в системе: {cards_count}")
        
        # Тест получения партнеров
        partners_count = db_v2.get_partners_count()
        logger.info(f"✅ Партнеров в системе: {partners_count}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к базе данных: {e}")
        return False

async def test_partner_creation():
    """Тест создания партнера"""
    logger.info("🔍 Тестируем создание партнера...")
    
    try:
        from core.database.db_v2 import db_v2
        
        # Создаем тестового партнера
        test_user_id = 999999999  # Тестовый ID
        test_name = "Тестовый Партнер"
        
        partner = db_v2.get_or_create_partner(test_user_id, test_name)
        logger.info(f"✅ Партнер создан: ID={partner.id}, Name={partner.display_name}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания партнера: {e}")
        return False

async def test_card_creation():
    """Тест создания карточки"""
    logger.info("🔍 Тестируем создание карточки...")
    
    try:
        from core.database.db_v2 import db_v2
        
        # Создаем тестового партнера
        test_user_id = 999999999
        test_name = "Тестовый Партнер"
        partner = db_v2.get_or_create_partner(test_user_id, test_name)
        
        # Создаем тестовую карточку
        from core.database.db_v2 import Card
        
        card = Card(
            id=None,
            partner_id=partner.id,
            category_id=1,  # Предполагаем что категория 1 существует
            title='Тестовое Заведение',
            description='Описание тестового заведения',
            address='Тестовый адрес',
            contact='+7999999999',
            status='pending'
        )
        
        card_id = db_v2.create_card(card)
        logger.info(f"✅ Карточка создана: ID={card_id}, Title={card.title}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания карточки: {e}")
        return False

async def test_feature_flags():
    """Тест фича-флагов"""
    logger.info("🔍 Проверяем фича-флаги...")
    
    try:
        from core.settings import settings
        
        logger.info(f"✅ Partner FSM: {settings.features.partner_fsm}")
        logger.info(f"✅ Moderation: {settings.features.moderation}")
        logger.info(f"✅ New Menu: {settings.features.new_menu}")
        logger.info(f"✅ WebApp URL: {settings.features.webapp_url}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка проверки фича-флагов: {e}")
        return False

async def test_handlers():
    """Тест обработчиков"""
    logger.info("🔍 Проверяем обработчики...")
    
    try:
        # Проверяем что обработчики импортируются
        from core.handlers.partner import start_add_card
        from core.handlers.profile import on_become_partner
        
        logger.info("✅ Обработчики партнерства импортированы")
        
        # Проверяем клавиатуры
        from core.keyboards.reply_v2 import get_partner_keyboard
        from core.keyboards.reply_v2 import get_user_cabinet_keyboard
        
        logger.info("✅ Клавиатуры импортированы")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка импорта обработчиков: {e}")
        return False

async def main():
    """Главная функция тестирования"""
    logger.info("🚀 Начинаем тестирование Supabase и функций...")
    
    tests = [
        ("Подключение к БД", test_database_connection),
        ("Фича-флаги", test_feature_flags),
        ("Обработчики", test_handlers),
        ("Создание партнера", test_partner_creation),
        ("Создание карточки", test_card_creation),
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
        logger.info("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Система готова к работе!")
    else:
        logger.warning("⚠️ Есть проблемы, требующие исправления")
    
    return passed == total

if __name__ == "__main__":
    asyncio.run(main())
