import asyncpg
import logging

logger = logging.getLogger(__name__)

async def upgrade_021(conn):
    """
    Migration 021: Create partners_v2, categories_v2, and cards_v2 tables for PostgreSQL.
    This migration ensures that the core tables for the loyalty system are present in the PostgreSQL database.
    """
    try:
        # Create partners_v2 table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS partners_v2 (
                id SERIAL PRIMARY KEY,
                tg_user_id BIGINT NOT NULL UNIQUE,
                display_name VARCHAR(255) NOT NULL,
                username VARCHAR(255),
                phone VARCHAR(20),
                email VARCHAR(255),
                status VARCHAR(50) DEFAULT 'pending',
                karma_points INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        logger.info("Table 'partners_v2' created or already exists.")

        # Create categories_v2 table
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
            );
        """)
        logger.info("Table 'categories_v2' created or already exists.")

        # Insert base categories
        await conn.execute("""
            INSERT INTO categories_v2 (name, slug, emoji, description, is_active, priority_level)
            VALUES
                ('Рестораны', 'restaurants', '🍽️', 'Рестораны и кафе', TRUE, 10),
                ('СПА и красота', 'spa', '💆', 'СПА, салоны красоты', TRUE, 9),
                ('Транспорт', 'transport', '🚗', 'Такси, аренда авто', TRUE, 8),
                ('Отели', 'hotels', '🏨', 'Отели и гостиницы', TRUE, 7),
                ('Туры', 'tours', '✈️', 'Туристические услуги', TRUE, 6),
                ('Магазины', 'shops', '🛍️', 'Розничная торговля', TRUE, 5)
            ON CONFLICT (slug) DO NOTHING;
        """)
        logger.info("Base categories inserted or already exist.")

        # Create cards_v2 table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS cards_v2 (
                id SERIAL PRIMARY KEY,
                partner_id INTEGER NOT NULL,
                category_id INTEGER NOT NULL,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                address VARCHAR(500),
                contact VARCHAR(255),
                google_maps_url VARCHAR(500),
                discount_text TEXT,
                status VARCHAR(50) DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (partner_id) REFERENCES partners_v2(id) ON DELETE CASCADE,
                FOREIGN KEY (category_id) REFERENCES categories_v2(id) ON DELETE CASCADE
            );
        """)
        logger.info("Table 'cards_v2' created or already exists.")

        # Create indexes
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_partners_v2_tg_user_id ON partners_v2(tg_user_id);
            CREATE INDEX IF NOT EXISTS idx_partners_v2_status ON partners_v2(status);
            CREATE INDEX IF NOT EXISTS idx_cards_v2_partner_id ON cards_v2(partner_id);
            CREATE INDEX IF NOT EXISTS idx_cards_v2_category_id ON cards_v2(category_id);
            CREATE INDEX IF NOT EXISTS idx_cards_v2_status ON cards_v2(status);
        """)
        logger.info("Indexes created or already exist.")

        logger.info("Migration 021 applied successfully: Created partners_v2, categories_v2, cards_v2 tables.")

    except Exception as e:
        logger.error(f"Error applying migration 021: {str(e)}")
        raise

async def downgrade_021(conn):
    """Откат миграции 021"""
    try:
        await conn.execute("DROP TABLE IF EXISTS cards_v2 CASCADE;")
        await conn.execute("DROP TABLE IF EXISTS categories_v2 CASCADE;")
        await conn.execute("DROP TABLE IF EXISTS partners_v2 CASCADE;")
        logger.info("Migration 021 downgraded successfully.")
    except Exception as e:
        logger.error(f"Error downgrading migration 021: {str(e)}")
        raise
