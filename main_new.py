"""
KARMABOT1 - Новый модульный entry point
ВАЖНО: Сохраняет адаптерную систему БД!
"""
import asyncio
import logging
import sys
import signal
from core.config.deployment import get_config, DeploymentMode
from core.bot.instance import get_bot, get_dispatcher, shutdown
from core.server.webhook import WebhookServer

# ВАЖНО: Импортируем адаптер БД
from core.database.db_adapter import db_v2

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

shutdown_event = asyncio.Event()

def signal_handler(signum, frame):
    logger.info(f"🛑 Signal {signum}")
    shutdown_event.set()

async def init_database():
    """
    Инициализация БД
    ВАЖНО: Используем существующий адаптер!
    """
    logger.info("🗄️ Initializing database...")
    
    # Ensure database is ready (из main_v2.py строка 403)
    from core.database.migrations import ensure_database_ready
    ensure_database_ready()
    
    if db_v2.use_postgresql:
        logger.info("✅ Using PostgreSQL (production)")
        # PostgreSQL уже инициализирован в адаптере
    else:
        logger.info("✅ Using SQLite (development)")
        # SQLite уже инициализирован в адаптере
    
    # Проверка подключения
    try:
        if db_v2.use_postgresql:
            # Простой тест PostgreSQL
            result = await db_v2.postgresql_service.fetch_one(
                "SELECT 1 as test"
            )
            logger.info(f"✅ PostgreSQL connection OK: {result}")
        else:
            # Простой тест SQLite
            result = db_v2.sqlite_service.fetch_one("SELECT 1 as test")
            logger.info(f"✅ SQLite connection OK: {result}")
    except Exception as e:
        logger.error(f"❌ Database test failed: {e}")
        raise

async def register_handlers(dp):
    """
    Регистрация handlers
    Использует централизованный registry из main_v2.py
    """
    logger.info("📝 Registering handlers...")
    
    try:
        from core.handlers.registry import register_all_handlers
        register_all_handlers(dp)
        logger.info("✅ All handlers registered successfully!")
    except Exception as e:
        logger.error(f"❌ Failed to register handlers: {e}")
        raise

async def run_webhook(bot, dp, config):
    """Webhook режим"""
    logger.info("🌐 Starting WEBHOOK mode...")
    
    server = WebhookServer(bot, dp, config)
    await server.start()
    
    logger.info("✅ Webhook running")
    await shutdown_event.wait()
    
    await server.stop()

async def run_polling(bot, dp):
    """Polling режим"""
    logger.info("🔄 Starting POLLING mode...")
    
    await bot.delete_webhook(drop_pending_updates=True)
    
    try:
        await dp.start_polling(bot)
    except asyncio.CancelledError:
        logger.info("🛑 Polling cancelled")

async def main():
    try:
        logger.info("=" * 60)
        logger.info("🚀 KARMABOT1 Starting")
        logger.info("=" * 60)
        
        # 1. Конфигурация
        config = get_config()
        
        # 2. База данных
        await init_database()
        
        # 3. Bot и Dispatcher
        bot = get_bot()
        dp = get_dispatcher()
        
        # 4. Handlers
        await register_handlers(dp)
        
        # 5. Запуск
        if config.mode == DeploymentMode.WEBHOOK:
            await run_webhook(bot, dp, config)
        else:
            await run_polling(bot, dp)
        
    except KeyboardInterrupt:
        logger.info("🛑 Interrupted")
    except Exception as e:
        logger.error(f"❌ Fatal: {e}", exc_info=True)
        sys.exit(1)
    finally:
        await shutdown()

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    asyncio.run(main())
