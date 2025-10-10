"""
KARMABOT1 - Railway Production Entry Point
Использует модульную структуру с webhook режимом
"""
import os
import asyncio
import logging
import sys
import signal
from core.config.deployment import get_config, DeploymentMode
from core.bot.instance import get_bot, get_dispatcher, shutdown
from core.server.webhook import WebhookServer

# ВАЖНО: Импортируем адаптер БД
from core.database.db_adapter import db_v2

# Настройка логирования для Railway
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

shutdown_event = asyncio.Event()

def signal_handler(signum, frame):
    logger.info(f"🛑 Signal {signum}")
    shutdown_event.set()

async def init_database():
    """
    Инициализация БД для Railway
    """
    logger.info("🗄️ Initializing database for Railway...")
    
    # Ensure database is ready
    from core.database.migrations import ensure_database_ready
    ensure_database_ready()
    
    if db_v2.use_postgresql:
        logger.info("✅ Using PostgreSQL (Railway production)")
        # Инициализируем PostgreSQL pool
        await db_v2.init_postgresql()
    else:
        logger.info("✅ Using SQLite (fallback)")
    
    # Проверка подключения
    try:
        if db_v2.use_postgresql:
            result = await db_v2.postgresql_service.fetch_one("SELECT 1 as test")
            logger.info(f"✅ PostgreSQL connection OK: {result}")
        else:
            result = db_v2.sqlite_service.fetch_one("SELECT 1 as test")
            logger.info(f"✅ SQLite connection OK: {result}")
    except Exception as e:
        logger.error(f"❌ Database test failed: {e}")
        raise

async def register_handlers(dp):
    """
    Регистрация handlers для Railway
    """
    logger.info("📝 Registering handlers for Railway...")
    
    try:
        from core.handlers.registry import register_all_handlers
        register_all_handlers(dp)
        logger.info("✅ All handlers registered successfully!")
    except Exception as e:
        logger.error(f"❌ Failed to register handlers: {e}")
        raise

async def run_webhook(bot, dp, config):
    """Webhook режим для Railway"""
    logger.info("🌐 Starting WEBHOOK mode for Railway...")
    
    server = WebhookServer(bot, dp, config)
    await server.start()
    
    logger.info("✅ Webhook running on Railway")
    await shutdown_event.wait()
    
    await server.stop()

async def main():
    try:
        logger.info("=" * 60)
        logger.info("🚀 KARMABOT1 Starting on Railway")
        logger.info("=" * 60)
        
        # Логируем переменные окружения
        logger.info(f"RAILWAY_ENVIRONMENT: {os.getenv('RAILWAY_ENVIRONMENT', 'NOT SET')}")
        logger.info(f"RAILWAY_STATIC_URL: {os.getenv('RAILWAY_STATIC_URL', 'NOT SET')}")
        logger.info(f"DATABASE_URL: {'SET' if os.getenv('DATABASE_URL') else 'NOT SET'}")
        logger.info(f"BOT_TOKEN: {'SET' if os.getenv('BOT_TOKEN') else 'NOT SET'}")
        
        # 1. Конфигурация
        config = get_config()
        logger.info(f"📋 Deployment config: {config}")
        
        # 2. База данных
        await init_database()
        
        # 3. Bot и Dispatcher
        bot = get_bot()
        dp = get_dispatcher()
        
        # 4. Handlers
        await register_handlers(dp)
        
        # 5. Запуск (Railway всегда webhook)
        if config.mode == DeploymentMode.WEBHOOK:
            await run_webhook(bot, dp, config)
        else:
            logger.warning("⚠️ Polling mode detected on Railway - switching to webhook")
            config.mode = DeploymentMode.WEBHOOK
            await run_webhook(bot, dp, config)
        
    except KeyboardInterrupt:
        logger.info("🛑 Interrupted")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        await shutdown()

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    asyncio.run(main())
