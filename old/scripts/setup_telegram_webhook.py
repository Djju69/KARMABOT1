#!/usr/bin/env python3
"""
Script to set up Telegram webhook.

This script configures the Telegram bot webhook URL and verifies the setup.
"""
import asyncio
import logging
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from core import settings
from core.telegram_service import TelegramService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def setup_webhook():
    """Set up the Telegram webhook with the configured URL."""
    if not settings.telegram.is_configured:
        logger.error("Telegram bot is not properly configured. Check TELEGRAM_BOT_TOKEN and TELEGRAM_BOT_USERNAME.")
        return False
    
    if not settings.telegram.webhook_url:
        logger.error("Webhook URL is not configured. Set TELEGRAM_WEBHOOK_URL environment variable.")
        return False
    
    telegram_service = TelegramService()
    
    try:
        # Set webhook
        logger.info(f"Setting up webhook URL: {settings.telegram.webhook_url}")
        result = await telegram_service.set_webhook(
            url=settings.telegram.webhook_url,
            secret_token=settings.telegram.webhook_secret,
            max_connections=settings.telegram.max_connections,
            allowed_updates=settings.telegram.allowed_updates
        )
        
        if result:
            logger.info("✅ Webhook set up successfully!")
            
            # Verify webhook info
            webhook_info = await telegram_service.get_webhook_info()
            logger.info(f"Webhook info: {webhook_info}")
            
            if webhook_info.get('url') != settings.telegram.webhook_url:
                logger.warning("⚠️ Webhook URL doesn't match the configured URL!")
                return False
                
            return True
        else:
            logger.error("❌ Failed to set webhook")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error setting up webhook: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    # Check if webhook URL is set
    if not settings.telegram.webhook_url:
        logger.error("Error: TELEGRAM_WEBHOOK_URL environment variable is not set")
        print("\nPlease set the following environment variables:")
        print(f"- TELEGRAM_BOT_TOKEN=your_bot_token")
        print(f"- TELEGRAM_BOT_USERNAME=your_bot_username")
        print(f"- TELEGRAM_WEBHOOK_URL=https://your-domain.com/webhooks/telegram")
        print("\nOptional:")
        print(f"- TELEGRAM_WEBHOOK_SECRET={settings.telegram.webhook_secret}  # Auto-generated if not set")
        print(f"- TELEGRAM_MAX_CONNECTIONS={settings.telegram.max_connections}")
        sys.exit(1)
    
    # Run the async function
    success = asyncio.run(setup_webhook())
    sys.exit(0 if success else 1)
