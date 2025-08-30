"""
KARMABOT1 - Main entry point with aiogram v3 compatibility
"""
from __future__ import annotations
import os
import asyncio
import logging
import logging.handlers
import secrets
import socket
import aiohttp
import re
import inspect
from pathlib import Path
from typing import Optional, Dict, Any, List, Union, Callable, Awaitable

import redis.asyncio as aioredis
from aiogram import Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.exceptions import TelegramUnauthorizedError
from aiogram.client.bot import Bot, DefaultBotProperties
from aiogram.enums import ParseMode

from core.config import Settings, load_settings

# --- Leader lock settings ---
LOCK_TTL = 300
# Get BOT_ID from environment or extract from BOT_TOKEN
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
BOT_ID_STR = os.getenv("BOT_ID", BOT_TOKEN.split(":")[0] if BOT_TOKEN and ":" in BOT_TOKEN else "0")
LOCK_KEY = f"production:bot:{BOT_ID_STR}:polling:leader"
INSTANCE = f"{os.environ.get('HOSTNAME','local')}:{os.getpid()}"
FORCE = os.getenv("LEADER_FORCE", "0") == "1"

# Redis URL from environment (required for Railway)
REDIS_URL = os.getenv("REDIS_URL")
if not REDIS_URL:
    raise ValueError("REDIS_URL environment variable is required")
    
redis: aioredis.Redis = aioredis.from_url(REDIS_URL, decode_responses=True)

# --- END: Leader lock settings ---

# Read and validate bot token
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
if not BOT_TOKEN or ":" not in BOT_TOKEN:
    raise SystemExit("❌ BOT_TOKEN is empty or contains spaces/newlines - fix in Variables")

async def acquire_leader_lock(redis: aioredis.Redis, key: str, instance: str, ttl: int, retries: int = 12):
    """Acquire leader lock with retries and force option."""
    for i in range(retries):
        if FORCE:
            await redis.set(key, instance, ex=ttl)
            logging.warning(f"⚠️ Forced leader lock acquired (key={key}, holder={instance})")
            return True
        ok = await redis.set(key, instance, nx=True, ex=ttl)
        if ok:
            logging.info(f"✅ Polling leader lock acquired (key={key}, holder={instance})")
            return True
        holder = await redis.get(key)
        remain = await redis.ttl(key)
        logging.error(f"❌ Lock held by {holder}, ttl={remain}; retry {i+1}/{retries}")
        await asyncio.sleep(max(3, min(10, (remain or 5)//3)))
    return False

def make_shutdown_handler(redis: aioredis.Redis):
    """Create a shutdown handler that releases the leader lock."""
    async def _shutdown_handler(event):
        try:
            cur = await redis.get(LOCK_KEY)
            if cur == INSTANCE:
                await redis.delete(LOCK_KEY)
                logging.info(f"🔓 Leader lock released (key={LOCK_KEY})")
        finally:
            # Close Redis connection properly
            if hasattr(redis, "aclose"):
                await redis.aclose()
            else:
                try:
                    redis.close()
                except Exception:
                    pass
    return _shutdown_handler
# --- END: Token and lock configuration ---

def get_bot_token_from_env_or_settings(settings):
    """
    ЕДИНЫЙ источник токена: BOTS__BOT_TOKEN > BOT_TOKEN > settings.bots.bot_token
    Возвращает очищенный токен без пробельных символов.
    """
    import re
    
    # Получаем токен из любого источника
    raw_token = os.getenv("BOTS__BOT_TOKEN") or os.getenv("BOT_TOKEN") \
               or getattr(getattr(settings, "bots", None), "bot_token", None)
    
    if not raw_token:
        raise RuntimeError("BOT token is not set (BOTS__BOT_TOKEN / BOT_TOKEN / settings.bots.bot_token).")
    
    # Удаляем все пробельные символы (пробелы, переносы строк, табы)
    token = re.sub(r'\s+', '', str(raw_token))
    
    # Проверяем формат токена (число:буквенно-цифровые_символы)
    if not re.match(r'^\d+:[A-Za-z0-9_-]+$', token):
        logger.error(f"❌ Invalid bot token format. First 9 chars: {token[:9]!r}...")
        raise ValueError("Invalid bot token format. Expected format: '123456789:ABCdefGHIJKLMNOPQRSTUVWXYZ'")
    
    return token

def make_lock_key(token: str) -> str:
    """
    Генерирует безопасный ключ для блокировки на основе окружения и префикса токена.
    Пример: production:bot:83635304:polling:leader
    
    Args:
        token: Токен бота в формате '123456789:ABCdef...'
    """
    # Безопасно извлекаем первую часть токена (до двоеточия)
    try:
        token_id = token.split(':', 1)[0]
    except (AttributeError, IndexError):
        token_id = 'invalid'
    
    # Очищаем ID от недопустимых символов
    import re
    token_id = re.sub(r'[^a-zA-Z0-9_-]', '', token_id)
    
    env = os.getenv("ENV", "production")
    # Убедимся, что в ключе нет переносов строк
    lock_key = f"{env}:bot:{token_id}:polling:leader".replace('\n', '').replace('\r', '')
    
    logger.debug(f"Generated lock key: {lock_key}")
    return lock_key

def _mask(t: str|None) -> str:
    """Mask sensitive information in logs."""
    if not t:
        return "<none>"
    return f"{t[:8]}…{t[-6:]}" if len(t) > 14 else "***"

def resolve_bot_token(settings):
    """Resolve and validate bot token from settings or environment."""
    try:
        # Используем нашу улучшенную функцию, которая уже делает санитизацию
        return get_bot_token_from_env_or_settings(settings)
    except Exception as e:
        logger.error(f"❌ Failed to resolve bot token: {e}")
        return None

# Load settings after environment is set up
try:
    settings = load_settings()
except Exception as e:
    logging.error("Failed to load settings: %s", str(e))
    raise

def setup_logging(level=logging.INFO, retention_days: int = 7):
    """Configure logging with file and console handlers.
    
    Args:
        level: Logging level
        retention_days: Number of days to keep log files
    """
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Set up file handler with rotation
    log_file = logs_dir / "bot.log"
    file_handler = logging.handlers.TimedRotatingFileHandler(
        log_file, when="midnight", backupCount=retention_days, encoding="utf-8"
    )
    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    )
    
    # Set up console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%H:%M:%S"
        )
    )
    
    # Configure root logger
    logging.basicConfig(
        level=level,
        handlers=[file_handler, console_handler],
        force=True  # Override any existing handlers
    )
    
    # Log environment info
    logger = logging.getLogger(__name__)
    logger.info("Starting in %s environment", settings.environment)
    logger.info("Using bot token: %s", _mask(settings.bots.bot_token))
    
    return logger

