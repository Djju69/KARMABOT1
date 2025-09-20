#!/usr/bin/env python3
"""
Скрипт для создания таблиц PostgreSQL в Supabase
"""

import os
import asyncio
import asyncpg
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_tables():
    """Создать все необходимые таблицы в PostgreSQL"""
    
    # Получаем DATABASE_URL из переменных окружения
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        logger.error("❌ DATABASE_URL не установлен")
        return False
    
    logger.info(f"🗄️ Подключаемся к PostgreSQL: {database_url[:50]}...")
    
    try:
        # Подключаемся к базе данных
        conn = await asyncpg.connect(database_url)
        logger.info("✅ Подключение к PostgreSQL установлено")
        
        # SQL для создания таблиц
        create_tables_sql = """
        -- Создание таблицы категорий
        CREATE TABLE IF NOT EXISTS categories_v2 (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            slug VARCHAR(50) UNIQUE NOT NULL,
            emoji VARCHAR(10),
            description TEXT,
            is_active BOOLEAN DEFAULT true,
            priority_level INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Создание таблицы партнеров
        CREATE TABLE IF NOT EXISTS partners_v2 (
            id SERIAL PRIMARY KEY,
            tg_user_id BIGINT UNIQUE NOT NULL,
            display_name VARCHAR(200),
            phone VARCHAR(20),
            email VARCHAR(100),
            is_verified BOOLEAN DEFAULT false,
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Создание таблицы карточек
        CREATE TABLE IF NOT EXISTS cards_v2 (
            id SERIAL PRIMARY KEY,
            partner_id INTEGER NOT NULL REFERENCES partners_v2(id) ON DELETE CASCADE,
            category_id INTEGER NOT NULL REFERENCES categories_v2(id) ON DELETE CASCADE,
            title VARCHAR(200) NOT NULL,
            description TEXT,
            address TEXT,
            contact VARCHAR(100),
            google_maps_url TEXT,
            discount_text TEXT,
            status VARCHAR(20) DEFAULT 'pending',
            priority_level INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Создание таблицы фотографий карточек
        CREATE TABLE IF NOT EXISTS card_photos (
            id SERIAL PRIMARY KEY,
            card_id INTEGER NOT NULL REFERENCES cards_v2(id) ON DELETE CASCADE,
            file_id VARCHAR(200) NOT NULL,
            file_path VARCHAR(500),
            is_main BOOLEAN DEFAULT false,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Создание индексов для оптимизации
        CREATE INDEX IF NOT EXISTS idx_partners_tg_user_id ON partners_v2(tg_user_id);
        CREATE INDEX IF NOT EXISTS idx_cards_category_id ON cards_v2(category_id);
        CREATE INDEX IF NOT EXISTS idx_cards_status ON cards_v2(status);
        CREATE INDEX IF NOT EXISTS idx_cards_partner_id ON cards_v2(partner_id);
        CREATE INDEX IF NOT EXISTS idx_categories_slug ON categories_v2(slug);
        CREATE INDEX IF NOT EXISTS idx_categories_active ON categories_v2(is_active);
        """
        
        # Выполняем создание таблиц
        await conn.execute(create_tables_sql)
        logger.info("✅ Таблицы созданы успешно")
        
        # Добавляем тестовые данные
        await add_test_data(conn)
        
        await conn.close()
        logger.info("✅ Подключение закрыто")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка при создании таблиц: {e}")
        return False

async def add_test_data(conn):
    """Добавить тестовые данные"""
    
    logger.info("📊 Добавляем тестовые данные...")
    
    # Добавляем категории
    categories_data = [
        ('Рестораны', 'restaurants', '🍽️', 'Рестораны и кафе', 100),
        ('SPA и красота', 'spa', '💆', 'SPA, салоны красоты', 90),
        ('Транспорт', 'transport', '🚗', 'Такси, аренда авто', 80),
        ('Отели', 'hotels', '🏨', 'Отели и гостиницы', 70),
        ('Туры', 'tours', '✈️', 'Туристические услуги', 60),
        ('Магазины', 'shops', '🛍️', 'Магазины и торговля', 50)
    ]
    
    for name, slug, emoji, description, priority in categories_data:
        await conn.execute("""
            INSERT INTO categories_v2 (name, slug, emoji, description, priority_level)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (slug) DO NOTHING
        """, name, slug, emoji, description, priority)
    
    logger.info("✅ Категории добавлены")
    
    # Добавляем тестового партнера
    partner_result = await conn.fetchrow("""
        INSERT INTO partners_v2 (tg_user_id, display_name, phone, email, is_verified, is_active)
        VALUES ($1, $2, $3, $4, $5, $6)
        ON CONFLICT (tg_user_id) DO UPDATE SET display_name = EXCLUDED.display_name
        RETURNING id
    """, 7006636786, 'Тестовый партнер', '+7 (999) 123-45-67', 'test@example.com', True, True)
    
    partner_id = partner_result['id']
    logger.info(f"✅ Партнер создан/обновлен: ID={partner_id}")
    
    # Добавляем тестовые карточки
    cards_data = [
        (partner_id, 'restaurants', 'Ресторан "Вкусно"', 'Лучшие блюда города', 'ул. Центральная, 1', '+7 (999) 111-11-11', 'Скидка 20% на все блюда'),
        (partner_id, 'spa', 'SPA "Релакс"', 'Полный спектр SPA услуг', 'ул. Мира, 15', '+7 (999) 222-22-22', 'Скидка 30% на массаж'),
        (partner_id, 'transport', 'Такси "Быстро"', 'Быстрое и надежное такси', 'ул. Транспортная, 5', '+7 (999) 333-33-33', 'Скидка 15% на поездки'),
        (partner_id, 'hotels', 'Отель "Комфорт"', 'Уютные номера в центре', 'ул. Гостиничная, 10', '+7 (999) 444-44-44', 'Скидка 25% на проживание'),
        (partner_id, 'tours', 'Туры "Приключения"', 'Интересные экскурсии', 'ул. Туристическая, 3', '+7 (999) 555-55-55', 'Скидка 20% на туры'),
        (partner_id, 'shops', 'Магазин "Все для дома"', 'Товары для дома и сада', 'ул. Торговая, 7', '+7 (999) 666-66-66', 'Скидка 10% на все товары')
    ]
    
    for partner_id_val, category_slug, title, description, address, contact, discount in cards_data:
        # Получаем ID категории
        category_result = await conn.fetchrow("SELECT id FROM categories_v2 WHERE slug = $1", category_slug)
        if category_result:
            category_id = category_result['id']
            
            await conn.execute("""
                INSERT INTO cards_v2 (partner_id, category_id, title, description, address, contact, discount_text, status)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """, partner_id_val, category_id, title, description, address, contact, discount, 'approved')
    
    logger.info("✅ Тестовые карточки добавлены")
    logger.info("🎉 Тестовые данные успешно добавлены!")

async def main():
    """Основная функция"""
    logger.info("🚀 Создание таблиц PostgreSQL для KarmaBot")
    
    success = await create_tables()
    
    if success:
        logger.info("🎉 ВСЕ ГОТОВО! Таблицы созданы, тестовые данные добавлены")
        logger.info("✅ Теперь можно тестировать функции бота")
    else:
        logger.error("❌ Ошибка при создании таблиц")

if __name__ == "__main__":
    asyncio.run(main())
