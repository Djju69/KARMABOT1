"""
KARMABOT1 - Enhanced main entry point with backward compatibility
Integrates all new components while preserving existing functionality
"""
import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.client.bot import DefaultBotProperties

# Core imports
from core.settings import settings
from core.utils.commands import set_commands
from core.utils.logging_setup import setup_logging
from core.middlewares.locale import LocaleMiddleware
from core.database.migrations import ensure_database_ready

# Routers
from core.handlers.main_menu_router import main_menu_router
from core.handlers.basic import router as basic_router
from core.handlers.callback import router as callback_router
from core.handlers.category_handlers_v2 import get_category_router
from core.handlers.partner import get_partner_router
from core.handlers.moderation import get_moderation_router

# Services
from core.services.profile import profile_service
from core.services.cache import cache_service
from core.services.pg_notify import pg_notify_listener

logger = logging.getLogger(__name__)

# Explicit app version marker to verify running build in logs
APP_VERSION = "feature/webapp-cabinets@4c342bb"

async def setup_routers(dp: Dispatcher):
    """Centralized function to set up all bot routers with correct priority."""

    # 1. Main menu router must be first to catch main commands
    dp.include_router(main_menu_router)

    # 2. Basic and callback routers for general commands
    dp.include_router(basic_router)
    dp.include_router(callback_router)

    # 3. Category router for category-specific logic
    category_router = get_category_router()
    dp.include_router(category_router)

    # 4. Feature-flagged routers
    if settings.features.partner_fsm:
        partner_router = get_partner_router()
        dp.include_router(partner_router)
        logger.info("✅ Partner FSM enabled")
    else:
        logger.info("⚠️ Partner FSM disabled")

    if settings.features.moderation:
        moderation_router = get_moderation_router()
        dp.include_router(moderation_router)
        logger.info("✅ Moderation enabled")
    else:
        logger.info("⚠️ Moderation disabled")


async def on_startup(bot: Bot):
    """Bot startup handler"""
    await set_commands(bot)
    logger.info("Bot started and commands set.")
    try:
        await bot.send_message(settings.bots.admin_id, f"🚀 KARMABOT1 запущен | version: {APP_VERSION}")
    except Exception as e:
        logger.warning(f"Could not send startup message to admin: {e}")
    # Start PG LISTEN (no-op if disabled)
    try:
        await pg_notify_listener.start()
    except Exception as e:
        logger.warning(f"PGNotifyListener start error: {e}")

async def on_shutdown(bot: Bot):
    """Bot shutdown handler"""
    logger.info("😴 Stopping KARMABOT1...")
    # Stop listeners/services
    try:
        await pg_notify_listener.stop()
    except Exception:
        pass
    try:
        await cache_service.close()
    except Exception:
        pass
    await profile_service.disconnect()
    try:
        await bot.send_message(settings.bots.admin_id, "😴 KARMABOT1 остановлен")
    except Exception as e:
        logger.warning(f"Could not send shutdown message to admin: {e}")

async def main():
    """Main entry point for the bot"""
    # Centralized logging with stdout + daily rotation (retention 7d by default)
    setup_logging(level=logging.INFO, retention_days=7)
    logger.info(f"🚀 Starting KARMABOT1... version={APP_VERSION}")

    ensure_database_ready()

    default_properties = DefaultBotProperties(parse_mode="HTML")
    bot = Bot(token=settings.bots.bot_token, default=default_properties)
    dp = Dispatcher()

    # Connect services
    profile_service._redis_url = settings.database.redis_url or ""
    await profile_service.connect()
    await cache_service.connect()

    # Register middlewares
    dp.update.middleware(LocaleMiddleware())

    # Register startup/shutdown handlers
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Setup all routers
    await setup_routers(dp)
    logger.info(f"✅ All routers registered successfully | version={APP_VERSION}")

    # To ensure no conflicts, we delete any existing webhook
    # and start polling cleanly.
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped by user.")
        raise
