#!/usr/bin/env python3
"""
Проверка и настройка переменных окружения для Telegram бота.
"""
import os
import sys
import secrets
import logging
from pathlib import Path

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_railway_environment():
    """Проверяет, запущен ли скрипт в среде Railway."""
    return 'RAILWAY_ENVIRONMENT' in os.environ

def generate_webhook_secret():
    """Генерирует безопасный секретный ключ для вебхука."""
    return secrets.token_urlsafe(32)

def check_required_vars():
    """Проверяет наличие обязательных переменных окружения."""
    required_vars = {
        'TELEGRAM_BOT_TOKEN': 'Токен вашего бота от @BotFather',
        'RAILWAY_STATIC_URL': 'URL вашего приложения на Railway',
        'TELEGRAM_WEBHOOK_SECRET': 'Секретный ключ для верификации вебхука (сгенерирован автоматически)'
    }
    
    missing_vars = []
    config = {}
    
    for var, description in required_vars.items():
        value = os.getenv(var)
        if not value:
            missing_vars.append((var, description))
        config[var] = value
    
    # Генерация секретного ключа, если он отсутствует
    if not config['TELEGRAM_WEBHOOK_SECRET']:
        config['TELEGRAM_WEBHOOK_SECRET'] = generate_webhook_secret()
    
    return config, missing_vars

def generate_railway_toml(config):
    """Генерирует конфигурационный файл для Railway."""
    toml_content = f"""[deploy]
  autoRollback = true

[build]
  builder = "nixpacks"
  buildCommand = "pip install -r requirements.txt"
  startCommand = "uvicorn main:app --host 0.0.0.0 --port $PORT"

[build.environment]
  PYTHON_VERSION = "3.10"
  PORT = "8000"

[build.variables]
  TELEGRAM_BOT_TOKEN = "{config['TELEGRAM_BOT_TOKEN']}"
  TELEGRAM_WEBHOOK_SECRET = "{config['TELEGRAM_WEBHOOK_SECRET']}"
  ENVIRONMENT = "production"
  DEBUG = "false"
"""
    return toml_content

def main():
    """Основная функция."""
    is_railway = check_railway_environment()
    
    if is_railway:
        logger.info("Обнаружена среда Railway")
    else:
        logger.warning("Скрипт запущен не в среде Railway")
    
    config, missing_vars = check_required_vars()
    
    if missing_vars:
        logger.warning("\n⚠️ Обнаружены отсутствующие переменные окружения:")
        for var, description in missing_vars:
            logger.warning(f"- {var}: {description}")
        
        if is_railway:
            logger.info("\nПожалуйста, установите эти переменные в настройках вашего проекта Railway:")
            logger.info("1. Перейдите в настройки проекта")
            logger.info("2. Выберите вкладку 'Variables'")
            logger.info("3. Добавьте недостающие переменные")
        else:
            logger.info("\nРекомендуемый способ настройки - через Railway.toml:")
            toml_content = generate_railway_toml(config)
            logger.info("\nДобавьте в файл railway.toml:")
            print("\n" + "="*80)
            print(toml_content)
            print("="*80 + "\n")
    else:
        logger.info("✅ Все необходимые переменные окружения настроены")
    
    # Вывод текущей конфигурации
    logger.info("\nТекущая конфигурация:")
    for var, value in config.items():
        if var == 'TELEGRAM_BOT_TOKEN' and value:
            logger.info(f"{var}: {'*' * 10 + value[-4:] if value else 'Не установлен'}")
        elif var == 'TELEGRAM_WEBHOOK_SECRET' and value:
            logger.info(f"{var}: {'*' * 10 + value[-4:] if value else 'Не установлен'}")
        else:
            logger.info(f"{var}: {value if value else 'Не установлен'}")
    
    if not missing_vars:
        logger.info("\n✅ Готово! Вы можете настроить вебхук с помощью скрипта setup_telegram_webhook_auto.py")
        return True
    
    return False

if __name__ == "__main__":
    if not main():
        sys.exit(1)
