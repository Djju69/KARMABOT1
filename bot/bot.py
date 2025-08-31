"""
Main bot module for KarmaBot.
This module initializes the bot instance and sets up the dispatcher.
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = str(Path(__file__).parent.parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.handlers.RotatingFileHandler(
            'bot.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
    ]
)
logger = logging.getLogger(__name__)

# Log Python and path info
logger.info(f"Python: {sys.version}")
logger.info(f"Current directory: {os.getcwd()}")
logger.info(f"Files in directory: {os.listdir('.')}")

# Import aiogram after path setup
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

# Initialize bot with default properties
try:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN environment variable is not set")
        
    logger.info(f"Initializing bot with token: {BOT_TOKEN[:10]}...{BOT_TOKEN[-5:] if BOT_TOKEN else 'MISSING'}")
    
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    dp = Dispatcher()
    
    # Add test command handler
    @dp.message(Command("start"))
    async def cmd_start(message: types.Message):
        logger.info(f"Received /start from user {message.from_user.id}")
        await message.answer("🚀 Бот запущен и работает!")
    
    # Import and include other handlers
    try:
        from core.handlers import (
            basic, commands, callback, contact, lang, main_menu_router,
            profile, partner, activity, admin_cabinet, category_handlers
        )
        
        # Setup routers
        routers = [
            basic.router,
            commands.router,
            callback.router,
            contact.router,
            lang.router,
            main_menu_router.router,
            profile.router,
            partner.router,
            activity.router,
            admin_cabinet.router,
            category_handlers.router
        ]
        
        for router in routers:
            if router:
                dp.include_router(router)
        
        logger.info("All routers initialized successfully")
        
    except ImportError as e:
        logger.error(f"Failed to import handlers: {e}", exc_info=True)
        logger.warning("Running in limited mode with only basic commands")
    
    # This will be called from start.py
    async def start():
        """Start the bot"""
        logger.info("🚀 Starting bot with polling...")
        try:
            await dp.start_polling(bot, skip_updates=True)
        except Exception as e:
            logger.critical(f"Bot polling failed: {e}", exc_info=True)
            raise
    
    # For direct execution
    if __name__ == "__main__":
        logger.info("Starting bot in direct execution mode")
        import asyncio
        asyncio.run(start())
        
except Exception as e:
    logger.critical(f"Failed to initialize bot: {e}", exc_info=True)
    raise