# Initialize logging
logger = setup_logging(level=logging.INFO, retention_days=7)

# Safe environment loading
try:
    from dotenv import load_dotenv
except Exception as e:
    logger.warning("Failed to import dotenv: %s", str(e))
    load_dotenv = None

# Detect production environment
IS_PROD = bool(os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("ENVIRONMENT") == "production")


def _mask_token(t: str | None) -> str:
    if not t: return "<none>"
    return f"{t[:8]}…{t[-6:]}" if len(t) > 14 else "***"

def resolve_bot_token(settings) -> str:
    t = os.getenv("BOTS__BOT_TOKEN")
    if t and t.strip():
        return t.strip()
    return getattr(getattr(settings, "bots", None), "bot_token", "")

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.client.bot import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramUnauthorizedError

# Import core config
from core.config import BOT_TOKEN, load_settings

# Load settings
settings = load_settings()

def _get_redis_url() -> str:
    """Safely get Redis URL from environment or settings."""
    return os.getenv("REDIS_URL") or ""

async def set_commands(bot: Bot) -> None:
    """Set bot commands"""
    from aiogram.types import BotCommand, BotCommandScopeDefault
    
    cmds = [
        BotCommand(command="start", description="Старт / меню"),
        BotCommand(command="help",  description="Помощь"),
    ]
    await bot.set_my_commands(cmds, scope=BotCommandScopeDefault())

async def main():
    """Main entry point"""
    settings = Settings()
    token = resolve_token(settings)
    logger.info("🔑 Environment: %s", settings.environment)
    logger.info("🔑 Using bot token: %s", _mask(token))

    bot = Bot(token=token)
    dp = Dispatcher()

    # Include routers from core.handlers
    from core.handlers import basic_router, callback_router, main_menu_router
    from core.handlers.language import router as language_router
    
    # Include all routers
    dp.include_router(basic_router)
    dp.include_router(callback_router)
    dp.include_router(main_menu_router)
    dp.include_router(language_router)  # Add language router for callback handlers

    # Set up bot commands
    await set_commands(bot)
    logger.info("✅ Bot commands set")

    try:
        # Verify bot token and get bot info
        me = await bot.get_me()
        logger.info("✅ Bot authorized: @%s (id=%s)", me.username, me.id)
        
        # Delete any existing webhook to ensure we're using polling
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("🗑️  Deleted any existing webhook")
        
    except TelegramUnauthorizedError as e:
        logger.error("❌ Invalid BOT TOKEN. %s", e)
        try: 
            await bot.session.close()
        finally: 
            raise

    logger.info("🚀 Start polling")
    await dp.start_polling(bot)

