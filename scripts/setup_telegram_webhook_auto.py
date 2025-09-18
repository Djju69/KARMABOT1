#!/usr/bin/env python3
"""
Автоматическая настройка вебхука для Telegram бота.
"""
import os
import sys
import json
import logging
import requests
from pathlib import Path

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Проверка переменных окружения
def check_env_vars():
    """Проверяет наличие необходимых переменных окружения."""
    required_vars = [
        'TELEGRAM_BOT_TOKEN',
        'RAILWAY_STATIC_URL',
        'TELEGRAM_WEBHOOK_SECRET'
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Отсутствуют обязательные переменные окружения: {', '.join(missing_vars)}")
        logger.info("\nПожалуйста, установите следующие переменные окружения в настройках Railway:")
        logger.info("- TELEGRAM_BOT_TOKEN: Токен вашего бота от @BotFather")
        logger.info("- RAILWAY_STATIC_URL: URL вашего приложения на Railway")
        logger.info("- TELEGRAM_WEBHOOK_SECRET: Секретный ключ для верификации вебхука")
        return False
    
    return True

def setup_webhook():
    """Настраивает вебхук для Telegram бота."""
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    webhook_url = f"{os.getenv('RAILWAY_STATIC_URL')}/webhooks/telegram"
    secret_token = os.getenv('TELEGRAM_WEBHOOK_SECRET')
    
    logger.info(f"Настройка вебхука для бота...")
    logger.info(f"Webhook URL: {webhook_url}")
    
    url = f"https://api.telegram.org/bot{bot_token}/setWebhook"
    
    try:
        response = requests.post(
            url,
            data={
                'url': webhook_url,
                'secret_token': secret_token
            },
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                logger.info("✅ Вебхук успешно настроен!")
                logger.info(f"Статус: {result.get('description')}")
                return True
            else:
                logger.error(f"❌ Ошибка при настройке вебхука: {result.get('description')}")
        else:
            logger.error(f"❌ Ошибка HTTP {response.status_code}: {response.text}")
    
    except Exception as e:
        logger.error(f"❌ Ошибка при настройке вебхука: {str(e)}")
    
    return False

def check_webhook():
    """Проверяет текущие настройки вебхука."""
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    url = f"https://api.telegram.org/bot{bot_token}/getWebhookInfo"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                webhook_info = result.get('result', {})
                logger.info("\nТекущие настройки вебхука:")
                logger.info(f"URL: {webhook_info.get('url')}")
                logger.info(f"Имеет пользовательский сертификат: {webhook_info.get('has_custom_certificate')}")
                logger.info(f"Ожидающие обновления: {webhook_info.get('pending_update_count')}")
                logger.info(f"Дата последней ошибки: {webhook_info.get('last_error_date')}")
                logger.info(f"Последнее сообщение об ошибке: {webhook_info.get('last_error_message')}")
                return True
    except Exception as e:
        logger.error(f"❌ Ошибка при проверке вебхука: {str(e)}")
    
    return False

if __name__ == "__main__":
    if not check_env_vars():
        sys.exit(1)
    
    if setup_webhook():
        check_webhook()
    else:
        sys.exit(1)
