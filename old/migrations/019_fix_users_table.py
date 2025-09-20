"""
Миграция 019: Исправление таблицы users
Принудительно создает таблицу users если её нет
"""
import sqlite3
from datetime import datetime

async def upgrade_019(conn):
    """Принудительно создает таблицу users"""
    try:
        print("🔧 Force creating users table...")
        
        # Проверяем, существует ли таблица users
        try:
            await conn.fetchval("SELECT COUNT(*) FROM users LIMIT 1")
            print("✅ Users table already exists")
        except:
            print("❌ Users table does not exist, creating...")
            
            # Создаем таблицу users
            await conn.execute("""
                CREATE TABLE users (
                    id SERIAL PRIMARY KEY,
                    telegram_id BIGINT UNIQUE NOT NULL,
                    username VARCHAR(255),
                    first_name VARCHAR(255),
                    last_name VARCHAR(255),
                    language_code VARCHAR(10) DEFAULT 'ru',
                    karma_points INTEGER DEFAULT 0,
                    role VARCHAR(20) DEFAULT 'user',
                    reputation_score INTEGER DEFAULT 0,
                    level INTEGER DEFAULT 1,
                    is_banned BOOLEAN DEFAULT FALSE,
                    ban_reason TEXT,
                    banned_by BIGINT,
                    banned_at TIMESTAMP,
                    last_activity TIMESTAMP DEFAULT NOW(),
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """)
            print("✅ Users table created successfully")
        
        # Создаем таблицу user_notifications если её нет
        try:
            await conn.fetchval("SELECT COUNT(*) FROM user_notifications LIMIT 1")
            print("✅ user_notifications table already exists")
        except:
            print("❌ user_notifications table does not exist, creating...")
            await conn.execute("""
                CREATE TABLE user_notifications (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    message TEXT NOT NULL,
                    is_read BOOLEAN DEFAULT FALSE,
                    notification_type VARCHAR(50),
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            print("✅ user_notifications table created successfully")
        
        # Создаем таблицу user_achievements если её нет
        try:
            await conn.fetchval("SELECT COUNT(*) FROM user_achievements LIMIT 1")
            print("✅ user_achievements table already exists")
        except:
            print("❌ user_achievements table does not exist, creating...")
            await conn.execute("""
                CREATE TABLE user_achievements (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    achievement_type VARCHAR(50) NOT NULL,
                    achievement_data JSONB,
                    earned_at TIMESTAMP DEFAULT NOW()
                )
            """)
            print("✅ user_achievements table created successfully")
            
    except Exception as e:
        print(f"❌ Error in migration 019: {e}")
        raise

def upgrade_019_sqlite(conn):
    """SQLite версия миграции 019"""
    try:
        print("🔧 Force creating users table (SQLite)...")
        
        # Проверяем, существует ли таблица users
        try:
            conn.execute("SELECT COUNT(*) FROM users LIMIT 1").fetchone()
            print("✅ Users table already exists")
        except:
            print("❌ Users table does not exist, creating...")
            
            # Создаем таблицу users
            conn.execute("""
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER UNIQUE NOT NULL,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    language_code TEXT DEFAULT 'ru',
                    karma_points INTEGER DEFAULT 0,
                    role TEXT DEFAULT 'user',
                    reputation_score INTEGER DEFAULT 0,
                    level INTEGER DEFAULT 1,
                    is_banned BOOLEAN DEFAULT 0,
                    ban_reason TEXT,
                    banned_by INTEGER,
                    banned_at TEXT,
                    last_activity TEXT DEFAULT CURRENT_TIMESTAMP,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("✅ Users table created successfully")
        
        # Создаем таблицу user_notifications если её нет
        try:
            conn.execute("SELECT COUNT(*) FROM user_notifications LIMIT 1").fetchone()
            print("✅ user_notifications table already exists")
        except:
            print("❌ user_notifications table does not exist, creating...")
            conn.execute("""
                CREATE TABLE user_notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    message TEXT NOT NULL,
                    is_read BOOLEAN DEFAULT 0,
                    notification_type TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("✅ user_notifications table created successfully")
        
        # Создаем таблицу user_achievements если её нет
        try:
            conn.execute("SELECT COUNT(*) FROM user_achievements LIMIT 1").fetchone()
            print("✅ user_achievements table already exists")
        except:
            print("❌ user_achievements table does not exist, creating...")
            conn.execute("""
                CREATE TABLE user_achievements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    achievement_type TEXT NOT NULL,
                    achievement_data TEXT,
                    earned_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("✅ user_achievements table created successfully")
            
    except Exception as e:
        print(f"❌ Error in migration 019 (SQLite): {e}")
        raise
