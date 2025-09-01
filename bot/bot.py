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

# Import middlewares
from core.middleware import setup_rbac_middleware, setup_2fa_middleware

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
    
    # Setup middlewares
    setup_rbac_middleware(dp)
    setup_2fa_middleware(dp)
    
    # Add test command handler
    @dp.message(Command("start"))
    async def cmd_start(message: types.Message):
        logger.info(f"Received /start from user {message.from_user.id}")
        await message.answer("🚀 Бот запущен и работает!")
    
    # Import and include other handlers
    try:
        # Import 2FA handlers
        from core.handlers.two_factor_handlers import handlers as two_factor_handlers
        for handler in two_factor_handlers:
            dp.include_router(handler)
            
        # Import admin audit handlers
        from core.handlers.admin_audit_handlers import handlers as admin_audit_handlers
        for handler in admin_audit_handlers:
            dp.include_router(handler)
            
        # Import individual routers with error handling
        routers = []
        
        # Helper function to safely import and get router
        def get_router(module_name):
            try:
                module = __import__(f'core.handlers.{module_name}', fromlist=[module_name])
                # Skip modules that don't have routers
                if module_name == 'commands':
                    logger.info("ℹ️  Skipping commands module as it doesn't have a router")
                    return None
                    
                # Try common router attribute names
                for attr in ['router', 'message_router', 'command_router', 'main_router']:
                    if hasattr(module, attr):
                        router = getattr(module, attr)
                        logger.info(f"✅ Found router {attr} in {module_name}")
                        return router
                logger.warning(f"⚠️ No router found in {module_name}")
                return None
            except ImportError as e:
                logger.warning(f"⚠️ Failed to import {module_name}: {e}")
                return None
        
        # List of handler modules to import (without commands)
        handler_modules = [
            'basic', 'callback', 'contact', 'lang', 'main_menu_router',
            'profile', 'partner', 'activity', 'admin_cabinet', 'category_handlers'
        ]
        
        # Get all available routers
        for module_name in handler_modules:
            router = get_router(module_name)
            if router:
                routers.append(router)
        
        # Include all found routers
        for router in routers:
            try:
                if router:
                    dp.include_router(router)
                    logger.info(f"✅ Successfully included router from {router}")
            except Exception as e:
                logger.error(f"❌ Failed to include router {router}: {e}", exc_info=True)
        
        # Set up commands directly since commands.py doesn't have a router
        async def setup_commands():
            try:
                from core.handlers.commands import set_commands
                await set_commands(bot)
                logger.info("✅ Bot commands set up successfully")
                return True
            except Exception as e:
                logger.error(f"❌ Failed to set up bot commands: {e}", exc_info=True)
                return False
                
        # Run command setup in the event loop
        import asyncio
        asyncio.create_task(setup_commands())
        
        logger.info(f"✅ All routers initialized. Total routers: {len(routers)}")
        
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
