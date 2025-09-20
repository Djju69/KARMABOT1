"""
Test script to verify bot functionality
"""
import os
import asyncio
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_bot():
    """Test bot initialization and basic functionality"""
    try:
        # Import bot module
        from bot.bot import bot, dp
        
        # Test bot info
        bot_info = await bot.get_me()
        logger.info(f"🤖 Bot Info: {bot_info}")
        
        # Test command handling
        logger.info("✅ Bot initialized successfully")
        logger.info("ℹ️  Send /start to the bot to test if it responds")
        
        # Start polling with a timeout
        logger.info("🚀 Starting bot polling (press Ctrl+C to stop)...")
        await dp.start_polling(bot, skip_updates=True)
        
    except Exception as e:
        logger.error(f"❌ Bot test failed: {e}", exc_info=True)
        raise
    finally:
        await (await bot.get_session()).close()

if __name__ == "__main__":
    # Ensure we have the required environment variables
    if not os.getenv("BOT_TOKEN"):
        logger.error("❌ BOT_TOKEN environment variable is not set")
        exit(1)
        
    logger.info("🔍 Starting bot test...")
    asyncio.run(test_bot())
