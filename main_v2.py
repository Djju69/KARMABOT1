"""
KARMABOT1 - Enhanced main entry point with backward compatibility
Integrates all new components while preserving existing functionality
"""
import asyncio
import logging
import os
import secrets
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
from core.handlers.admin_cabinet import get_admin_cabinet_router
from core.handlers.profile import get_profile_router

# Services
from core.services.profile import profile_service
from core.services.cache import cache_service
from core.services.pg_notify import pg_notify_listener
from core.services.admins import admins_service

logger = logging.getLogger(__name__)

# Explicit app version marker to verify running build in logs
APP_VERSION = "feature/webapp-cabinets@4c342bb"

# Optional Redis client for leader lock (non-breaking)
try:
    from redis.asyncio import Redis as AsyncRedis  # type: ignore
except Exception:  # pragma: no cover
    AsyncRedis = None  # type: ignore


async def _acquire_leader_lock(redis_url: str, key: str, ttl: int):
    """Try to acquire a Redis-based leader lock.
    Returns (owned: bool, release_coro: callable|None).
    Safe no-op if Redis not available or url empty.
    """
    if not redis_url or not AsyncRedis:
        logging.getLogger(__name__).warning(
            "Polling leader lock disabled (no REDIS_URL or aioredis)"
        )
        return True, None  # allow single-instance assumption

    token = secrets.token_hex(16)
    try:
        redis = AsyncRedis.from_url(redis_url, encoding="utf-8", decode_responses=True)
        # ensure connectivity
        await redis.ping()
    except Exception as e:
        logging.getLogger(__name__).warning(
            f"Leader lock: cannot connect to Redis, proceeding without lock: {e}"
        )
        return True, None

    # Try SET NX EX
    try:
        ok = await redis.set(key, token, ex=ttl, nx=True)
    except Exception as e:
        logging.getLogger(__name__).warning(
            f"Leader lock: SET NX failed, proceeding without lock: {e}"
        )
        try:
            await redis.close()
        except Exception:
            pass
        return True, None

    if not ok:
        # Someone else holds the lock
        try:
            await redis.close()
        except Exception:
            pass
        return False, None

    logger.info("✅ Polling leader lock acquired (key=%s)", key)

    refresh_task = None

    async def _refresh_loop():
        try:
            # Refresh at 1/3 of TTL
            interval = max(1, ttl // 3)
            while True:
                await asyncio.sleep(interval)
                try:
                    # Refresh only if our token is still present
                    cur = await redis.get(key)
                    if cur != token:
                        logger.warning("Leader lock token changed/lost; stopping refresh loop")
                        break
                    await redis.expire(key, ttl)
                except Exception as e:
                    logger.warning(f"Leader lock refresh error: {e}")
                    # continue trying
        except asyncio.CancelledError:
            pass

    refresh_task = asyncio.create_task(_refresh_loop())

    async def _release():
        try:
            try:
                cur = await redis.get(key)
                if cur == token:
                    await redis.delete(key)
                    logger.info("🧹 Polling leader lock released (key=%s)", key)
            except Exception:
                pass
            if refresh_task:
                refresh_task.cancel()
                try:
                    await refresh_task
                except Exception:
                    pass
        finally:
            try:
                await redis.close()
            except Exception:
                pass

    return True, _release

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

    # 4. Profile router (inline cabinet)
    dp.include_router(get_profile_router())

    # 5. Feature-flagged routers
    if settings.features.partner_fsm:
        partner_router = get_partner_router()
        dp.include_router(partner_router)
        logger.info("✅ Partner FSM enabled")
    else:
        logger.info("⚠️ Partner FSM disabled")

    if settings.features.moderation:
        moderation_router = get_moderation_router()
        dp.include_router(moderation_router)
        # Admin cabinet router (inline menu under adm:*)
        dp.include_router(get_admin_cabinet_router())
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
    # Connect admins service (Redis or memory)
    try:
        await admins_service.connect()
    except Exception as e:
        logger.warning(f"AdminsService connect error: {e}")

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
        await admins_service.disconnect()
    except Exception:
        pass
    try:
        await bot.send_message(settings.bots.admin_id, "😴 KARMABOT1 остановлен")
    except Exception as e:
        logger.warning(f"Could not send shutdown message to admin: {e}")

async def main():
    """Main entry point for the bot"""
    # Centralized logging with stdout + daily rotation (retention 7d by default)
    setup_logging(level=logging.INFO, retention_days=7)
    logger.info(f"🚀 Starting KARMABOT1... version={APP_VERSION}")
    # Explicit config echo for deploy diagnostics (safe/masked)
    try:
        dp_flag = os.getenv("DISABLE_POLLING", "").lower()
        masked_redis = "set" if settings.database.redis_url else "empty"
        logger.info(
            "[CFG] env=%s partner_fsm=%s moderation=%s disable_polling=%s redis_url=%s",
            settings.environment,
            settings.features.partner_fsm,
            settings.features.moderation,
            dp_flag if dp_flag else "",
            masked_redis,
        )
    except Exception:
        pass
    # Optional: disable polling for "empty" deploys (e.g., to avoid conflicts on Railway)
    if os.getenv("DISABLE_POLLING", "").lower() in {"1", "true", "yes"}:
        logger.warning("Bot polling is DISABLED by DISABLE_POLLING env. Staying idle.")
        # Keep process alive without touching Telegram getUpdates
        await asyncio.Event().wait()
        return

    ensure_database_ready()

    default_properties = DefaultBotProperties(parse_mode="HTML")
    # Strip accidental whitespace/newlines to satisfy aiogram token validator
    safe_token = (settings.bots.bot_token or "").strip()
    bot = Bot(token=safe_token, default=default_properties)
    dp = Dispatcher()

    # Connect services
    profile_service._redis_url = settings.database.redis_url or ""
    await profile_service.connect()
    await cache_service.connect()
    try:
        await admins_service.connect()
    except Exception as e:
        logger.warning(f"AdminsService connect error: {e}")

    # Register middlewares
    dp.update.middleware(LocaleMiddleware())

    # Register startup/shutdown handlers
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Setup all routers
    await setup_routers(dp)
    logger.info(f"✅ All routers registered successfully | version={APP_VERSION}")

    # Optional leader lock to avoid multiple pollers
    lock_enabled = os.getenv("ENABLE_POLLING_LEADER_LOCK", "1").lower() in {"1", "true", "yes"}
    release_lock = None
    if lock_enabled:
        lock_ttl = int(os.getenv("POLLING_LEADER_LOCK_TTL", "120"))
        lock_key = f"{settings.environment}:bot:polling:leader"
        owned, release = await _acquire_leader_lock(settings.database.redis_url, lock_key, lock_ttl)
        if not owned:
            logger.error("❌ Another instance holds polling leader lock (%s). Staying idle.", lock_key)
            # Keep process alive but do not touch Telegram API
            await asyncio.Event().wait()
            return
        release_lock = release

    try:
        # To ensure no conflicts, we delete any existing webhook and start polling cleanly.
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        if release_lock:
            try:
                await release_lock()
            except Exception:
                pass


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped by user.")
        raise
