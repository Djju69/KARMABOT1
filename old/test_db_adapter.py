#!/usr/bin/env python3
"""
Тест адаптера базы данных
"""
import os
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_db_adapter():
    """Тест адаптера базы данных"""
    logger.info("🔍 Тестируем адаптер базы данных...")
    
    try:
        from core.database.db_adapter import db_v2
        
        logger.info(f"✅ Адаптер создан: PostgreSQL={db_v2.use_postgresql}")
        
        # Тест получения категорий
        categories = db_v2.get_categories()
        logger.info(f"✅ Категории получены: {len(categories)} штук")
        
        # Тест получения карточек
        cards = db_v2.get_cards_by_category('restaurants', status='approved')
        logger.info(f"✅ Карточки ресторанов получены: {len(cards)} штук")
        
        # Тест создания партнера
        partner = db_v2.get_or_create_partner(999999999, "Тестовый Партнер 2")
        logger.info(f"✅ Партнер создан/получен: ID={partner.id}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка в адаптере: {e}")
        return False

async def main():
    """Главная функция"""
    logger.info("🚀 Тестирование адаптера базы данных")
    
    success = await test_db_adapter()
    
    if success:
        logger.info("🎉 АДАПТЕР РАБОТАЕТ!")
    else:
        logger.error("❌ АДАПТЕР НЕ РАБОТАЕТ")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())
