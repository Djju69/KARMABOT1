"""
Миграция 018: Система личных кабинетов
Дополняет существующую схему базы данных согласно ТЗ
"""
import sqlite3
from datetime import datetime

async def upgrade_018(conn):
    """Дополняет схему базы данных для системы личных кабинетов"""
    try:
        # Дополняем таблицу users недостающими полями согласно ТЗ
        print("🔧 Updating users table...")
        
        # Добавляем поле role
        try:
            await conn.execute("""
                ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'user'
            """)
            print("✅ Added role column to users table")
        except:
            print("⚠️ role column already exists")
        
        # Добавляем поле reputation_score
        try:
            await conn.execute("""
                ALTER TABLE users ADD COLUMN reputation_score INTEGER DEFAULT 0
            """)
            print("✅ Added reputation_score column to users table")
        except:
            print("⚠️ reputation_score column already exists")
        
        # Добавляем поле level
        try:
            await conn.execute("""
                ALTER TABLE users ADD COLUMN level INTEGER DEFAULT 1
            """)
            print("✅ Added level column to users table")
        except:
            print("⚠️ level column already exists")
        
        # Добавляем поля для бана
        try:
            await conn.execute("""
                ALTER TABLE users ADD COLUMN is_banned BOOLEAN DEFAULT FALSE
            """)
            print("✅ Added is_banned column to users table")
        except:
            print("⚠️ is_banned column already exists")
        
        try:
            await conn.execute("""
                ALTER TABLE users ADD COLUMN ban_reason TEXT
            """)
            print("✅ Added ban_reason column to users table")
        except:
            print("⚠️ ban_reason column already exists")
        
        try:
            await conn.execute("""
                ALTER TABLE users ADD COLUMN banned_by BIGINT
            """)
            print("✅ Added banned_by column to users table")
        except:
            print("⚠️ banned_by column already exists")
        
        try:
            await conn.execute("""
                ALTER TABLE users ADD COLUMN banned_at TIMESTAMP
            """)
            print("✅ Added banned_at column to users table")
        except:
            print("⚠️ banned_at column already exists")
        
        # Добавляем поле last_activity
        try:
            await conn.execute("""
                ALTER TABLE users ADD COLUMN last_activity TIMESTAMP
            """)
            print("✅ Added last_activity column to users table")
        except:
            print("⚠️ last_activity column already exists")
        
        # Создаем таблицу user_notifications согласно ТЗ
        print("🔧 Creating user_notifications table...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS user_notifications (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                message TEXT NOT NULL,
                is_read BOOLEAN DEFAULT FALSE,
                notification_type VARCHAR(50), -- 'karma_change', 'card_bound', 'level_up', 'system'
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Created user_notifications table")
        
        # Создаем таблицу user_achievements согласно ТЗ
        print("🔧 Creating user_achievements table...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS user_achievements (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                achievement_type VARCHAR(50), -- 'first_card', 'karma_milestone', 'level_up'
                achievement_data JSON,
                earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Created user_achievements table")
        
        # Дополняем таблицу admin_logs согласно ТЗ
        print("🔧 Updating admin_logs table...")
        
        # Добавляем недостающие поля в admin_logs
        try:
            await conn.execute("""
                ALTER TABLE admin_logs ADD COLUMN target_user_id BIGINT
            """)
            print("✅ Added target_user_id column to admin_logs table")
        except:
            print("⚠️ target_user_id column already exists")
        
        try:
            await conn.execute("""
                ALTER TABLE admin_logs ADD COLUMN target_card_id VARCHAR(20)
            """)
            print("✅ Added target_card_id column to admin_logs table")
        except:
            print("⚠️ target_card_id column already exists")
        
        try:
            await conn.execute("""
                ALTER TABLE admin_logs ADD COLUMN details TEXT
            """)
            print("✅ Added details column to admin_logs table")
        except:
            print("⚠️ details column already exists")
        
        # Переименовываем поле reason в details если нужно
        try:
            await conn.execute("""
                ALTER TABLE admin_logs RENAME COLUMN reason TO details
            """)
            print("✅ Renamed reason to details in admin_logs table")
        except:
            print("⚠️ reason column already renamed or doesn't exist")
        
        # Дополняем таблицу cards_generated согласно ТЗ
        print("🔧 Updating cards_generated table...")
        
        try:
            await conn.execute("""
                ALTER TABLE cards_generated ADD COLUMN block_reason TEXT
            """)
            print("✅ Added block_reason column to cards_generated table")
        except:
            print("⚠️ block_reason column already exists")
        
        try:
            await conn.execute("""
                ALTER TABLE cards_generated ADD COLUMN blocked_by BIGINT
            """)
            print("✅ Added blocked_by column to cards_generated table")
        except:
            print("⚠️ blocked_by column already exists")
        
        try:
            await conn.execute("""
                ALTER TABLE cards_generated ADD COLUMN blocked_at TIMESTAMP
            """)
            print("✅ Added blocked_at column to cards_generated table")
        except:
            print("⚠️ blocked_at column already exists")
        
        # Создаем индексы для новых таблиц
        print("🔧 Creating indexes...")
        
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_notifications_user_id 
            ON user_notifications(user_id)
        """)
        
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_notifications_type 
            ON user_notifications(notification_type)
        """)
        
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_notifications_is_read 
            ON user_notifications(is_read)
        """)
        
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_achievements_user_id 
            ON user_achievements(user_id)
        """)
        
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_achievements_type 
            ON user_achievements(achievement_type)
        """)
        
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_role 
            ON users(role)
        """)
        
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_is_banned 
            ON users(is_banned)
        """)
        
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_level 
            ON users(level)
        """)
        
        print("✅ Created indexes for personal cabinets tables")
        
        await conn.commit()
        print("🔗 Migration 018: Personal cabinets schema updated successfully")
        
    except Exception as e:
        print(f"❌ Error in migration 018: {e}")
        raise

async def downgrade_018(conn):
    """Откатывает изменения схемы для системы личных кабинетов"""
    try:
        # Удаляем новые таблицы
        await conn.execute("DROP TABLE IF EXISTS user_achievements")
        await conn.execute("DROP TABLE IF EXISTS user_notifications")
        
        # Удаляем индексы
        await conn.execute("DROP INDEX IF EXISTS idx_user_notifications_user_id")
        await conn.execute("DROP INDEX IF EXISTS idx_user_notifications_type")
        await conn.execute("DROP INDEX IF EXISTS idx_user_notifications_is_read")
        await conn.execute("DROP INDEX IF EXISTS idx_user_achievements_user_id")
        await conn.execute("DROP INDEX IF EXISTS idx_user_achievements_type")
        await conn.execute("DROP INDEX IF EXISTS idx_users_role")
        await conn.execute("DROP INDEX IF EXISTS idx_users_is_banned")
        await conn.execute("DROP INDEX IF EXISTS idx_users_level")
        
        # Примечание: В PostgreSQL можно удалить колонки, но это может быть опасно
        # Лучше оставить колонки для безопасности данных
        
        await conn.commit()
        print("✅ Rolled back personal cabinets schema changes")
    except Exception as e:
        print(f"❌ Error rolling back personal cabinets schema: {e}")
        raise
