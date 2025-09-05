#!/usr/bin/env python3
"""
Скрипт для остановки всех экземпляров бота
"""
import os
import sys
import asyncio
import logging
from pathlib import Path

# Add project root to path
project_root = str(Path(__file__).parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def stop_bot():
    """Остановка бота через webhook"""
    try:
        import aiohttp
        from core.settings import settings
        
        bot_token = settings.BOT_TOKEN
        if not bot_token:
            logger.error("BOT_TOKEN не найден")
            return
            
        # Удаляем webhook
        webhook_url = f"https://api.telegram.org/bot{bot_token}/deleteWebhook"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url) as response:
                if response.status == 200:
                    logger.info("✅ Webhook удален успешно")
                else:
                    logger.error(f"❌ Ошибка удаления webhook: {response.status}")
                    
    except Exception as e:
        logger.error(f"❌ Ошибка остановки бота: {e}")

if __name__ == "__main__":
    logger.info("🛑 Останавливаем все экземпляры бота...")
    asyncio.run(stop_bot())
