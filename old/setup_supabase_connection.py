#!/usr/bin/env python3
"""
Быстрая настройка подключения к Supabase для проекта svtotgesqufeazjkztlv
"""
import os
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Данные вашего Supabase проекта
SUPABASE_PROJECT_URL = "https://svtotgesqufeazjkztlv.supabase.co"
SUPABASE_PROJECT_REF = "svtotgesqufeazjkztlv"
SUPABASE_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InN2dG90Z2VzcXVmZWF6amt6dGx2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTgxOTc3NTEsImV4cCI6MjA3Mzc3Mzc1MX0.SzPMTuCokyTuoYLmP7tKBLDmsa_YklvA2DW6yhaRYro"

def create_env_file():
    """Создать .env файл с настройками Supabase"""
    logger.info("🔧 Создаем .env файл с настройками Supabase...")
    
    # Запрашиваем пароль от базы данных
    print("\n🔑 Введите пароль от Supabase базы данных:")
    print("(Пароль был создан при создании проекта)")
    db_password = input("Password: ").strip()
    
    if not db_password:
        logger.error("❌ Пароль не может быть пустым!")
        return False
    
    # Создаем DATABASE_URL
    database_url = f"postgresql://postgres:{db_password}@db.{SUPABASE_PROJECT_REF}.supabase.co:5432/postgres"
    
    # Создаем .env файл
    env_content = f"""# Supabase Configuration
DATABASE_URL={database_url}
APPLY_MIGRATIONS=1

# Supabase API
SUPABASE_URL={SUPABASE_PROJECT_URL}
SUPABASE_KEY={SUPABASE_API_KEY}

# Bot Configuration (заполните сами)
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
    """Тестируем подключение к Supabase"""
    logger.info("🧪 Тестируем подключение к Supabase...")
    
    try:
        import asyncpg
        
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            logger.error("❌ DATABASE_URL не найдена в переменных окружения")
            logger.info("💡 Запустите скрипт снова и создайте .env файл")
            return False
        
        # Подключаемся к базе
        conn = await asyncpg.connect(db_url)
        
        # Проверяем версию PostgreSQL
        version = await conn.fetchval("SELECT version()")
        logger.info(f"✅ Подключение к Supabase успешно!")
        logger.info(f"📊 Версия PostgreSQL: {version[:50]}...")
        
        # Проверяем существующие таблицы
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        if tables:
            logger.info(f"✅ Найдено таблиц: {len(tables)}")
            for table in tables[:5]:
                logger.info(f"  📋 {table['table_name']}")
            if len(tables) > 5:
                logger.info(f"  ... и еще {len(tables) - 5} таблиц")
        else:
            logger.info("ℹ️ Таблицы не найдены - это нормально для нового проекта")
            logger.info("💡 Миграции создадут нужные таблицы при запуске бота")
        
        await conn.close()
        return True
        
    except ImportError:
        logger.error("❌ asyncpg не установлен")
        logger.info("💡 Установите: pip install asyncpg")
        return False
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к Supabase: {e}")
        logger.info("💡 Проверьте правильность пароля")
        return False

def show_railway_instructions():
    """Показать инструкции для Railway"""
    logger.info("\n🚀 ИНСТРУКЦИИ ДЛЯ RAILWAY:")
    logger.info("="*50)
    
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        logger.info("1. Зайти в Railway Dashboard")
        logger.info("2. Перейти в Variables")
        logger.info("3. Добавить переменные:")
        logger.info(f"   DATABASE_URL={db_url}")
        logger.info("   APPLY_MIGRATIONS=1")
        logger.info("4. Перезапустить бота")
    else:
        logger.info("Сначала создайте .env файл с правильным паролем")

def main():
    """Главная функция"""
    logger.info("🚀 Настройка подключения к Supabase")
    logger.info(f"📊 Проект: {SUPABASE_PROJECT_URL}")
    
    # Проверяем есть ли уже .env файл
    if os.path.exists('.env'):
        logger.info("✅ .env файл уже существует")
        choice = input("Пересоздать? (y/n): ").strip().lower()
        if choice != 'y':
            logger.info("ℹ️ Используем существующий .env файл")
        else:
            if not create_env_file():
                return False
    else:
        if not create_env_file():
            return False
    
    # Загружаем переменные из .env
    try:
        from dotenv import load_dotenv
        load_dotenv()
        logger.info("✅ Переменные окружения загружены из .env")
    except ImportError:
        logger.warning("⚠️ python-dotenv не установлен, переменные не загружены")
        logger.info("💡 Установите: pip install python-dotenv")
    
    # Тестируем подключение
    logger.info("\n🧪 Тестируем подключение...")
    try:
        result = asyncio.run(test_connection())
        if result:
            logger.info("\n🎉 НАСТРОЙКА ЗАВЕРШЕНА!")
            logger.info("✅ Supabase подключен")
            logger.info("✅ Миграции включены")
            logger.info("✅ Функции создания карточек и партнерства должны работать")
            
            show_railway_instructions()
        else:
            logger.error("\n❌ ЕСТЬ ПРОБЛЕМЫ С ПОДКЛЮЧЕНИЕМ")
            logger.info("💡 Проверьте правильность пароля в .env файле")
    except Exception as e:
        logger.error(f"\n❌ Ошибка тестирования: {e}")
    
    return True

if __name__ == "__main__":
    main()
