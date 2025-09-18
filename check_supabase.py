#!/usr/bin/env python3
"""
Проверка настроек Supabase
"""
import os
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_env_vars():
    """Проверка переменных окружения"""
    logger.info("🔍 Проверяем переменные окружения...")
    
    # Проверяем DATABASE_URL
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        logger.error("❌ DATABASE_URL не установлена!")
        logger.info("💡 Нужно настроить подключение к Supabase PostgreSQL")
        return False
    
    logger.info(f"✅ DATABASE_URL: {db_url[:50]}...")
    
    # Проверяем тип базы данных
    if db_url.startswith("postgresql://"):
        logger.info("✅ Используется PostgreSQL (Supabase)")
        return True
    elif db_url.startswith("sqlite://"):
        logger.warning("⚠️ Используется SQLite (локальная разработка)")
        logger.info("💡 Для продакшена нужен PostgreSQL (Supabase)")
        return False
    else:
        logger.warning(f"⚠️ Неизвестный тип БД: {db_url[:20]}...")
        return False

def check_migrations():
    """Проверка настроек миграций"""
    logger.info("🔍 Проверяем настройки миграций...")
    
    apply_migrations = os.getenv("APPLY_MIGRATIONS", "0")
    logger.info(f"APPLY_MIGRATIONS: {apply_migrations}")
    
    if apply_migrations == "1":
        logger.info("✅ Миграции включены")
        return True
    else:
        logger.warning("⚠️ Миграции отключены")
        logger.info("💡 Установите APPLY_MIGRATIONS=1 для создания таблиц")
        return False

async def test_supabase_connection():
    """Тест подключения к Supabase"""
    logger.info("🔍 Тестируем подключение к Supabase...")
    
    try:
        import asyncpg
        
        db_url = os.getenv("DATABASE_URL")
        if not db_url or not db_url.startswith("postgresql://"):
            logger.error("❌ DATABASE_URL не настроена для PostgreSQL")
            return False
        
        # Подключаемся к базе
        conn = await asyncpg.connect(db_url)
        
        # Проверяем версию PostgreSQL
        version = await conn.fetchval("SELECT version()")
        logger.info(f"✅ Подключение к PostgreSQL успешно!")
        logger.info(f"📊 Версия: {version[:50]}...")
        
        # Проверяем существующие таблицы
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        if tables:
            logger.info(f"✅ Найдено таблиц: {len(tables)}")
            for table in tables[:5]:  # Показываем первые 5
                logger.info(f"  📋 {table['table_name']}")
            if len(tables) > 5:
                logger.info(f"  ... и еще {len(tables) - 5} таблиц")
        else:
            logger.warning("⚠️ Таблицы не найдены")
            logger.info("💡 Нужно запустить миграции (APPLY_MIGRATIONS=1)")
        
        await conn.close()
        return True
        
    except ImportError:
        logger.error("❌ asyncpg не установлен")
        logger.info("💡 Установите: pip install asyncpg")
        return False
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к Supabase: {e}")
        return False

def main():
    """Главная функция"""
    logger.info("🚀 Проверка настроек Supabase...")
    
    # Проверяем переменные
    env_ok = check_env_vars()
    migrations_ok = check_migrations()
    
    if not env_ok:
        logger.error("\n❌ ПРОБЛЕМА: DATABASE_URL не настроена")
        logger.info("📋 РЕШЕНИЕ:")
        logger.info("1. Создайте проект в Supabase")
        logger.info("2. Скопируйте Connection string")
        logger.info("3. Установите DATABASE_URL в переменные окружения")
        logger.info("4. Установите APPLY_MIGRATIONS=1")
        return False
    
    if not migrations_ok:
        logger.warning("\n⚠️ ПРОБЛЕМА: Миграции отключены")
        logger.info("📋 РЕШЕНИЕ:")
        logger.info("1. Установите APPLY_MIGRATIONS=1")
        logger.info("2. Перезапустите бота")
        return False
    
    # Тестируем подключение
    logger.info("\n🧪 Тестируем подключение...")
    try:
        result = asyncio.run(test_supabase_connection())
        if result:
            logger.info("\n🎉 ВСЕ НАСТРОЙКИ КОРРЕКТНЫ!")
            logger.info("✅ Supabase подключен")
            logger.info("✅ Миграции включены")
            logger.info("✅ Функции создания карточек и партнерства должны работать")
        else:
            logger.error("\n❌ ЕСТЬ ПРОБЛЕМЫ С ПОДКЛЮЧЕНИЕМ")
    except Exception as e:
        logger.error(f"\n❌ Ошибка тестирования: {e}")
    
    return True

if __name__ == "__main__":
    main()
