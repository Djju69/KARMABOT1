#!/usr/bin/env python3
"""
KARMABOT1 - Railway Deployment Script
Автоматический деплой на Railway.app
"""

import os
import sys
import subprocess
import json

def check_railway_cli():
    """Проверить установлен ли Railway CLI"""
    try:
        result = subprocess.run(['railway', '--version'], 
                              capture_output=True, text=True, check=True)
        print(f"Railway CLI установлен: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Railway CLI не установлен")
        return False

def install_railway_cli():
    """Установить Railway CLI через PowerShell"""
    print("Устанавливаем Railway CLI...")
    
    # Команда для установки Railway CLI на Windows
    install_cmd = [
        'powershell', '-Command',
        'iwr "https://railway.app/install.ps1" -useb | iex'
    ]
    
    try:
        subprocess.run(install_cmd, check=True)
        print("Railway CLI установлен успешно")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Ошибка установки Railway CLI: {e}")
        return False

def railway_login():
    """Войти в Railway аккаунт"""
    print("Вход в Railway аккаунт...")
    try:
        subprocess.run(['railway', 'login'], check=True)
        print("Успешный вход в Railway")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Ошибка входа в Railway: {e}")
        return False

def create_railway_project():
    """Создать новый Railway проект"""
    print("Создаем Railway проект...")
    try:
        # Связать с существующим GitHub репозиторием
        subprocess.run(['railway', 'link'], check=True)
        print("Проект создан и связан с GitHub")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Ошибка создания проекта: {e}")
        return False

def add_postgresql():
    """Добавить PostgreSQL базу данных"""
    print("Добавляем PostgreSQL...")
    try:
        subprocess.run(['railway', 'add', 'postgresql'], check=True)
        print("PostgreSQL добавлен")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Ошибка добавления PostgreSQL: {e}")
        return False

def set_environment_variables():
    """Установить переменные окружения"""
    print("Устанавливаем переменные окружения...")
    
    variables = {
        'BOT_TOKEN': '7619342315:AAFU8c7uNN6KClV0MSGDKnWWAWw2X5ho-Fg',
        'ADMIN_ID': '6391215556',
        'FERNET_KEY_HEX': '729191104e4400c325e25b204175bd896297e2bc83520c968a9c105aaad9f9cc',
        'LOG_LEVEL': 'INFO',
        'ENVIRONMENT': 'production',
        'RAILWAY_ENVIRONMENT': 'production',
        'FEATURE_PARTNER_FSM': 'false',
        'FEATURE_MODERATION': 'false',
        'FEATURE_NEW_MENU': 'false',
        'FEATURE_QR_WEBAPP': 'false',
        'FEATURE_LISTEN_NOTIFY': 'false'
    }
    
    try:
        for key, value in variables.items():
            cmd = ['railway', 'variables', 'set', f'{key}={value}']
            subprocess.run(cmd, check=True)
            print(f"  {key} установлен")
        
        print("Все переменные установлены")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Ошибка установки переменных: {e}")
        return False

def deploy():
    """Запустить деплой"""
    print("Запускаем деплой...")
    try:
        subprocess.run(['railway', 'up'], check=True)
        print("Деплой запущен успешно")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Ошибка деплоя: {e}")
        return False

def main():
    """Основная функция деплоя"""
    print("KARMABOT1 - Автоматический деплой на Railway")
    print("=" * 50)
    
    # Проверить Railway CLI
    if not check_railway_cli():
        print("\nУстанавливаем Railway CLI...")
        if not install_railway_cli():
            print("\nНе удалось установить Railway CLI")
            print("Установите вручную: https://docs.railway.app/develop/cli")
            return False
    
    # Войти в аккаунт
    if not railway_login():
        return False
    
    # Создать проект
    if not create_railway_project():
        return False
    
    # Добавить PostgreSQL
    if not add_postgresql():
        return False
    
    # Установить переменные
    if not set_environment_variables():
        return False
    
    # Деплой
    if not deploy():
        return False
    
    print("\nKARMABOT1 успешно развернут на Railway!")
    print("Проверьте логи: railway logs")
    print("Откройте проект: railway open")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
