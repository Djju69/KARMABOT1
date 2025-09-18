#!/usr/bin/env python3
"""
Скрипт для настройки вебхука Telegram бота на Railway.
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

class TelegramBotSetup:
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.webhook_secret = os.getenv('TELEGRAM_WEBHOOK_SECRET')
        self.railway_url = os.getenv('RAILWAY_STATIC_URL')
        
        if not all([self.bot_token, self.railway_url]):
            logger.error("Необходимо установить переменные окружения TELEGRAM_BOT_TOKEN и RAILWAY_STATIC_URL")
            sys.exit(1)
            
        if not self.webhook_secret:
            self.webhook_secret = os.urandom(16).hex()
            logger.warning(f"Сгенерирован новый секретный ключ: {self.webhook_secret}")
    
    def setup_webhook(self):
        """Настраивает вебхук для Telegram бота."""
        webhook_url = f"{self.railway_url.rstrip('/')}/webhooks/telegram"
        
        logger.info(f"Настройка вебхука для бота...")
        logger.info(f"Webhook URL: {webhook_url}")
        
        url = f"https://api.telegram.org/bot{self.bot_token}/setWebhook"
        
        try:
            response = requests.post(
                url,
                data={
                    'url': webhook_url,
                    'secret_token': self.webhook_secret,
                    'drop_pending_updates': 'true',
                    'allowed_updates': json.dumps(["message", "callback_query", "inline_query"])
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    logger.info("✅ Вебхук успешно настроен!")
                    logger.info(f"Описание: {result.get('description')}")
                    return True
                else:
                    logger.error(f"❌ Ошибка при настройке вебхука: {result.get('description')}")
            else:
                logger.error(f"❌ Ошибка HTTP {response.status_code}: {response.text}")
        
        except Exception as e:
            logger.error(f"❌ Ошибка при настройке вебхука: {str(e)}")
        
        return False
    
    def check_webhook(self):
        """Проверяет текущие настройки вебхука."""
        url = f"https://api.telegram.org/bot{self.bot_token}/getWebhookInfo"
        
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    webhook_info = result.get('result', {})
                    logger.info("\nТекущие настройки вебхука:")
                    logger.info(f"URL: {webhook_info.get('url')}")
                    logger.info(f"Ожидающие обновления: {webhook_info.get('pending_update_count')}")
                    
                    if webhook_info.get('last_error_date'):
                        logger.warning(f"Дата последней ошибки: {webhook_info.get('last_error_date')}")
                        logger.warning(f"Последнее сообщение об ошибке: {webhook_info.get('last_error_message')}")
                    
                    return True
        except Exception as e:
            logger.error(f"❌ Ошибка при проверке вебхука: {str(e)}")
        
        return False
    
    def run(self):
        """Запускает процесс настройки."""
        logger.info("🚀 Начало настройки Telegram бота")
        logger.info(f"Используется URL приложения: {self.railway_url}")
        
        if self.setup_webhook():
            self.check_webhook()
            
            logger.info("\n✅ Настройка завершена!")
            logger.info("Проверьте работу бота, отправив ему команду /start")
        else:
            logger.error("\n❌ Не удалось настроить вебхук. Пожалуйста, проверьте логи и настройки.")
            sys.exit(1)

if __name__ == "__main__":
    try:
        setup = TelegramBotSetup()
        setup.run()
    except KeyboardInterrupt:
        logger.info("\nСкрипт остановлен пользователем")
        sys.exit(0)
