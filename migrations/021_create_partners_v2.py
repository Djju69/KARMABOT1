"""
Миграция 021: Создание таблицы partners_v2 для PostgreSQL
"""

import asyncpg
import logging

logger = logging.getLogger(__name__)

async def upgrade_021(conn):
    """Создание таблицы partners_v2"""
    try:
        # Создаем таблицу partners_v2
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS partners_v2 (
                id SERIAL PRIMARY KEY,
                tg_user_id BIGINT UNIQUE NOT NULL,
                display_name VARCHAR(255),
                phone VARCHAR(50),
                email VARCHAR(255),
                is_verified BOOLEAN DEFAULT FALSE,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # Создаем таблицу categories_v2
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS categories_v2 (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                slug VARCHAR(50) UNIQUE NOT NULL,
                emoji VARCHAR(10),
                description TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                priority_level INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # Создаем таблицу cards_v2
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS cards_v2 (
                id SERIAL PRIMARY KEY,
                partner_id INTEGER REFERENCES partners_v2(id) ON DELETE CASCADE,
                category_id INTEGER REFERENCES categories_v2(id) ON DELETE RESTRICT,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                address VARCHAR(500),
                contact VARCHAR(255),
                google_maps_url VARCHAR(500),
                discount_text TEXT,
                status VARCHAR(50) DEFAULT 'pending',
                priority_level INTEGER DEFAULT 0,
                view_count INTEGER DEFAULT 0,
                is_featured BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # Создаем индексы
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_partners_v2_tg_user_id ON partners_v2(tg_user_id);
            CREATE INDEX IF NOT EXISTS idx_categories_v2_slug ON categories_v2(slug);
            CREATE INDEX IF NOT EXISTS idx_cards_v2_partner_id ON cards_v2(partner_id);
            CREATE INDEX IF NOT EXISTS idx_cards_v2_category_id ON cards_v2(category_id);
            CREATE INDEX IF NOT EXISTS idx_cards_v2_status ON cards_v2(status);
        """)
        
        # Вставляем базовые категории
        await conn.execute("""
            INSERT INTO categories_v2 (name, slug, emoji, description, is_active, priority_level)
            VALUES 
                ('Рестораны', 'restaurants', '🍽️', 'Рестораны и кафе', TRUE, 10),
                ('СПА и красота', 'spa', '💆', 'СПА, салоны красоты', TRUE, 9),
                ('Транспорт', 'transport', '🚗', 'Такси, аренда авто', TRUE, 8),
                ('Отели', 'hotels', '🏨', 'Отели и гостиницы', TRUE, 7),
                ('Туры', 'tours', '✈️', 'Туристические услуги', TRUE, 6),
                ('Магазины', 'shops', '🛍️', 'Розничная торговля', TRUE, 5)
            ON CONFLICT (slug) DO NOTHING
        """)
        
        logger.info("Migration 021 applied successfully: Created partners_v2, categories_v2, cards_v2 tables")
        
    except Exception as e:
        logger.error(f"Error applying migration 021: {str(e)}")
        raise

async def downgrade_021(conn):
    """Откат миграции 021"""
    try:
        await conn.execute("DROP TABLE IF EXISTS cards_v2")
        await conn.execute("DROP TABLE IF EXISTS categories_v2")
        await conn.execute("DROP TABLE IF EXISTS partners_v2")
        
        logger.info("Migration 021 downgraded successfully")
        
    except Exception as e:
        logger.error(f"Error downgrading migration 021: {str(e)}")
        raise
