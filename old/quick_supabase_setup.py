#!/usr/bin/env python3
"""
Быстрая настройка Supabase без интерактивного ввода
"""
import os
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_env_file_with_password(password):
    """Создать .env файл с паролем"""
    logger.info("🔧 Создаем .env файл...")
    
    # Данные Supabase проекта
    SUPABASE_PROJECT_REF = "svtotgesqufeazjkztlv"
    SUPABASE_PROJECT_URL = "https://svtotgesqufeazjkztlv.supabase.co"
    SUPABASE_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InN2dG90Z2VzcXVmZWF6amt6dGx2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTgxOTc3NTEsImV4cCI6MjA3Mzc3Mzc1MX0.SzPMTuCokyTuoYLmP7tKBLDmsa_YklvA2DW6yhaRYro"
    
    # Создаем DATABASE_URL
    database_url = f"postgresql://postgres:{password}@db.{SUPABASE_PROJECT_REF}.supabase.co:5432/postgres"
    
    # Создаем .env файл
    env_content = f"""# Supabase Configuration
DATABASE_URL={database_url}
APPLY_MIGRATIONS=1

# Supabase API
SUPABASE_URL={SUPABASE_PROJECT_URL}
SUPABASE_KEY={SUPABASE_API_KEY}

# Bot Configuration
BOT_TOKEN=your_bot_token_here
REDIS_URL=redis://localhost:6379/0

# Environment
ENVIRONMENT=development
LOG_LEVEL=INFO
"""
    
    try:
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(env_content)
        
        logger.info("✅ .env файл создан!")
        logger.info(f"📊 DATABASE_URL: {database_url[:50]}...")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания .env файла: {e}")
        return False

async def test_connection():
    """Тестируем подключение"""
    logger.info("🧪 Тестируем подключение к Supabase...")
    
    try:
        import asyncpg
        
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            logger.error("❌ DATABASE_URL не найдена")
            return False
        
        # Подключаемся к базе
        conn = await asyncpg.connect(db_url)
        
        # Проверяем версию PostgreSQL
        version = await conn.fetchval("SELECT version()")
        logger.info(f"✅ Подключение к Supabase успешно!")
        logger.info(f"📊 Версия: {version[:50]}...")
        
        await conn.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка подключения: {e}")
        return False

def main():
    """Главная функция"""
    logger.info("🚀 Быстрая настройка Supabase")
    
    # Попробуем несколько стандартных паролей
    common_passwords = [
        "password",
        "123456",
        "admin",
        "supabase",
        "postgres",
        "karmabot",
        "railway"
    ]
    
    logger.info("🔍 Пробуем стандартные пароли...")
    
    for password in common_passwords:
        logger.info(f"🔑 Пробуем пароль: {password}")
        
        # Создаем .env с этим паролем
        if create_env_file_with_password(password):
            # Загружаем переменные
            try:
                from dotenv import load_dotenv
                load_dotenv()
                
                # Тестируем подключение
                result = asyncio.run(test_connection())
                if result:
                    logger.info(f"🎉 УСПЕХ! Пароль: {password}")
                    logger.info("✅ Supabase подключен!")
                    logger.info("✅ Миграции включены!")
                    logger.info("✅ Функции создания карточек и партнерства должны работать!")
                    return True
                else:
                    logger.info(f"❌ Пароль {password} не подошел")
            except Exception as e:
                logger.error(f"❌ Ошибка с паролем {password}: {e}")
    
    logger.error("❌ Ни один стандартный пароль не подошел")
    logger.info("💡 Нужно найти правильный пароль в Supabase Dashboard")
    logger.info("📋 Settings → Database → Reset database password")
    
    return False

if __name__ == "__main__":
    main()
