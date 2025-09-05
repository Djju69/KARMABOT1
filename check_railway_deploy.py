#!/usr/bin/env python3
"""
Railway Deployment Readiness Check
Проверяет готовность проекта к деплою на Railway
"""

import os
import sys
import subprocess
from pathlib import Path

def check_file_exists(file_path, description):
    """Проверяет существование файла"""
    if os.path.exists(file_path):
        print(f"✅ {description}: {file_path}")
        return True
    else:
        print(f"❌ {description}: {file_path} - НЕ НАЙДЕН")
        return False

def check_imports():
    """Проверяет импорты основных модулей"""
    try:
        # Проверяем основные импорты
        from web.main import app
        print("✅ Web app импорт: OK")
        
        from bot.bot import bot
        print("✅ Bot импорт: OK")
        
        from core.database import get_db
        print("✅ Database импорт: OK")
        
        return True
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        return False

def check_requirements():
    """Проверяет requirements.txt"""
    if not os.path.exists("requirements.txt"):
        print("❌ requirements.txt не найден")
        return False
    
    try:
        with open("requirements.txt", "r") as f:
            requirements = f.read()
        
        # Проверяем ключевые зависимости
        key_deps = [
            "fastapi",
            "uvicorn",
            "aiogram",
            "sqlalchemy",
            "redis",
            "python-jose"
        ]
        
        missing_deps = []
        for dep in key_deps:
            if dep not in requirements:
                missing_deps.append(dep)
        
        if missing_deps:
            print(f"❌ Отсутствуют зависимости: {', '.join(missing_deps)}")
            return False
        else:
            print("✅ Все ключевые зависимости присутствуют")
            return True
            
    except Exception as e:
        print(f"❌ Ошибка чтения requirements.txt: {e}")
        return False

def check_railway_config():
    """Проверяет конфигурацию Railway"""
    if not os.path.exists("railway.json"):
        print("❌ railway.json не найден")
        return False
    
    try:
        import json
        with open("railway.json", "r") as f:
            config = json.load(f)
        
        # Проверяем ключевые настройки
        checks = [
            ("build.builder", "nixpacks"),
            ("deploy.startCommand", "python start.py"),
            ("deploy.healthcheckPath", "/health"),
            ("plugins", "postgresql"),
            ("plugins", "redis")
        ]
        
        all_good = True
        for check_path, expected in checks:
            if check_path == "plugins":
                plugins = config.get("plugins", [])
                if not any(p.get("name") == expected for p in plugins):
                    print(f"❌ Плагин {expected} не настроен")
                    all_good = False
            else:
                keys = check_path.split(".")
                value = config
                for key in keys:
                    value = value.get(key)
                    if value is None:
                        break
                
                if value != expected:
                    print(f"❌ {check_path}: ожидалось '{expected}', получено '{value}'")
                    all_good = False
        
        if all_good:
            print("✅ Railway конфигурация корректна")
        
        return all_good
        
    except Exception as e:
        print(f"❌ Ошибка чтения railway.json: {e}")
        return False

def check_dockerfile():
    """Проверяет Dockerfile"""
    if not os.path.exists("Dockerfile"):
        print("❌ Dockerfile не найден")
        return False
    
    try:
        with open("Dockerfile", "r") as f:
            dockerfile = f.read()
        
        # Проверяем ключевые элементы
        checks = [
            "FROM python:",
            "WORKDIR /app",
            "COPY requirements.txt",
            "RUN pip install",
            "COPY . .",
            "EXPOSE 8080",
            "CMD [\"python\", \"start.py\"]"
        ]
        
        missing = []
        for check in checks:
            if check not in dockerfile:
                missing.append(check)
        
        if missing:
            print(f"❌ В Dockerfile отсутствуют: {', '.join(missing)}")
            return False
        else:
            print("✅ Dockerfile корректный")
            return True
            
    except Exception as e:
        print(f"❌ Ошибка чтения Dockerfile: {e}")
        return False

def check_start_script():
    """Проверяет start.py"""
    if not os.path.exists("start.py"):
        print("❌ start.py не найден")
        return False
    
    try:
        with open("start.py", "r") as f:
            start_script = f.read()
        
        # Проверяем ключевые элементы
        checks = [
            "validate_environment",
            "run_bot",
            "run_web_server",
            "asyncio.run(main())"
        ]
        
        missing = []
        for check in checks:
            if check not in start_script:
                missing.append(check)
        
        if missing:
            print(f"❌ В start.py отсутствуют: {', '.join(missing)}")
            return False
        else:
            print("✅ start.py корректный")
            return True
            
    except Exception as e:
        print(f"❌ Ошибка чтения start.py: {e}")
        return False

def main():
    """Основная функция проверки"""
    print("🚀 Railway Deployment Readiness Check")
    print("=" * 50)
    
    checks = [
        ("Файлы проекта", lambda: all([
            check_file_exists("requirements.txt", "Requirements"),
            check_file_exists("railway.json", "Railway config"),
            check_file_exists("Dockerfile", "Dockerfile"),
            check_file_exists("start.py", "Start script"),
            check_file_exists("web/main.py", "Web app"),
            check_file_exists("bot/bot.py", "Bot module"),
            check_file_exists("core/database/__init__.py", "Database module")
        ])),
        ("Requirements", check_requirements),
        ("Railway config", check_railway_config),
        ("Dockerfile", check_dockerfile),
        ("Start script", check_start_script),
        ("Импорты", check_imports)
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\n📋 Проверка: {name}")
        print("-" * 30)
        try:
            result = check_func()
            results.append(result)
        except Exception as e:
            print(f"❌ Ошибка при проверке {name}: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("📊 РЕЗУЛЬТАТЫ ПРОВЕРКИ")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print("🎉 ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ!")
        print("✅ Проект готов к деплою на Railway")
        print("\n🚀 Следующие шаги:")
        print("1. Создать проект на Railway")
        print("2. Подключить GitHub репозиторий")
        print("3. Настроить переменные окружения")
        print("4. Деплой запустится автоматически")
    else:
        print(f"❌ ПРОЙДЕНО: {passed}/{total} проверок")
        print("🔧 Исправьте ошибки перед деплоем")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
