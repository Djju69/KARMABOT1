"""
Миграция 017: Система лояльности и партнерская экосистема
Добавляет баллы лояльности, заведения партнеров и систему продаж
"""

import asyncpg
import logging

logger = logging.getLogger(__name__)

async def upgrade_017(conn):
    """Применение миграции 017"""
    try:
        # 1. Расширяем таблицу users для баллов лояльности
        await conn.execute("""
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS points_balance INTEGER DEFAULT 0,
            ADD COLUMN IF NOT EXISTS partner_id INTEGER
        """)
        
        # 2. Создаем таблицу истории баллов лояльности
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS points_history (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                change_amount INTEGER NOT NULL,
                reason VARCHAR(500),
                transaction_type VARCHAR(20) DEFAULT 'earned', -- earned, spent, bonus, admin_adjust, refund
                sale_id INTEGER, -- связь с продажей
                admin_id BIGINT, -- кто сделал операцию
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # 3. Создаем таблицу заведений партнеров (адаптируем существующую cards_v2)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS partner_places (
                id SERIAL PRIMARY KEY,
                partner_id INTEGER REFERENCES partners(id),
                title VARCHAR(60) NOT NULL,
                status VARCHAR(20) DEFAULT 'draft', -- draft, pending, published, hidden, rejected
                address VARCHAR(255),
                geo_lat NUMERIC(10,6),
                geo_lon NUMERIC(10,6),
                hours VARCHAR(120),
                phone VARCHAR(50),
                website VARCHAR(255),
                price_level VARCHAR(5), -- $, $$, $$$
                rating NUMERIC(3,1) DEFAULT 0,
                reviews_count INTEGER DEFAULT 0,
                description TEXT, -- до 600 символов
                base_discount_pct NUMERIC(5,2), -- переопределяет partners.base_discount_pct
                loyalty_accrual_pct NUMERIC(5,2) DEFAULT 5.00, -- % от чека на начисление
                min_redeem INTEGER DEFAULT 0, -- минимум баллов для списания
                max_percent_per_bill NUMERIC(5,2) DEFAULT 50.00, -- максимум % от чека
                cover_file_id TEXT, -- обложка
                gallery_file_ids JSONB DEFAULT '[]', -- до 10 фото
                categories JSONB DEFAULT '[]', -- до 3 категорий
                referral_bonus_1_10 INTEGER DEFAULT 5,
                referral_bonus_11_20 INTEGER DEFAULT 7,
                referral_bonus_over_20 INTEGER DEFAULT 3,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
                created_by BIGINT, -- кто создал карточку
                updated_by BIGINT  -- кто последний редактировал
            )
        """)
        
        # 4. Создаем таблицу логов модерации заведений
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS place_moderation_logs (
                id SERIAL PRIMARY KEY,
                place_id INTEGER REFERENCES partner_places(id),
                moderator_id BIGINT,
                action VARCHAR(30), -- submitted, edited, approved, rejected, hidden, published
                old_status VARCHAR(20),
                new_status VARCHAR(20),
                reason TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # 5. Создаем таблицу продаж партнеров
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS partner_sales (
                id SERIAL PRIMARY KEY,
                partner_id INTEGER REFERENCES partners(id),
                place_id INTEGER REFERENCES partner_places(id),
                operator_telegram_id BIGINT, -- партнер, который провел операцию
                user_telegram_id BIGINT,
                amount_gross NUMERIC(12,2) NOT NULL, -- сумма до скидок
                base_discount_pct NUMERIC(5,2) NOT NULL, -- B - скидка партнера
                extra_discount_pct NUMERIC(5,2) NOT NULL DEFAULT 0.00, -- E - доп скидка за баллы
                extra_value NUMERIC(12,2) NOT NULL DEFAULT 0.00, -- денежная часть доп скидки
                amount_partner_due NUMERIC(12,2) NOT NULL, -- к доплате партнеру
                amount_user_subsidy NUMERIC(12,2) NOT NULL, -- компенсация платформы
                points_spent INTEGER NOT NULL DEFAULT 0,
                points_earned INTEGER NOT NULL DEFAULT 0,
                redeem_rate NUMERIC(14,4) NOT NULL, -- курс в момент транзакции
                receipt VARCHAR(100), -- номер чека
                qr_token VARCHAR(255), -- JWT токен QR-кода
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # 6. Создаем таблицу конфигурации лояльности
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS platform_loyalty_config (
                id SERIAL PRIMARY KEY,
                redeem_rate NUMERIC(14,4) NOT NULL DEFAULT 5000.0, -- 1 балл = X денег (VND)
                rounding_rule VARCHAR(20) DEFAULT 'bankers',
                max_accrual_percent NUMERIC(5,2) DEFAULT 20.00, -- максимум начислений
                updated_at TIMESTAMP DEFAULT NOW(),
                updated_by BIGINT
            )
        """)
        
        # 7. Создаем индексы для производительности
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_points_history_user_id ON points_history(user_id);
            CREATE INDEX IF NOT EXISTS idx_points_history_created_at ON points_history(created_at);
            CREATE INDEX IF NOT EXISTS idx_partner_places_partner_id ON partner_places(partner_id);
            CREATE INDEX IF NOT EXISTS idx_partner_places_status ON partner_places(status);
            CREATE INDEX IF NOT EXISTS idx_partner_sales_partner_id ON partner_sales(partner_id);
            CREATE INDEX IF NOT EXISTS idx_partner_sales_user_id ON partner_sales(user_telegram_id);
            CREATE INDEX IF NOT EXISTS idx_partner_sales_created_at ON partner_sales(created_at);
        """)
        
        # 8. Вставляем дефолтную конфигурацию лояльности
        await conn.execute("""
            INSERT INTO platform_loyalty_config (redeem_rate, rounding_rule, max_accrual_percent)
            VALUES (5000.0, 'bankers', 20.00)
            ON CONFLICT DO NOTHING
        """)
        
        logger.info("Migration 017 applied successfully: Loyalty system and partner ecosystem")
        
    except Exception as e:
        logger.error(f"Error applying migration 017: {str(e)}")
        raise

async def downgrade_017(conn):
    """Откат миграции 017"""
    try:
        # Удаляем созданные таблицы
        await conn.execute("DROP TABLE IF EXISTS platform_loyalty_config")
        await conn.execute("DROP TABLE IF EXISTS partner_sales")
        await conn.execute("DROP TABLE IF EXISTS place_moderation_logs")
        await conn.execute("DROP TABLE IF EXISTS partner_places")
        await conn.execute("DROP TABLE IF EXISTS points_history")
        
        # Удаляем добавленные колонки
        await conn.execute("""
            ALTER TABLE users 
            DROP COLUMN IF EXISTS points_balance,
            DROP COLUMN IF EXISTS partner_id
        """)
        
        logger.info("Migration 017 downgraded successfully")
        
    except Exception as e:
        logger.error(f"Error downgrading migration 017: {str(e)}")
        raise