# Ensure settings.features exists
try:
    from core.config import FeatureFlags  # if exists in config.py
except ImportError:
    # minimal local stub to prevent crashes
    from pydantic import BaseModel
    class FeatureFlags(BaseModel):
        partner_fsm: bool = False
        loyalty_points: bool = True
        referrals: bool = True
        web_cabinets: bool = True

# Ensure settings.features exists
if not hasattr(settings, "features") or settings.features is None:
    settings.features = FeatureFlags()  # type: ignore[attr-defined]

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
from core.handlers.activity import get_activity_router

# Services
from core.services.profile import profile_service
from core.services.cache import init_cache_service, get_cache_service, BaseCacheService
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

# Optional asyncpg for Postgres advisory lock fallback
try:
    import asyncpg  # type: ignore
except Exception:  # pragma: no cover
    asyncpg = None  # type: ignore


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

    try:
        redis = AsyncRedis.from_url(redis_url, encoding="utf-8", decode_responses=True)
        # Try to acquire the lock with instance ID as value
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
        # Optional preempt: if PREEMPT_LEADER is set, try to delete the key and acquire again
        if os.getenv("PREEMPT_LEADER", "").lower() in {"1", "true", "yes"}:
            try:
                cur = await redis.get(key)
            except Exception:
                cur = None
            logging.getLogger(__name__).warning(
                "PREEMPT (Redis): attempting to remove existing leader lock (key=%s, cur_token=%s)", key, (cur or "<unknown>")
            )
            try:
                # Best-effort delete; not strictly safe but acceptable for single-service Railway setup
                await redis.delete(key)
            except Exception as e:
                logging.getLogger(__name__).warning("PREEMPT (Redis): delete failed: %s", e)
            # Small delay and retry SET NX
            try:
                await asyncio.sleep(0.2)
                ok2 = await redis.set(key, token, ex=ttl, nx=True)
            except Exception as e:
                logging.getLogger(__name__).warning("PREEMPT (Redis): retry SET NX failed: %s", e)
                ok2 = False
            if ok2:
                logging.getLogger(__name__).info("✅ PREEMPT SUCCESS: Redis leader lock acquired (key=%s)", key)
            else:
                try:
                    await redis.close()
                except Exception:
                    pass
                return False, None
        else:
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
            finally:
                if refresh_task:
                    refresh_task.cancel()
                    try:
                        await refresh_task
                    except Exception:
                        pass
        finally:
            try:
                if hasattr(redis, 'aclose'):
                    await redis.aclose()  # redis-py 5.x+
                else:
                    await redis.close()   # backward compatibility
            except Exception:
                pass

    return True, _release

async def _log_pg_lock_holder(conn: "asyncpg.Connection", big_key: int) -> None:
    """Log info about the process holding the advisory lock if possible.
    On Postgres, bigint advisory locks are represented as (classid, objid) int4 pair in pg_locks.
    We split the 64-bit key into two 32-bit parts: hi=classid, lo=objid.
    """
    hi = (big_key >> 32) & 0xFFFFFFFF
    lo = big_key & 0xFFFFFFFF
    rows = await conn.fetch(
        """
        SELECT l.pid, a.application_name, a.usename, a.client_addr, a.query
        FROM pg_locks l
        JOIN pg_stat_activity a ON a.pid = l.pid
        WHERE l.locktype = 'advisory'
          AND l.classid = $1::integer
          AND l.objid = $2::integer
          AND l.mode = 'ExclusiveLock'
          AND l.granted = true
        LIMIT 5
        """,
        hi, lo,
    )
    if not rows:
        logger.warning("DB lock holder not found in pg_locks (key split hi=%s lo=%s)", hi, lo)
        return
    for r in rows:
        logger.error(
            "DB lock holder: pid=%s app=%s user=%s addr=%s | query=%s",
            r["pid"], r["application_name"], r["usename"], str(r["client_addr"]), (r["query"] or "")[:120],
        )

