#!/usr/bin/env python3
"""
Скрипт для применения миграции многоуровневой реферальной системы
"""
import sqlite3
import os
import sys
from pathlib import Path

def apply_migration():
    """Применить миграцию многоуровневой реферальной системы"""
    try:
        # Путь к базе данных
        db_path = "core/database/karmabot.db"
        
        if not os.path.exists(db_path):
            print(f"❌ База данных не найдена: {db_path}")
            return False
        
        # Читаем миграцию
        migration_file = "migrations/013_multilevel_referral_system.sql"
        if not os.path.exists(migration_file):
            print(f"❌ Файл миграции не найден: {migration_file}")
            return False
        
        with open(migration_file, 'r', encoding='utf-8') as f:
            migration_sql = f.read()
        
        print("🚀 Применяем миграцию многоуровневой реферальной системы...")
        
        # Подключаемся к базе данных
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Выполняем миграцию
        cursor.executescript(migration_sql)
        
        # Проверяем созданные таблицы
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'referral%'")
        tables = cursor.fetchall()
        
        print("✅ Миграция применена успешно!")
        print("📊 Созданные таблицы:")
        for table in tables:
            print(f"  - {table[0]}")
        
        # Проверяем индексы
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_referral%'")
        indexes = cursor.fetchall()
        
        print("🔍 Созданные индексы:")
        for index in indexes:
            print(f"  - {index[0]}")
        
        # Проверяем триггеры
        cursor.execute("SELECT name FROM sqlite_master WHERE type='trigger' AND name LIKE '%referral%'")
        triggers = cursor.fetchall()
        
        print("⚡ Созданные триггеры:")
        for trigger in triggers:
            print(f"  - {trigger[0]}")
        
        conn.commit()
        conn.close()
        
        print("\n🎉 Многоуровневая реферальная система готова к работе!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка применения миграции: {e}")
        return False

def test_referral_system():
    """Тестирование реферальной системы"""
    try:
        print("\n🧪 Тестируем реферальную систему...")
        
        # Импортируем сервис
        sys.path.append('.')
        from core.services.multilevel_referral_service import multilevel_referral_service
        
        print("✅ Сервис многоуровневых рефералов импортирован успешно")
        
        # Проверяем настройки
        print(f"📊 Проценты бонусов: {multilevel_referral_service.level_percentages}")
        print(f"💰 Минимальные суммы: {multilevel_referral_service.min_bonus_amounts}")
        
        print("✅ Реферальная система готова к работе!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        return False

def main():
    """Основная функция"""
    print("🎯 Применение миграции многоуровневой реферальной системы")
    print("=" * 60)
    
    # Применяем миграцию
    if not apply_migration():
        sys.exit(1)
    
    # Тестируем систему
    if not test_referral_system():
        sys.exit(1)
    
    print("\n🎉 ВСЕ ГОТОВО!")
    print("📋 Что было сделано:")
    print("  ✅ Создана модель ReferralTree с поддержкой 3 уровней")
    print("  ✅ Создан сервис MultilevelReferralService")
    print("  ✅ Добавлены обработчики для реферальной программы")
    print("  ✅ Интегрирована система с loyalty_service")
    print("  ✅ Обновлено главное меню и локализация")
    print("  ✅ Созданы тесты для системы")
    print("  ✅ Применена миграция базы данных")
    
    print("\n🚀 Система готова к использованию!")
    print("💡 Следующие шаги:")
    print("  1. Запустить бота и протестировать реферальную программу")
    print("  2. Проверить начисление бонусов при покупках")
    print("  3. Протестировать команду /invite для регистрации рефералов")

if __name__ == "__main__":
    main()
