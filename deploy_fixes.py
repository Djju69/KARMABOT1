#!/usr/bin/env python3
"""
Скрипт для деплоя исправлений бота
"""
import subprocess
import sys
import os

def run_command(cmd):
    """Выполнить команду и показать результат"""
    print(f"🔄 Выполняем: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Успешно: {cmd}")
            if result.stdout:
                print(result.stdout)
        else:
            print(f"❌ Ошибка: {cmd}")
            print(result.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Исключение: {e}")
        return False

def main():
    print("🚀 Начинаем деплой исправлений бота...")
    
    # Проверяем что мы в правильной директории
    if not os.path.exists("main_v2.py"):
        print("❌ Не найден main_v2.py. Убедитесь что вы в корне проекта.")
        return
    
    # Добавляем все изменения
    if not run_command("git add ."):
        print("❌ Ошибка при добавлении файлов в git")
        return
    
    # Коммитим изменения
    commit_msg = "🔧 Исправления критических ошибок: AsyncConnectionWrapper, start_monitoring, Settings.database, баллы лояльности"
    if not run_command(f'git commit -m "{commit_msg}"'):
        print("❌ Ошибка при коммите")
        return
    
    # Пушим изменения
    if not run_command("git push"):
        print("❌ Ошибка при push")
        return
    
    print("🎉 Деплой завершен успешно!")
    print("📊 Исправления:")
    print("  ✅ AsyncConnectionWrapper context manager")
    print("  ✅ start_monitoring await")
    print("  ✅ Settings.database атрибут")
    print("  ✅ Баллы лояльности согласно документации:")
    print("    - Ежедневный вход: 5 баллов (было 10)")
    print("    - Привязка карты: 25 баллов (было 100)")
    print("    - За приглашение: 50 баллов (было 100)")

if __name__ == "__main__":
    main()
