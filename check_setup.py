#!/usr/bin/env python3
"""
Простой скрипт для проверки унификации БД
"""
import os
import sys

# Проверяем переменные окружения
print("🔍 ПРОВЕРКА ПЕРЕМЕННЫХ ОКРУЖЕНИЯ:")
print(f"DATABASE_URL: {'✅ Установлен' if os.getenv('DATABASE_URL') else '❌ Не установлен'}")
print(f"APP_ENV: {os.getenv('APP_ENV', 'Не установлен')}")
print(f"RAILWAY_ENVIRONMENT: {os.getenv('RAILWAY_ENVIRONMENT', 'Не установлен')}")

# Проверяем файлы
print("\n📁 ПРОВЕРКА ФАЙЛОВ:")
files_to_check = [
    'core/database/migrations.py',
    'core/database/postgresql_service.py', 
    'core/database/db_adapter.py',
    'test_database_unification.py'
]

for file_path in files_to_check:
    if os.path.exists(file_path):
        print(f"✅ {file_path}")
    else:
        print(f"❌ {file_path}")

print("\n🎯 ГОТОВО К ТЕСТИРОВАНИЮ!")
print("Запустите: python test_database_unification.py")