async def _preempt_pg_leader(conn: "asyncpg.Connection", big_key: int) -> bool:
    """Attempt to terminate backends that hold the advisory lock and free it.
    Returns True if at least one backend was terminated (attempted), False otherwise.
    Guarded by env PREEMPT_LEADER.
    """
    hi = (big_key >> 32) & 0xFFFFFFFF
    lo = big_key & 0xFFFFFFFF
    rows = await conn.fetch(
        """
        SELECT l.pid
        FROM pg_locks l
        WHERE l.locktype = 'advisory'
          AND l.classid = $1::integer
          AND l.objid = $2::integer
          AND l.mode = 'ExclusiveLock'
          AND l.granted = true
        LIMIT 5
        """,
        hi, lo,
    )
    if not rows:
        return False
    terminated_any = False
    for r in rows:
        pid = r["pid"]
        try:
            ok = await conn.fetchval("SELECT pg_terminate_backend($1)", pid)
            logger.warning("PREEMPT: pg_terminate_backend(pid=%s) -> %s", pid, ok)
            if ok:
                terminated_any = True
        except Exception as e:
            logger.warning("PREEMPT: terminate pid=%s failed: %s", pid, e)
    return terminated_any

async def _acquire_pg_leader_lock(db_url: str, key: str):
    """Acquire a Postgres advisory lock as a fallback leader lock.
    Returns (owned: bool, release_coro: callable|None).
    Safe no-op if asyncpg not available or db_url empty.
    """
    if not db_url or not asyncpg:
        logging.getLogger(__name__).warning(
            "Polling DB leader lock disabled (no DATABASE_URL or asyncpg)"
        )
        return True, None

    # Convert SQLAlchemy-style URL to asyncpg-compatible DSN if needed
    dsn = db_url.replace("postgresql+asyncpg://", "postgresql://", 1)

    # Derive a 64-bit signed key from string
    key_hash = hashlib.sha256(key.encode()).digest()
    big_key = int.from_bytes(key_hash[:8], byteorder="big", signed=False)
    lock_key = big_key % (2**63)  # fit into BIGINT signed range

    try:
        conn = await asyncpg.connect(dsn)
    except Exception as e:
        logging.getLogger(__name__).warning(
            f"DB leader lock: cannot connect to Postgres, proceeding without lock: {e}"
        )
        return True, None

    try:
        ok = await conn.fetchval("SELECT pg_try_advisory_lock($1)", big_key)
    except Exception as e:
        logging.getLogger(__name__).warning(
            f"DB leader lock: pg_try_advisory_lock failed, proceeding without lock: {e}"
        )
        try:
            await conn.close()
        except Exception:
            pass
        return True, None

    if not ok:
        # Try to identify the holder for diagnostics
        try:
            await _log_pg_lock_holder(conn, big_key)
        except Exception as e:
            logger.warning("Could not fetch lock holder diagnostics: %s", e)
        # Optional preempt
        if os.getenv("PREEMPT_LEADER", "").lower() in {"1", "true", "yes"}:
            logger.warning("PREEMPT: Attempting to preempt DB advisory lock holder(s)…")
            try:
                attempted = await _preempt_pg_leader(conn, big_key)
                if attempted:
                    # small delay to allow lock release propagation
                    await asyncio.sleep(0.5)
                    try:
                        ok2 = await conn.fetchval("SELECT pg_try_advisory_lock($1)", big_key)
                    except Exception as e:
                        logger.warning("PREEMPT: retry pg_try_advisory_lock failed: %s", e)
                        ok2 = False
                    if ok2:
                        logger.info("✅ PREEMPT SUCCESS: DB advisory lock acquired (key=%s)", key)
                        async def _release():
                            try:
                                try:
                                    await conn.fetchval("SELECT pg_advisory_unlock($1)", big_key)
                                    logger.info("🧹 DB advisory lock released (key=%s)", key)
                                except Exception:
                                    pass
                            finally:
                                try:
                                    await conn.close()
                                except Exception:
                                    pass
                        return True, _release
            except Exception as e:
                logger.warning("PREEMPT: failed: %s", e)
        logger.error("❌ Another instance holds DB advisory lock (%s). Staying idle.", key)
        await conn.close()
        return False, None

    logger.info("✅ DB advisory lock acquired (key=%s)", key)

    async def _release():
        try:
            try:
                await conn.fetchval("SELECT pg_advisory_unlock($1)", big_key)
                logger.info("🧹 DB advisory lock released (key=%s)", key)
            except Exception:
                pass
        finally:
            try:
                await conn.close()
            except Exception:
                pass

    return True, _release

