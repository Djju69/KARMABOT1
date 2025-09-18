#!/usr/bin/env python3
"""
Простой скрипт для push в git
"""
import subprocess
import sys
import os

def main():
    print("🚀 Выполняем git push...")
    
    try:
        # Проверяем статус
        print("📊 Проверяем статус...")
        result = subprocess.run(['git', 'status'], capture_output=True, text=True)
        print(result.stdout)
        
        # Добавляем все файлы
        print("📁 Добавляем файлы...")
        subprocess.run(['git', 'add', '.'], check=True)
        
        # Коммитим
        print("💾 Коммитим изменения...")
        commit_msg = """chore: fix legacy imports and remove outdated files

- Created modern exception module core/common/exceptions.py
- Created restaurant keyboards module core/keyboards/restaurant_keyboards.py  
- Updated all imports in handlers and services to use new modules
- Removed legacy files: core/keyboards/inline.py and core/exceptions.py
- Updated legacy_report.json to reflect completed cleanup"""
        
        subprocess.run(['git', 'commit', '-m', commit_msg], check=True)
        
        # Пушим
        print("🚀 Пушим в main...")
        subprocess.run(['git', 'push', 'origin', 'main'], check=True)
        
        print("✅ Успешно выполнено!")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка: {e}")
        return False
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)