#!/usr/bin/env python3
"""
Скрипт для унификации структуры базы данных PostgreSQL/SQLite
и добавления тестовых данных
"""
import os
import sys
import logging

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.database.migrations import unify_database_structure, add_sample_cards

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Основная функция для унификации БД"""
    try:
        logger.info("🚀 Начинаю унификацию структуры базы данных...")
        
        # ЭТАП 1: Унификация структуры
        logger.info("📋 ЭТАП 1: Унификация структуры PostgreSQL с SQLite")
        unify_database_structure()
        
        # ЭТАП 2: Добавление тестовых данных
        logger.info("📋 ЭТАП 2: Добавление тестовых карточек")
        add_sample_cards()
        
        logger.info("✅ Унификация базы данных завершена успешно!")
        logger.info("🎯 Теперь каталог бота должен показывать карточки во всех категориях")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при унификации БД: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