def dump_router(router, prefix=""):
    """Debug function to dump router's message handlers and sub-routers."""
    try:
        obs = router.observers.get("message")
        if obs:
            for h in getattr(obs, "handlers", []):
                cb = getattr(h, "callback", None)
                name = getattr(cb, "__name__", repr(cb))
                filters = getattr(h, "filters", None)
                logger.info("%s📌 message handler: %s | filters=%s", prefix, name, filters)
    except Exception as e:
        logger.error("%sError dumping router: %s", prefix, e, exc_info=True)

    # Recursively process sub-routers
    for child in getattr(router, "sub_routers", []):
        logger.info("%s➡️ child router: %r id=%s", prefix, child, id(child))
        dump_router(child, prefix + "  ")

async def setup_routers(dp: Dispatcher):
    """Centralized function to set up all bot routers with correct priority."""
    logger.info("🔧 Setting up routers...")
    
    # Add a catch-all handler at the end to log unhandled updates
    @dp.update()
    async def unhandled_update(update: Update, bot: Bot, state: FSMContext):
        """Log all unhandled updates for debugging."""
        logger.warning("⚠️ Unhandled update: %s", update)
        
        # Log more details about the update
        if update.message:
            logger.warning("📩 Unhandled message: %s (chat_id=%s, from_id=%s, text=%s)",
                         update.message.message_id,
                         update.message.chat.id,
                         update.message.from_user.id if update.message.from_user else None,
                         update.message.text)
        elif update.callback_query:
            logger.warning("🔘 Unhandled callback: %s (data=%s, from_id=%s)",
                         update.callback_query.id,
                         update.callback_query.data,
                         update.callback_query.from_user.id)

    # 1. Main menu router must be first to catch main commands
    logger.info("\n🔵 [ROUTER SETUP] Including main_menu_router...")
    logger.info("🔍 Router details: %r id=%s from %s", 
               main_menu_router, id(main_menu_router), "core.handlers.main_menu_router")
    
    # Add middleware for debugging
    @main_menu_router.message.middleware()
    async def log_middleware(handler, event: Message, data: dict):
        logger.debug(f"📨 [MAIN_MENU] Received message: {event.text} (chat_id={event.chat.id})")
        result = await handler(event, data)
        logger.debug(f"✅ [MAIN_MENU] Handled message: {event.text}")
        return result
    
    dp.include_router(main_menu_router)
    logger.info("✅ [ROUTER SETUP] main_menu_router included successfully")

    # 2. Basic and callback routers for general commands
    logger.info("\n🔗 Including basic_router...")
    logger.info("🔎 will include %r id=%s from %s", basic_router, id(basic_router), "core.handlers.basic")
    dp.include_router(basic_router)
    logger.info("🔗 include_router: %r id=%s", basic_router, id(basic_router))

    logger.info("\n🔗 Including callback_router...")
    logger.info("🔎 will include %r id=%s from %s", callback_router, id(callback_router), "core.handlers.callback")
    dp.include_router(callback_router)
    logger.info("🔗 include_router: %r id=%s", callback_router, id(callback_router))

    # 3. Category router for category-specific logic
    logger.info("\n🔗 Creating and including category_router...")
    category_router = get_category_router()
    logger.info("🔎 will include %r id=%s from %s", category_router, id(category_router), "get_category_router()")
    dp.include_router(category_router)
    logger.info("🔗 include_router: %r id=%s", category_router, id(category_router))

    # 4. Profile router (inline cabinet)
    logger.info("\n🔗 Creating and including profile_router...")
    profile_router = get_profile_router()
    logger.info("🔎 will include %r id=%s from %s", profile_router, id(profile_router), "get_profile_router()")
    dp.include_router(profile_router)
    logger.info("🔗 include_router: %r id=%s", profile_router, id(profile_router))

    # 4.1 Activity (Loyalty) router
    logger.info("\n🔗 Creating and including activity_router...")
    activity_router = get_activity_router()
    logger.info("🔎 will include %r id=%s from %s", activity_router, id(activity_router), "get_activity_router()")
    dp.include_router(activity_router)
    logger.info("🔗 include_router: %r id=%s", activity_router, id(activity_router))

    # 5. Feature-flagged routers
    if getattr(settings.features, "partner_fsm", False):
        logger.info("\n🔗 Creating and including partner_router...")
        partner_router = get_partner_router()
        logger.info("🔎 will include %r id=%s from %s", partner_router, id(partner_router), "get_partner_router()")
        dp.include_router(partner_router)
        logger.info("🔗 include_router: %r id=%s", partner_router, id(partner_router))
        logger.info("✅ Partner FSM enabled")
    else:
        logger.info("⚠️ Partner FSM disabled")

    if getattr(settings.features, "moderation", False):
        logger.info("\n🔗 Creating and including moderation_router...")
        moderation_router = get_moderation_router()
        logger.info("🔎 will include %r id=%s from %s", moderation_router, id(moderation_router), "get_moderation_router()")
        dp.include_router(moderation_router)
        logger.info("🔗 include_router: %r id=%s", moderation_router, id(moderation_router))
        
        # Admin cabinet router (inline menu under adm:*)
        logger.info("\n🔗 Creating and including admin_router...")
        admin_router = get_admin_cabinet_router()
        logger.info("🔎 will include %r id=%s from %s", admin_router, id(admin_router), "get_admin_cabinet_router()")
        dp.include_router(admin_router)
        logger.info("🔗 include_router: %r id=%s", admin_router, id(admin_router))
        logger.info("✅ Moderation and Admin Cabinet enabled")
    else:
        logger.info("⚠️ Moderation and Admin Cabinet disabled")
    
    # Dump all registered handlers for debugging
    logger.info("\n==== ROUTERS DUMP START ====")
    dump_router(dp)
    logger.info("==== ROUTERS DUMP END ====\n")

