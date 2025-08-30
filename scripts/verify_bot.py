"""Script to verify bot functionality and environment."""
import os
import sys
import logging
import asyncio

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aiogram import Bot, Dispatcher, Router
from aiogram.filters import CommandStart
from aiogram.types import Message

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create a test router
test_router = Router(name="test_router")

@test_router.message(CommandStart())
async def cmd_start(message: Message):
    """Handle /start command for testing."""
    await message.answer("✅ Test bot is working!")

@test_router.message()
async def echo(message: Message):
    """Echo back the received message."""
    await message.answer(f"Echo: {message.text}")

async def run_test():
    """Run the test bot."""
    from core.config import BOT_TOKEN
    
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN is not configured")
        return 1
        
    print(f"🚀 Starting test bot with token: {BOT_TOKEN[:8]}...")
    
    # Initialize bot and dispatcher
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(test_router)
    
    try:
        # Get bot info
        me = await bot.get_me()
        print(f"\n🤖 Bot Info:")
        print(f"Username: @{me.username}")
        print(f"ID: {me.id}")
        print(f"Name: {me.full_name}")
        
        # Check webhook
        print("\n🌐 Webhook Info:")
        webhook_info = await bot.get_webhook_info()
        print(f"URL: {webhook_info.url or 'Not set'}")
        print(f"Pending updates: {webhook_info.pending_update_count}")
        
        if webhook_info.url:
            print("\n⚠️  Webhook is set! Deleting it for polling mode...")
            await bot.delete_webhook(drop_pending_updates=True)
            print("✅ Webhook deleted")
        
        # Start polling
        print("\n🔄 Starting polling... (Press Ctrl+C to stop)")
        print("  - Try sending /start to your bot")
        print("  - Or send any message to test echo")
        
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types(),
            drop_pending_updates=True
        )
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1
    finally:
        await bot.session.close()
    
    return 0

if __name__ == "__main__":
    sys.exit(asyncio.run(run_test()))
