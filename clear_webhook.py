#!/usr/bin/env python3
"""
Script to clear Telegram webhook and stop bot instances
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def clear_webhook():
    """Clear Telegram webhook"""
    try:
        from aiogram import Bot

        # Get bot token from environment
        bot_token = os.getenv('BOT_TOKEN')
        if not bot_token:
            logger.error("❌ BOT_TOKEN not found in environment")
            return False

        logger.info("🔄 Clearing webhook...")

        # Create bot instance
        bot = Bot(token=bot_token)

        # Delete webhook
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("✅ Webhook cleared successfully")

        # Close session
        await bot.session.close()

        return True

    except Exception as e:
        logger.error(f"❌ Failed to clear webhook: {e}")
        return False

async def main():
    """Main function"""
    logger.info("🚀 Starting webhook cleanup...")

    success = await clear_webhook()

    if success:
        logger.info("🎉 Webhook cleared successfully!")
        logger.info("💡 Bot can now be restarted without conflicts")
    else:
        logger.error("💥 Failed to clear webhook")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