async def _preflight_polling_conflict(bot_token: str) -> bool:
    """Call Telegram getUpdates once to detect 409 Conflict preflight.
    Returns True if conflict is detected and we should stay idle.
    """
    if not bot_token:
        return False
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates?timeout=0&offset=-1"
    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as resp:
                if resp.status == 409:
                    text = await resp.text()
                    logger.error("❌ Preflight: Telegram Conflict detected: %s", text[:200])
                    return True
                # In rare cases TG returns 200 with ok=false and description containing Conflict
                if resp.status == 200:
                    data = await resp.json(content_type=None)
                    if not data.get("ok") and "Conflict" in str(data.get("description", "")):
                        logger.error("❌ Preflight: Telegram Conflict detected (ok=false): %s", data)
                        return True
    except Exception as e:
        # Do not block startup on preflight errors; assume no conflict
        logger.warning("Preflight getUpdates check failed: %s", e)
    return False


async def on_startup(bot: Bot):
    """Bot startup handler"""
    logger.info("🚀 Bot startup sequence started")
    
    # Set bot commands
    try:
        await set_commands(bot)
        logger.info("✅ Bot commands set")
    except Exception as e:
        logger.error(f"❌ Failed to set bot commands: {e}")
        raise
    
    # Initialize database connection pool
    try:
        from core.database import init_db
        await init_db()
        logger.info("✅ Database pool initialized")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise
    
    # Verify Redis connection
    try:
        if not hasattr(bot, '_redis_initialized'):
            await redis.ping()
            bot._redis_initialized = True
            logger.info("✅ Redis connection verified")
    except Exception as e:
        logger.error(f"❌ Redis connection failed: {e}")
        raise
    
    logger.info("🚀 Bot startup completed")
    # Send startup message to admin
    admin_id = getattr(settings.bots, "admin_id", None)
    if isinstance(admin_id, int):
        try:
            await bot.send_message(admin_id, "✅ Bot started and commands set.")
        except Exception as e:
            logger.warning("Could not send startup message to admin: %s", e)
    else:
        logger.warning("Admin ID is not set or invalid; skip startup notify.")
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

async def on_shutdown(dp: Dispatcher):
    """Bot shutdown handler"""
    logger.info("😴 Stopping KARMABOT1...")
    
    # Close Redis connection and release lock
    logger.info("🔌 Closing Redis connection...")
    await close_redis()
    logger.info("✅ Redis connection closed")
    
    # Try to send shutdown notification to admin
    try:
        admin_id = getattr(settings.bots, "admin_id", None)
        if isinstance(admin_id, int):
            await bot.send_message(admin_id, "😴 KARMABOT1 остановлен")
    except Exception as e:
        logger.warning(f"Could not send shutdown message to admin: {e}")
    
    # Stop PG notify listener
    try:
        await pg_notify_listener.stop()
    except Exception as e:
        logger.warning(f"Error stopping PG notify listener: {e}")
    
    # Close cache service
    try:
        cache_service = get_cache_service()
        if hasattr(cache_service, 'close') and callable(getattr(cache_service, 'close')):
            await cache_service.close()
            logger.info("✅ Cache service closed")
    except Exception as e:
        logger.warning(f"Error closing cache service: {e}")
    
    # Disconnect services
    try:
        await profile_service.disconnect()
        logger.info("✅ Profile service disconnected")
    except Exception as e:
        logger.warning(f"Error disconnecting profile service: {e}")
    
    try:
        await admins_service.disconnect()
        logger.info("✅ Admins service disconnected")
    except Exception as e:
        logger.warning(f"Error disconnecting admins service: {e}")
    
    # Ensure bot session is closed
    try:
        if not bot.session.closed:
            await bot.session.close()
            logger.info("✅ Bot session closed")
    except Exception as e:
        logger.warning(f"Error closing bot session: {e}")
    
    logger.info("✅ KARMABOT1 shutdown complete")

