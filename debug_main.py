#!/usr/bin/env python3
"""
KARMABOT1 - Debug version for Railway troubleshooting
Minimal version with detailed logging for diagnostics
"""
import os
import sys
import asyncio
import logging
from pathlib import Path

# Setup logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def check_environment():
    """Check all required environment variables"""
    logger.info("=== ENVIRONMENT CHECK ===")
    
    required_vars = ['BOT_TOKEN', 'ADMIN_ID']
    optional_vars = ['DATABASE_URL', 'ENVIRONMENT', 'LOG_LEVEL']
    
    missing_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            if var == 'BOT_TOKEN':
                logger.info(f"{var}: {value[:10]}...{value[-4:]}")  # Mask token
            else:
                logger.info(f"{var}: {value}")
        else:
            logger.error(f"MISSING: {var}")
            missing_vars.append(var)
    
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            logger.info(f"{var}: {value}")
        else:
            logger.warning(f"NOT SET: {var}")
    
    if missing_vars:
        logger.error(f"Missing required variables: {missing_vars}")
        return False
    
    return True

def check_imports():
    """Check if all required modules can be imported"""
    logger.info("=== IMPORT CHECK ===")
    
    try:
        import aiogram
        logger.info(f"aiogram: {aiogram.__version__}")
    except ImportError as e:
        logger.error(f"Failed to import aiogram: {e}")
        return False
    
    try:
        from environs import Env
        logger.info("environs: OK")
    except ImportError as e:
        logger.error(f"Failed to import environs: {e}")
        return False
    
    try:
        import asyncpg
        logger.info("asyncpg: OK (PostgreSQL support)")
    except ImportError as e:
        logger.warning(f"asyncpg not available: {e}")
    
    try:
        import aiosqlite
        logger.info("aiosqlite: OK (SQLite fallback)")
    except ImportError as e:
        logger.warning(f"aiosqlite not available: {e}")
    
    return True

def check_settings():
    """Check settings loading"""
    logger.info("=== SETTINGS CHECK ===")
    
    try:
        from core.settings import settings
        logger.info("Settings loaded successfully")
        logger.info(f"Database URL: {settings.database.url}")
        logger.info(f"Environment: {settings.environment}")
        logger.info(f"Admin ID: {settings.bots.admin_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to load settings: {e}")
        return False

async def test_bot_connection():
    """Test bot token and connection"""
    logger.info("=== BOT CONNECTION TEST ===")
    
    try:
        from aiogram import Bot
        from core.settings import settings
        
        bot = Bot(token=settings.bots.bot_token)
        me = await bot.get_me()
        logger.info(f"Bot connected: @{me.username} ({me.first_name})")
        await bot.session.close()
        return True
    except Exception as e:
        logger.error(f"Bot connection failed: {e}")
        return False

async def test_database():
    """Test database connection"""
    logger.info("=== DATABASE TEST ===")
    
    try:
        from core.settings import settings
        db_url = settings.database.url
        
        if db_url.startswith('postgresql'):
            import asyncpg
            # Extract connection info from URL
            conn = await asyncpg.connect(db_url)
            result = await conn.fetchval('SELECT version()')
            logger.info(f"PostgreSQL connected: {result[:50]}...")
            await conn.close()
        else:
            import aiosqlite
            async with aiosqlite.connect(db_url.replace('sqlite:///', '')) as conn:
                cursor = await conn.execute('SELECT sqlite_version()')
                result = await cursor.fetchone()
                logger.info(f"SQLite connected: {result[0]}")
        
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False

async def main():
    """Main diagnostic function"""
    logger.info("🔍 KARMABOT1 - Railway Diagnostic")
    logger.info("=" * 50)
    
    # Check environment
    if not check_environment():
        logger.error("❌ Environment check failed")
        return False
    
    # Check imports
    if not check_imports():
        logger.error("❌ Import check failed")
        return False
    
    # Check settings
    if not check_settings():
        logger.error("❌ Settings check failed")
        return False
    
    # Test bot connection
    if not await test_bot_connection():
        logger.error("❌ Bot connection failed")
        return False
    
    # Test database
    if not await test_database():
        logger.error("❌ Database connection failed")
        return False
    
    logger.info("✅ All checks passed!")
    logger.info("🚀 Starting minimal bot...")
    
    # Start minimal bot
    try:
        from aiogram import Bot, Dispatcher
        from aiogram.filters import CommandStart
        from aiogram.types import Message
        from core.settings import settings
        
        bot = Bot(token=settings.bots.bot_token)
        dp = Dispatcher()
        
        @dp.message(CommandStart())
        async def start_handler(message: Message):
            await message.answer(
                f"🤖 KARMABOT1 v2.0 работает!\n"
                f"Админ: {settings.bots.admin_id}\n"
                f"База: {settings.database.url[:30]}...\n"
                f"Окружение: {settings.environment}"
            )
            logger.info(f"Start command from user {message.from_user.id}")
        
        logger.info("Reset webhook (drop pending updates) and start polling...")
        # Ensure no webhook is set when starting long polling to avoid conflicts
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"Bot startup failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
