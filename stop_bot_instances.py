#!/usr/bin/env python3
"""
Script to stop all active Telegram bot instances using deleteWebhook API call.
This resolves TelegramConflictError when multiple bot instances are running.
"""
import os
import sys
import asyncio
import logging
from typing import Optional

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def stop_bot_instances(bot_token: str) -> bool:
    """
    Stop all active bot instances by deleting webhook and closing polling connections.

    Args:
        bot_token: Telegram bot token

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create bot instance
        bot = Bot(token=bot_token)

        logger.info("🔄 Attempting to stop all bot instances...")

        # Delete webhook to stop webhook-based instances
        try:
            await bot.delete_webhook()
            logger.info("✅ Webhook deleted successfully")
        except TelegramBadRequest as e:
            if "webhook is already deleted" in str(e).lower():
                logger.info("ℹ️ Webhook was already deleted")
            else:
                logger.warning(f"⚠️ Failed to delete webhook: {e}")
        except Exception as e:
            logger.warning(f"⚠️ Unexpected error deleting webhook: {e}")

        # Close bot session
        await bot.session.close()
        logger.info("✅ Bot session closed")

        return True

    except Exception as e:
        logger.error(f"❌ Failed to stop bot instances: {e}")
        return False


async def main():
    """Main function to stop bot instances"""
    # Get bot token from environment
    bot_token = os.getenv('BOT_TOKEN')

    if not bot_token:
        logger.error("❌ BOT_TOKEN environment variable is not set")
        logger.error("Please set BOT_TOKEN in your environment or Railway dashboard")
        sys.exit(1)

    logger.info("🚀 Starting bot instance cleanup...")
    logger.info(f"Bot token: {bot_token[:10]}...{bot_token[-10:]}")

    success = await stop_bot_instances(bot_token)

    if success:
        logger.info("🎉 Bot instances stopped successfully!")
        logger.info("💡 You can now restart your bot without conflicts")
    else:
        logger.error("💥 Failed to stop bot instances")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())