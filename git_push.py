#!/usr/bin/env python3
"""
Скрипт для выполнения git push в локальную папку
"""

import subprocess
import sys
import os

def run_git_command(command):
    """Выполнить git команду"""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            cwd=os.getcwd()
        )
        print(f"Команда: {command}")
        print(f"Код выхода: {result.returncode}")
        if result.stdout:
            print(f"Вывод: {result.stdout}")
        if result.stderr:
            print(f"Ошибки: {result.stderr}")
        return result.returncode == 0
    except Exception as e:
        print(f"Ошибка выполнения команды: {e}")
        return False

def main():
    print("=== Git Push в локальную папку ===")
    
    # Проверяем текущий статус
    print("\n1. Проверяем статус git...")
    if not run_git_command("git status"):
        print("Ошибка при проверке статуса")
        return
    
    # Проверяем текущую ветку
    print("\n2. Проверяем текущую ветку...")
    if not run_git_command("git branch --show-current"):
        print("Ошибка при проверке ветки")
        return
    
    # Показываем удаленные репозитории
    print("\n3. Проверяем удаленные репозитории...")
    if not run_git_command("git remote -v"):
        print("Ошибка при проверке удаленных репозиториев")
        return
    
    # Выполняем push
    print("\n4. Выполняем push...")
    if run_git_command("git push origin main"):
        print("✅ Push выполнен успешно!")
    else:
        print("❌ Ошибка при выполнении push")
        
        # Попробуем push с force, если нужно
        print("\n5. Пробуем push с --force...")
        if run_git_command("git push origin main --force"):
            print("✅ Force push выполнен успешно!")
        else:
            print("❌ Ошибка при выполнении force push")

if __name__ == "__main__":
    main()
