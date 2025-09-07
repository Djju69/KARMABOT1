"""
Миграция 016: Система кармы и пластиковых карт
"""
import sqlite3
from datetime import datetime

async def upgrade_016(conn):
    """Создает таблицы для системы кармы и пластиковых карт"""
    try:
        # Добавляем поле karma_points в таблицу users
        try:
            await conn.execute("""
                ALTER TABLE users ADD COLUMN karma_points INTEGER DEFAULT 0
            """)
            print("✅ Added karma_points column to users table")
        except:
            print("⚠️ karma_points column already exists")
        
        # Создаем таблицу karma_transactions
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS karma_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id BIGINT NOT NULL,
                amount INTEGER NOT NULL,
                reason TEXT,
                admin_id BIGINT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Created karma_transactions table")
        
        # Создаем таблицу cards_generated
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS cards_generated (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                card_id VARCHAR(20) UNIQUE NOT NULL,
                card_id_printable VARCHAR(20) NOT NULL,
                qr_url TEXT NOT NULL,
                created_by BIGINT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_blocked BOOLEAN DEFAULT FALSE,
                is_deleted BOOLEAN DEFAULT FALSE,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Created cards_generated table")
        
        # Создаем таблицу cards_binding
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS cards_binding (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id BIGINT NOT NULL,
                card_id VARCHAR(20) NOT NULL UNIQUE,
                card_id_printable VARCHAR(50),
                qr_url TEXT,
                bound_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status VARCHAR(20) DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Created cards_binding table")
        
        # Создаем таблицу complaints
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS complaints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_user_id BIGINT NOT NULL,
                target_user_id BIGINT NOT NULL,
                reason TEXT NOT NULL,
                description TEXT,
                status VARCHAR(20) DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved_at TIMESTAMP,
                resolved_by BIGINT
            )
        """)
        print("✅ Created complaints table")
        
        # Создаем таблицу thanks
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS thanks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_user_id BIGINT NOT NULL,
                target_user_id BIGINT NOT NULL,
                reason TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Created thanks table")
        
        # Создаем таблицу admin_logs
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS admin_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id BIGINT NOT NULL,
                action VARCHAR(50) NOT NULL,
                target_id VARCHAR(50),
                reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Created admin_logs table")
        
        # Создаем индексы для быстрого поиска
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_karma_transactions_user_id 
            ON karma_transactions(user_id)
        """)
        
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_cards_binding_telegram_id 
            ON cards_binding(telegram_id)
        """)
        
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_cards_binding_card_id 
            ON cards_binding(card_id)
        """)
        
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_cards_binding_status 
            ON cards_binding(status)
        """)
        
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_cards_generated_card_id 
            ON cards_generated(card_id)
        """)
        
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_complaints_target_user_id 
            ON complaints(target_user_id)
        """)
        
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_thanks_target_user_id 
            ON thanks(target_user_id)
        """)
        
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_admin_logs_admin_id 
            ON admin_logs(admin_id)
        """)
        
        print("✅ Created indexes for karma and cards tables")
        
        await conn.commit()
        print("🔗 Migration 016: Karma system and plastic cards tables created successfully")
        
    except Exception as e:
        print(f"❌ Error in migration 016: {e}")
        raise

async def downgrade_016(conn):
    """Удаляет таблицы системы кармы и пластиковых карт"""
    try:
        await conn.execute("DROP TABLE IF EXISTS admin_logs")
        await conn.execute("DROP TABLE IF EXISTS thanks")
        await conn.execute("DROP TABLE IF EXISTS complaints")
        await conn.execute("DROP TABLE IF EXISTS cards_binding")
        await conn.execute("DROP TABLE IF EXISTS cards_generated")
        await conn.execute("DROP TABLE IF EXISTS karma_transactions")
        
        # Удаляем поле karma_points из users (SQLite не поддерживает DROP COLUMN)
        # Это нужно делать вручную при необходимости
        
        await conn.commit()
        print("✅ Dropped karma system and plastic cards tables")
    except Exception as e:
        print(f"❌ Error dropping karma system tables: {e}")
        raise
