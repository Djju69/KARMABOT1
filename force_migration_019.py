#!/usr/bin/env python3
"""
Принудительное выполнение миграции 019 для PostgreSQL
Обходит проверку "уже применена" и создает таблицу users
"""
import asyncio
import asyncpg
import os
import sys

async def force_migration_019():
    """Принудительно выполнить миграцию 019 для PostgreSQL"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL не найден")
        return False
    
    if not database_url.startswith("postgresql"):
        print("❌ Это не PostgreSQL база данных")
        return False
    
    print(f"🔧 Подключаемся к PostgreSQL: {database_url[:50]}...")
    
    try:
        conn = await asyncpg.connect(database_url)
        print("✅ Подключение к PostgreSQL установлено")
        
        # Принудительно создаем таблицу users
        print("🔧 Принудительно создаем таблицу users...")
        
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
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
        print("✅ Таблица users создана/проверена")
        
        # Создаем таблицу user_notifications
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS user_notifications (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                message TEXT NOT NULL,
                is_read BOOLEAN DEFAULT FALSE,
                notification_type VARCHAR(50),
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        print("✅ Таблица user_notifications создана/проверена")
        
        # Создаем таблицу user_achievements
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS user_achievements (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                achievement_type VARCHAR(50) NOT NULL,
                achievement_data TEXT,
                earned_at TIMESTAMP DEFAULT NOW()
            )
        """)
        print("✅ Таблица user_achievements создана/проверена")
        
        # Проверяем, что таблица users существует
        result = await conn.fetchval("SELECT COUNT(*) FROM users")
        print(f"✅ Таблица users содержит {result} записей")
        
        await conn.close()
        print("🎉 Миграция 019 выполнена успешно!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при выполнении миграции: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Принудительное выполнение миграции 019 для PostgreSQL")
    success = asyncio.run(force_migration_019())
    if success:
        print("✅ Миграция завершена успешно!")
        sys.exit(0)
    else:
        print("❌ Миграция завершилась с ошибкой!")
        sys.exit(1)
