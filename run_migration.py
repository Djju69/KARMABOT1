import asyncio
import asyncpg
import os

async def main():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL not found")
        return
    
    print(f"Connecting to PostgreSQL...")
    conn = await asyncpg.connect(database_url)
    
    try:
        # Create users table
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
        print("Users table created/verified")
        
        # Create user_notifications table
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
        print("User notifications table created/verified")
        
        # Create user_achievements table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS user_achievements (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                achievement_type VARCHAR(50) NOT NULL,
                achievement_data TEXT,
                earned_at TIMESTAMP DEFAULT NOW()
            )
        """)
        print("User achievements table created/verified")
        
        # Check users table
        count = await conn.fetchval("SELECT COUNT(*) FROM users")
        print(f"Users table has {count} records")
        
    finally:
        await conn.close()
    
    print("Migration completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())
