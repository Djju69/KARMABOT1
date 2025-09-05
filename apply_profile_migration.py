#!/usr/bin/env python3
"""
Скрипт для применения миграции системы профилей пользователей
"""
import sqlite3
import os
import sys
from pathlib import Path

def apply_migration():
    """Применить миграцию системы профилей пользователей"""
    try:
        # Путь к базе данных
        db_path = "core/database/karmabot.db"
        
        if not os.path.exists(db_path):
            print(f"❌ База данных не найдена: {db_path}")
            return False
        
        # Читаем миграцию
        migration_file = "migrations/014_user_profile_system.sql"
        if not os.path.exists(migration_file):
            print(f"❌ Файл миграции не найден: {migration_file}")
            return False
        
        with open(migration_file, 'r', encoding='utf-8') as f:
            migration_sql = f.read()
        
        print("🚀 Применяем миграцию системы профилей пользователей...")
        
        # Подключаемся к базе данных
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Выполняем миграцию
        cursor.executescript(migration_sql)
        
        # Проверяем созданные таблицы
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'user_%'")
        tables = cursor.fetchall()
        
        print("✅ Миграция применена успешно!")
        print("📊 Созданные таблицы:")
        for table in tables:
            print(f"  - {table[0]}")
        
        # Проверяем индексы
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_user_%'")
        indexes = cursor.fetchall()
        
        print("🔍 Созданные индексы:")
        for index in indexes:
            print(f"  - {index[0]}")
        
        # Проверяем триггеры
        cursor.execute("SELECT name FROM sqlite_master WHERE type='trigger' AND name LIKE '%user%'")
        triggers = cursor.fetchall()
        
        print("⚡ Созданные триггеры:")
        for trigger in triggers:
            print(f"  - {trigger[0]}")
        
        conn.commit()
        conn.close()
        
        print("\n🎉 Система профилей пользователей готова к работе!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка применения миграции: {e}")
        return False

def test_profile_system():
    """Тестирование системы профилей"""
    try:
        print("\n🧪 Тестируем систему профилей...")
        
        # Импортируем сервис
        sys.path.append('.')
        from core.services.user_profile_service import user_profile_service
        from core.models.user_profile import UserLevel
        
        print("✅ Сервис профилей пользователей импортирован успешно")
        
        # Проверяем настройки
        print(f"📊 Пороги уровней: {user_profile_service.level_thresholds}")
        print(f"🎁 Бонусы уровней: {user_profile_service.level_bonuses}")
        
        # Проверяем уровни
        print(f"🏆 Доступные уровни: {[level.value for level in UserLevel]}")
        
        print("✅ Система профилей готова к работе!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        return False

def main():
    """Основная функция"""
    print("🎯 Применение миграции системы профилей пользователей")
    print("=" * 60)
    
    # Применяем миграцию
    if not apply_migration():
        sys.exit(1)
    
    # Тестируем систему
    if not test_profile_system():
        sys.exit(1)
    
    print("\n🎉 ВСЕ ГОТОВО!")
    print("📋 Что было сделано:")
    print("  ✅ Создана модель UserProfile с системой уровней")
    print("  ✅ Создан сервис UserProfileService")
    print("  ✅ Добавлены обработчики для личного кабинета")
    print("  ✅ Обновлена локализация")
    print("  ✅ Создана миграция базы данных")
    print("  ✅ Добавлены триггеры для автоматического обновления статистики")
    
    print("\n🚀 Система готова к использованию!")
    print("💡 Следующие шаги:")
    print("  1. Запустить бота и протестировать личный кабинет")
    print("  2. Проверить систему уровней и достижений")
    print("  3. Протестировать QR-коды в личном кабинете")

if __name__ == "__main__":
    main()