async def main():
    """Main entry point for the bot"""
    # Centralized logging with stdout + daily rotation (retention 7d by default)
    setup_logging(level=logging.INFO, retention_days=7)
    logger.info(f"🚀 Starting KARMABOT1... version={APP_VERSION}")
    
    # Initialize Redis
    redis_url = _get_redis_url()
    if not redis_url:
        logger.error("❌ REDIS_URL not configured")
        return
        
    redis = aioredis.from_url(redis_url, decode_responses=True)
    
    # Initialize Dispatcher and register shutdown handler
    dp = Dispatcher()
    dp.shutdown.register(make_shutdown_handler(redis))
    
    # Include routers
    from core.handlers import ping
    dp.include_router(ping.router)
    
    # Ensure database is ready
    ensure_database_ready()
    
    # Log environment info
    env = settings.environment or "production"
    logger.info(f"🔑 Environment: {env}")
    
    # Leader lock settings
    lock_key = f"production:bot:{BOT_TOKEN.split(':')[0]}:polling:leader"
    instance = f"{os.getenv('HOSTNAME','local')}:{os.getpid()}"
    lock_ttl = 300  # 5 minutes TTL for lock
    
    logger.info(f"🔑 Lock key: {lock_key}")
    logger.info(f"🔑 Instance: {instance}")
    
    try:
        # Initialize bot with context manager
        async with Bot(
            token=BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        ) as bot:
            # Test Redis connection
            try:
                ok = await redis.ping()
                logger.info(f"✅ Redis ping: {ok}")
            except Exception as e:
                logger.error(f"❌ Redis connection failed: {e}")
                return
            
            # Try to acquire leader lock
            got_lock = await acquire_leader_lock(redis, lock_key, instance, lock_ttl, retries=12)
            if not got_lock:
                logger.error("❌ Failed to acquire leader lock after retries, exiting...")
                return
            
            # Set bot commands
            try:
                await set_commands(bot)
                logger.info("✅ Bot commands set")
            except Exception as e:
                logger.error(f"❌ Failed to set bot commands: {e}", exc_info=True)
                return
            
            # Start the bot with allowed updates
            logger.info("🚀 Starting bot polling...")
            await dp.start_polling(
                bot,
                allowed_updates=dp.resolve_used_update_types(),
                drop_pending_updates=True
            )
            
    except Exception as e:
        logger.error(f"❌ Fatal error in main: {e}", exc_info=True)
        raise
    
    # Preflight check with Telegram API
    try:
        me = await bot.get_me()
        logger.info("✅ Bot authorized: @%s (id=%s)", me.username, me.id)
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("🗑️  Deleted any existing webhook")
        
    except TelegramUnauthorizedError as e:
        logger.error("❌ Invalid BOT TOKEN (BOTS__BOT_TOKEN). %s", e)
        # Properly close the session before exiting
        try:
            await bot.session.close()
        except Exception as e:
            logger.error("Error closing bot session: %s", e)
        return  # Exit if token is invalid
    except Exception as e:
        logger.error("❌ Preflight check failed: %s", e, exc_info=True)
        try:
            await bot.session.close()
        except Exception:
            pass
        return
            
    dp = Dispatcher()

    # Connect services
    # Initialize cache service
    redis_url = _get_redis_url()
    try:
        # Initialize and get the cache service with proper await
        cache_service = await get_cache_service()
        # Check if we're using Redis
        if hasattr(cache_service, 'client') and cache_service.client is not None:
            await cache_service.ping()  # Test connection
            logger.info(f"Initialized Redis cache at {redis_url}")
        else:
            logger.warning("Using NullCacheService - Redis not available")
    except Exception as e:
        logger.error(f"Cache initialization error: {e}")
        logger.warning("Falling back to NullCacheService")
        from core.services.cache import NullCacheService
        cache_service = NullCacheService()

    # Register middlewares
    dp.update.middleware(LocaleMiddleware())

    # Setup dispatcher with our bot
    dp = Dispatcher()
    dp.startup.register(on_startup)
    
    # Create a partial function to pass redis to on_shutdown
    from functools import partial
    shutdown_handler = partial(on_shutdown, redis=redis)
    dp.shutdown.register(shutdown_handler)

    # Setup all routers
    await setup_routers(dp)
    logger.info(f"✅ All routers registered successfully | version={APP_VERSION}")

    # Optional leader lock to avoid multiple pollers
    lock_enabled = os.getenv("ENABLE_POLLING_LEADER_LOCK", "1").lower() in {"1", "true", "yes"}
    release_lock = None
    
    if lock_enabled:
        lock_ttl = int(os.getenv("POLLING_LEADER_TTL", "300"))  # 5 minutes by default
        
        # Log instance info for debugging
        logger.info(f"🔄 Acquiring leader lock (key={LOCK_KEY}, instance={INSTANCE_ID}, ttl={lock_ttl}s)")
        
        # Try Redis lock first
        owned, release = await _acquire_leader_lock(redis_url, LOCK_KEY, lock_ttl)
        
        if not owned:
            logger.error("❌ Another instance holds the leader lock")
            if os.getenv("EXIT_ON_CONFLICT", "1").lower() in {"1", "true", "yes"}:
                logger.info("EXIT_ON_CONFLICT=1 → Exiting (leader lock held by another instance)")
                return
                
            # If not exiting, wait forever to keep the container alive
            logger.warning("🔄 Waiting for leader lock to be released...")
            while True:
                await asyncio.sleep(60)
                owned, _ = await _acquire_leader_lock(redis_url, LOCK_KEY, lock_ttl)
                if owned:
                    logger.info("✅ Acquired leader lock after waiting")
                    break
                    
        release_lock = release
        
        # Start background task to refresh the lock
        async def refresh_lock():
            while True:
                await asyncio.sleep(lock_ttl // 2)  # Refresh at half TTL
                if release_lock is None:
                    break
                try:
                    redis = AsyncRedis.from_url(redis_url, encoding="utf-8", decode_responses=True)
                    await redis.setex(LOCK_KEY, lock_ttl, INSTANCE_ID)
                    await redis.close()
                    logger.debug(f"♻️ Refreshed leader lock (ttl={lock_ttl}s)")
                except Exception as e:
                    logger.error(f"❌ Failed to refresh leader lock: {e}")
        
        # Start the refresh task
        refresh_task = asyncio.create_task(refresh_lock())
        
        # Cleanup function to stop refresh and release lock
        async def cleanup():
            if release_lock:
                logger.info("🔓 Releasing leader lock on shutdown")
                await release_lock()
            refresh_task.cancel()
            try:
                await refresh_task
            except asyncio.CancelledError:
                pass
        
        # Register cleanup
        import atexit
        atexit.register(lambda: asyncio.run(cleanup()))

    try:
        # To ensure no conflicts, we delete any existing webhook and start polling cleanly.
        await bot.delete_webhook(drop_pending_updates=True)
        # Preflight: if another instance is polling (even foreign), go idle
        if await _preflight_polling_conflict(safe_token):
            logger.error("❌ Another instance is actively polling (preflight).")
            if os.getenv("EXIT_ON_CONFLICT", "").lower() in {"1", "true", "yes"}:
                logger.info("EXIT_ON_CONFLICT=1 → exiting instead of waiting (preflight)")
                return
            logger.error("Staying idle.")
            await asyncio.Event().wait()
            return
        await dp.start_polling(bot)
    finally:
        # Release distributed lock if held
        if release_lock:
            try:
                await release_lock()
            except Exception as e:
                logger.warning("Error releasing lock: %s", e)
                
        # Close bot session
        try:
            await bot.session.close()
        except Exception as e:
            logger.warning("Error closing bot session: %s", e)
            
        # Close Redis connection if it exists in cache service
        try:
            cache_service = await get_cache_service()
            if hasattr(cache_service, 'client') and cache_service.client is not None:
                if hasattr(cache_service.client, 'aclose'):
                    await cache_service.client.aclose()
                elif hasattr(cache_service.client, 'close'):
                    await cache_service.client.close()
        except Exception as e:
            logger.warning("Error closing Redis connection: %s", e)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped")
    except Exception as e:
        logger.exception("Fatal error in main()")
        raise
