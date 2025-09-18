#!/usr/bin/env python3
"""
Проверка критически важных файлов
"""
import os
import sys

def check_critical_files():
    """Проверяем наличие критически важных файлов"""
    print("🔍 Проверка критически важных файлов...")
    
    critical_files = [
        # Главные файлы
        "main_v2.py",
        "bot/bot.py",
        
        # Конфигурация
        "core/config.py",
        
        # База данных
        "core/database/__init__.py",
        "core/database/database.py",
        
        # Модели
        "core/models/user.py",
        "core/models/user_settings.py",
        
        # Сервисы
        "core/services/profile_service.py",
        "core/services/loyalty_service.py",
        "core/services/referral_service.py",
        "core/services/qr_code_service.py",
        
        # Обработчики
        "core/handlers/basic.py",
        "core/handlers/callback.py",
        
        # Клавиатуры
        "core/keyboards/restaurant_keyboards.py",
        "core/keyboards/language_keyboard.py",
        
        # Исключения
        "core/common/exceptions.py",
        
        # Зависимости
        "requirements.txt"
    ]
    
    missing_files = []
    existing_files = []
    
    for file_path in critical_files:
        if os.path.exists(file_path):
            existing_files.append(file_path)
            print(f"   ✅ {file_path}")
        else:
            missing_files.append(file_path)
            print(f"   ❌ {file_path} - ОТСУТСТВУЕТ!")
    
    print(f"\n📊 Результат:")
    print(f"   ✅ Найдено: {len(existing_files)} файлов")
    print(f"   ❌ Отсутствует: {len(missing_files)} файлов")
    
    if missing_files:
        print(f"\n🚨 КРИТИЧЕСКИЕ ФАЙЛЫ ОТСУТСТВУЮТ:")
        for file_path in missing_files:
            print(f"   - {file_path}")
        return False
    else:
        print(f"\n🎉 ВСЕ КРИТИЧЕСКИЕ ФАЙЛЫ НА МЕСТЕ!")
        return True

def check_directories():
    """Проверяем критические директории"""
    print("\n📁 Проверка критических директорий...")
    
    critical_dirs = [
        "core",
        "core/database",
        "core/handlers", 
        "core/keyboards",
        "core/services",
        "core/models",
        "core/common",
        "bot",
        "web",
        "tests"
    ]
    
    for dir_path in critical_dirs:
        if os.path.isdir(dir_path):
            file_count = len([f for f in os.listdir(dir_path) if f.endswith('.py')])
            print(f"   ✅ {dir_path} ({file_count} .py файлов)")
        else:
            print(f"   ❌ {dir_path} - ОТСУТСТВУЕТ!")

if __name__ == "__main__":
    print("=" * 60)
    print("🔍 ПРОВЕРКА КРИТИЧЕСКИ ВАЖНЫХ ФАЙЛОВ KARMABOT1")
    print("=" * 60)
    
    files_ok = check_critical_files()
    check_directories()
    
    print("\n" + "=" * 60)
    if files_ok:
        print("✅ ПРОЕКТ ГОТОВ К РАБОТЕ!")
    else:
        print("❌ ЕСТЬ КРИТИЧЕСКИЕ ПРОБЛЕМЫ!")
    print("=" * 60)
