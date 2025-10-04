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
import json
from aiogram import Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.exceptions import TelegramUnauthorizedError
from aiogram.client.bot import Bot, DefaultBotProperties
from aiogram.enums import ParseMode

from core.settings import Settings, get_settings, Features
from core.database.migrations import ensure_database_ready

# Переменная для отключения webhook (для тестирования)
DISABLE_WEBHOOK = os.getenv("DISABLE_WEBHOOK", "false").lower() == "true"

# Принудительное обновление версии
VERSION = "v2.1.0-port-fix"

# === ИНТЕГРАЦИЯ MULTI-PLATFORM API ===
try:
    from api.platform_endpoints import main_router
    from core.database.enhanced_unified_service import enhanced_unified_db
    MULTI_PLATFORM_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Multi-platform API not available: {e}")
    MULTI_PLATFORM_AVAILABLE = False

# --- Leader lock settings ---
LOCK_TTL = 300
# Get BOT_ID from environment or extract from BOT_TOKEN
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
BOT_ID_STR = os.getenv("BOT_ID", BOT_TOKEN.split(":")[0] if BOT_TOKEN and ":" in BOT_TOKEN else "0")
LOCK_KEY = f"production:bot:{BOT_ID_STR}:polling:leader"
INSTANCE = f"{os.environ.get('HOSTNAME','local')}:{os.getpid()}"
FORCE = os.getenv("LEADER_FORCE", "0") == "1"

# Redis URL from environment (optional; if missing, run without distributed lock)
REDIS_URL = os.getenv("REDIS_URL", "").strip()
redis: aioredis.Redis | None = None
if REDIS_URL:
    try:
        redis = aioredis.from_url(REDIS_URL, decode_responses=True)
    except Exception as e:
        logging.warning(f"Redis init failed, continue without lock: {e}")

# --- END: Leader lock settings ---

# Validate bot token
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
        logging.getLogger(__name__).error(f"❌ Invalid bot token format. First 9 chars: {token[:9]!r}...")
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

# Load settings after environment is set up (use core.settings.get_settings)
try:
    settings = get_settings()
    # Ensure features exist
    if not hasattr(settings, "features") or settings.features is None:
        settings.features = Features()
    # Force-enable required feature flags per production baseline
    settings.features.partner_fsm = True
    logging.getLogger(__name__).info("✅ Features: %s", settings.features)
except Exception as e:
    logging.error("Failed to load settings via get_settings(): %s", str(e))
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
    logger.info("Using bot token: %s", _mask(settings.bot_token))
    
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

import os

# Import core config
# removed stray import of load_settings

# Get BOT_TOKEN from environment variables (already validated above)
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required")

def _get_redis_url() -> str:
    """Safely get Redis URL from environment or settings."""
    return os.getenv("REDIS_URL") or ""

async def set_commands(bot: Bot) -> None:
    """Delegate commands setup to the centralized commands module."""
    try:
        from core.handlers.commands import set_commands as set_core_commands
        await set_core_commands(bot)
    except Exception as e:
        logger.error("set_commands failed: %s", e, exc_info=True)
        raise

# Первая функция main() удалена - используется вторая более полная версия
async def main():
    """Main entry point for the bot"""
    # Initialize logging first
    setup_logging()
    
    # Single instance check removed - function was not defined
    # This was causing NameError in production
        
    # Get Redis URL
    redis_url = _get_redis_url()
    setup_logging(level=logging.INFO, retention_days=7)
    logger.info("🚀 Starting KARMABOT1...")
    logger.info(f"📦 Version: {VERSION}")
    
    # Initialize Redis (optional)
    redis_url = _get_redis_url()
    redis = aioredis.from_url(redis_url, decode_responses=True) if redis_url else None
    
    # Initialize performance service
    try:
        from core.services.performance_service import performance_service
        await performance_service.initialize()
        logger.info("🚀 Performance service initialized")
    except Exception as e:
        logger.warning(f"Failed to initialize performance service: {e}")

    # Initialize analytics service
    try:
        from core.services.analytics_service import analytics_service
        await analytics_service.initialize()
        logger.info("📊 Analytics service initialized")
    except Exception as e:
        logger.warning(f"Failed to initialize analytics service: {e}")
    
    # Initialize notification service
    try:
        from core.services.notification_service import notification_service
        await notification_service.initialize()
        logger.info("📱 Notification service initialized")
    except Exception as e:
        logger.warning(f"Failed to initialize notification service: {e}")
    
    # Initialize Dispatcher and register shutdown handler
    dp = Dispatcher()
    if redis is not None:
        dp.shutdown.register(make_shutdown_handler(redis))
    
    # Include routers in canonical order: main_menu -> basic -> callback -> categories -> profile -> cabinet -> activity -> partner/moderation -> admin -> ping (last)
    from core.handlers import (
        basic_router,
        callback_router,
    )
    from core.handlers.main_menu_router import main_menu_router
    from core.handlers.category_handlers_v2 import get_category_router
    from core.handlers.profile import get_profile_router
    from core.handlers.cabinet_router import get_cabinet_router
    from core.handlers.activity import get_activity_router
    from core.handlers.moderation import get_moderation_router
    from core.handlers.admin_cabinet import get_admin_cabinet_router
    from core.handlers import ping

    # 1) Main menu first
    dp.include_router(main_menu_router)
    # 2) Basic and callback
    dp.include_router(basic_router)
    dp.include_router(callback_router)
    # 3) Categories
    dp.include_router(get_category_router())
    # 4) Profile and cabinet
    prof = get_profile_router()
    if prof:
        dp.include_router(prof)
    dp.include_router(get_cabinet_router())
    # 5) Activity
    dp.include_router(get_activity_router())
    # 6) Partner router
    from core.handlers.partner import partner_router as partner_router_instance
    dp.include_router(partner_router_instance)
    # 7) Moderation and admin (under feature flag if needed)
    if getattr(settings.features, "moderation", True):
        dp.include_router(get_moderation_router())
        dp.include_router(get_admin_cabinet_router())
    
    # 8) Loyalty settings FSM
    from core.handlers.loyalty_settings_router import router as loyalty_settings_router
    dp.include_router(loyalty_settings_router)
    
    # 9) Tariff management (admin only)
    from core.handlers.tariff_admin_router import router as tariff_admin_router
    dp.include_router(tariff_admin_router)
    
    # 9.1) Tariff commands for all users
    from core.handlers.tariffs_user_router import router as tariffs_user_router
    dp.include_router(tariffs_user_router)
    
    # 9.2) Language selection router
    from core.handlers.language_router import router as language_router
    dp.include_router(language_router)
    
    # 9.3) Gamification router
    from core.handlers.gamification_router import router as gamification_router
    dp.include_router(gamification_router)
    
    # 10) ВРЕМЕННЫЙ роутер для исправления каталога
    from core.handlers.temp_catalog_fix import temp_router
    dp.include_router(temp_router)
    
    # 10) Ping/catch-alls LAST
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
            if redis is not None:
                try:
                    ok = await redis.ping()
                    logger.info(f"✅ Redis ping: {ok}")
                except Exception as e:
                    logger.warning(f"⚠️ Redis connection failed, continue without lock: {e}")
                    redis = None
            
            # Try to acquire leader lock
            if redis is not None:
                got_lock = await acquire_leader_lock(redis, lock_key, instance, lock_ttl, retries=12)
                if not got_lock:
                    logger.error("❌ Failed to acquire leader lock after retries, exiting...")
                    return
                
                # Устанавливаем обработчик завершения для освобождения блокировки
                shutdown_handler = make_shutdown_handler(redis)
                import signal
                import asyncio
                
                def signal_handler(signum, frame):
                    asyncio.create_task(shutdown_handler(None))
                
                signal.signal(signal.SIGTERM, signal_handler)
                signal.signal(signal.SIGINT, signal_handler)
            
            # Set bot commands
            try:
                await set_commands(bot)
                logger.info("✅ Bot commands set")
            except Exception as e:
                logger.error(f"❌ Failed to set bot commands: {e}", exc_info=True)
                return
            
            # НОВАЯ ЛОГИКА ЗАПУСКА:
            if DISABLE_WEBHOOK:
                # ============================================
                # РЕЖИМ ТЕСТИРОВАНИЯ - WEBHOOK ОТКЛЮЧЕН
                # ============================================
                logger.info("="*60)
                logger.info("⚠️  РЕЖИМ ТЕСТИРОВАНИЯ - WEBHOOK ОТКЛЮЧЕН")
                logger.info("   Бот работает через long polling")
                logger.info("="*60)
                
                # Проверяем webhook перед запуском polling
                webhook_info = await bot.get_webhook_info()
                if webhook_info.url:
                    logger.info(f"⚠️  Webhook активен: {webhook_info.url}")
                    logger.info("   Удаляем webhook для polling...")
                    await bot.delete_webhook(drop_pending_updates=True)
                    logger.info("✅ Webhook удален")
                else:
                    logger.info("✅ Webhook не активен, можно запускать polling")
                
                await dp.start_polling(
                    bot,
                    allowed_updates=dp.resolve_used_update_types(),
                    skip_updates=False
                )
                
            else:
                # ============================================
                # ОБЫЧНЫЙ РЕЖИМ - WEBHOOK ВКЛЮЧЕН
                # ============================================
                logger.info("✅ ПРОДАКШЕН РЕЖИМ - WEBHOOK АКТИВЕН")
                
                WEBHOOK_URL = os.getenv("WEBHOOK_URL") or os.getenv("RAILWAY_STATIC_URL")
                
                if not WEBHOOK_URL:
                    logger.error("❌ WEBHOOK_URL не установлен!")
                    return
                
                if not WEBHOOK_URL.startswith("http"):
                    WEBHOOK_URL = f"https://{WEBHOOK_URL}"
                
                webhook_path = "/webhook"
                full_webhook_url = f"{WEBHOOK_URL}{webhook_path}"
                
                await bot.delete_webhook(drop_pending_updates=True)
                await bot.set_webhook(url=full_webhook_url, drop_pending_updates=True)
                
                logger.info(f"✅ Webhook: {full_webhook_url}")
                
                # ЗАПУСК WEB СЕРВЕРА
                from aiohttp import web
                from aiohttp.web import Request, Response
                
                async def webhook_handler(request: Request) -> Response:
                    """Handle incoming webhook updates"""
                    try:
                        data = await request.json()
                        update = types.Update(**data)
                        await dp.feed_update(bot, update)
                        return Response(text="OK")
                    except Exception as e:
                        logger.error(f"Webhook error: {e}")
                        return Response(text="Error", status=500)
                
                app = web.Application()
                app.router.add_post("/webhook", webhook_handler)
                
                # Health check endpoint
                async def health_handler(request: Request) -> Response:
                    return Response(text="OK")
                
                app.router.add_get("/health", health_handler)
                
                # Start web server
                runner = web.AppRunner(app)
                await runner.setup()
                
                # Используем порт 8000 для webhook сервера (не конфликтует с Railway)
                webhook_port = int(os.getenv('WEBHOOK_PORT', 8000))
                site = web.TCPSite(runner, '0.0.0.0', webhook_port)
                await site.start()
                
                logger.info("🌐 Web server started")
                
                # Keep running
                try:
                    await asyncio.Future()  # Run forever
                except KeyboardInterrupt:
                    logger.info("🛑 Shutting down...")
                finally:
                    await runner.cleanup()
            
    except Exception as e:
        logger.error(f"❌ Fatal error in main: {e}", exc_info=True)
        # Освобождаем блокировку при ошибке
        if redis is not None:
            try:
                shutdown_handler = make_shutdown_handler(redis)
                await shutdown_handler(None)
            except Exception as cleanup_error:
                logger.error(f"❌ Failed to cleanup Redis lock: {cleanup_error}")
        raise
    
    # Preflight check with Telegram API
    try:
        me = await bot.get_me()
        logger.info("✅ Bot authorized: @%s (id=%s)", me.username, me.id)
        
        # Удаляем webhook только если планируем использовать polling
        if DISABLE_WEBHOOK:
            await bot.delete_webhook(drop_pending_updates=True)
            logger.info("🗑️  Deleted any existing webhook (polling mode)")
        else:
            logger.info("✅ Webhook mode - keeping existing webhook")
        
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
    
    # Add rate limiting middleware
    rate_limit_middleware = create_rate_limit_middleware(REDIS_URL)
    dp.update.middleware(rate_limit_middleware)

    # Setup dispatcher with our bot
    dp = Dispatcher()
    dp.startup.register(on_startup)
    
    # Create a partial function to pass redis to on_shutdown
    from functools import partial
    shutdown_handler = partial(on_shutdown, redis=redis)
    dp.shutdown.register(shutdown_handler)

    # Setup all routers
    await setup_routers(dp)
    logger.info("✅ All routers registered successfully")

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
        # Удаляем webhook только если планируем использовать polling
        if DISABLE_WEBHOOK:
            await bot.delete_webhook(drop_pending_updates=True)
            logger.info("🗑️  Deleted any existing webhook for polling (distributed lock)")
        else:
            logger.info("✅ Webhook mode - keeping existing webhook (distributed lock)")
        
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
    # Запуск multiplatform ПЕРЕД основным ботом
    try:
        import subprocess
        import os
        if os.path.exists("multiplatform/main_api.py"):
            print("Starting multiplatform system...")
            subprocess.Popen(["python", "multiplatform/main_api.py"])
            print("Multiplatform started on port 8001")
    except Exception as e:
        print(f"Failed to start multiplatform: {e}")
    
    try:
        # Start simple web server in background thread
        import threading
        from http.server import HTTPServer, SimpleHTTPRequestHandler
        import os
        
        def start_web_server():
            port = int(os.getenv("API_PORT", 8080))
            os.chdir("webapp")  # Serve files from webapp directory
            
            # Создаем кастомный обработчик с API эндпоинтами
            class CustomHTTPRequestHandler(SimpleHTTPRequestHandler):
                def do_GET(self):
                    if self.path.startswith('/api/'):
                        self.handle_api_request()
                    else:
                        super().do_GET()
                
                def do_POST(self):
                    if self.path.startswith('/api/'):
                        self.handle_api_request()
                    else:
                        super().do_POST()
                
                def do_OPTIONS(self):
                    if self.path.startswith('/api/'):
                        self.send_response(200)
                        self.send_header('Access-Control-Allow-Origin', '*')
                        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                        self.end_headers()
                    else:
                        super().do_OPTIONS()
                
                def handle_api_request(self):
                    try:
                        import sys
                        import os
                        
                        # Добавляем путь к корню проекта
                        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                        
                        from core.database.db_adapter import db_v2
                        
                        if self.path == '/api/moderation/applications':
                            # Получаем заявки партнеров
                            if db_v2.use_postgresql:
                                applications = db_v2.postgresql_service.fetch_all_sync("""
                                    SELECT id, name, phone, email, telegram_user_id, created_at, status
                                    FROM partner_applications 
                                    WHERE status = 'pending' 
                                    ORDER BY created_at ASC 
                                    LIMIT 50
                                """)
                            else:
                                applications = db_v2.sqlite_service.fetch_all("""
                                    SELECT id, name, phone, email, telegram_user_id, created_at, status
                                    FROM partner_applications 
                                    WHERE status = 'pending' 
                                    ORDER BY created_at ASC 
                                    LIMIT 50
                                """)
                            
                            apps_list = []
                            for app in applications:
                                apps_list.append({
                                    'id': app['id'],
                                    'name': app['name'],
                                    'phone': app['phone'],
                                    'email': app['email'],
                                    'telegram_user_id': app['telegram_user_id'],
                                    'created_at': app['created_at'].isoformat() if hasattr(app['created_at'], 'isoformat') else str(app['created_at']),
                                    'status': app['status']
                                })
                            
                            response = {
                                'success': True,
                                'applications': apps_list,
                                'count': len(apps_list)
                            }
                            
                            self.send_json_response(response)
                            
                        elif self.path.startswith('/api/moderation/approve/'):
                            app_id = self.path.split('/')[-1]
                            if db_v2.use_postgresql:
                                db_v2.postgresql_service.execute_sync("""
                                    UPDATE partner_applications 
                                    SET status = 'approved', updated_at = CURRENT_TIMESTAMP
                                    WHERE id = ?
                                """, (app_id,))
                            else:
                                db_v2.sqlite_service.execute("""
                                    UPDATE partner_applications 
                                    SET status = 'approved', updated_at = CURRENT_TIMESTAMP
                                    WHERE id = ?
                                """, (app_id,))
                            
                            self.send_json_response({'success': True, 'message': 'Заявка одобрена'})
                            
                        elif self.path.startswith('/api/moderation/reject/'):
                            app_id = self.path.split('/')[-1]
                            if db_v2.use_postgresql:
                                db_v2.postgresql_service.execute_sync("""
                                    UPDATE partner_applications 
                                    SET status = 'rejected', updated_at = CURRENT_TIMESTAMP
                                    WHERE id = ?
                                """, (app_id,))
                            else:
                                db_v2.sqlite_service.execute("""
                                    UPDATE partner_applications 
                                    SET status = 'rejected', updated_at = CURRENT_TIMESTAMP
                                    WHERE id = ?
                                """, (app_id,))
                            
                            self.send_json_response({'success': True, 'message': 'Заявка отклонена'})
                            
                        elif self.path == '/api/admin/tariffs':
                            # Получаем тарифы для админ кабинета
                            try:
                                if db_v2.use_postgresql:
                                    tariffs = db_v2.postgresql_service.fetch_all_sync("""
                                        SELECT id, name, tariff_type, price_vnd, max_transactions_per_month, 
                                               commission_rate, analytics_enabled, priority_support, api_access,
                                               custom_integrations, dedicated_manager, description, is_active, created_at
                                        FROM partner_tariffs 
                                        ORDER BY price_vnd ASC
                                    """)
                                else:
                                    tariffs = db_v2.sqlite_service.fetch_all("""
                                        SELECT id, name, tariff_type, price_vnd, max_transactions_per_month, 
                                               commission_rate, analytics_enabled, priority_support, api_access,
                                               custom_integrations, dedicated_manager, description, is_active, created_at
                                        FROM partner_tariffs 
                                        ORDER BY price_vnd ASC
                                    """)
                                
                                self.send_json_response({
                                    'success': True,
                                    'data': {
                                        'tariffs': [dict(tariff) for tariff in tariffs]
                                    }
                                })
                            except Exception as e:
                                self.send_json_response({'success': False, 'error': str(e)}, status=500)
                            
                        elif self.path == '/api/admin/stats':
                            # Получаем статистику для админ кабинета
                            try:
                                if db_v2.use_postgresql:
                                    users_count = db_v2.postgresql_service.fetch_all_sync("SELECT COUNT(*) as count FROM users")[0]['count']
                                    partners_count = db_v2.postgresql_service.fetch_all_sync("SELECT COUNT(*) as count FROM partners_v2")[0]['count']
                                else:
                                    users_count = db_v2.sqlite_service.fetch_all("SELECT COUNT(*) as count FROM users")[0]['count']
                                    partners_count = db_v2.sqlite_service.fetch_all("SELECT COUNT(*) as count FROM partners_v2")[0]['count']
                                
                                self.send_json_response({
                                    'success': True,
                                    'data': {
                                        'users_count': users_count,
                                        'partners_count': partners_count
                                    }
                                })
                            except Exception as e:
                                self.send_json_response({'success': False, 'error': str(e)}, status=500)
                                
                        elif self.path == '/api/moderation/applications':
                            # Получаем заявки на модерацию
                            try:
                                if db_v2.use_postgresql:
                                    applications = db_v2.postgresql_service.fetch_all_sync("""
                                        SELECT pa.id, pa.user_id, pa.company_name, pa.description, 
                                               pa.status, pa.created_at, pa.updated_at,
                                               u.first_name, u.last_name, u.username
                                        FROM partner_applications pa
                                        LEFT JOIN users u ON pa.user_id = u.telegram_id
                                        WHERE pa.status = 'pending'
                                        ORDER BY pa.created_at DESC
                                    """)
                                else:
                                    applications = db_v2.sqlite_service.fetch_all("""
                                        SELECT pa.id, pa.user_id, pa.company_name, pa.description, 
                                               pa.status, pa.created_at, pa.updated_at,
                                               u.first_name, u.last_name, u.username
                                        FROM partner_applications pa
                                        LEFT JOIN users u ON pa.user_id = u.telegram_id
                                        WHERE pa.status = 'pending'
                                        ORDER BY pa.created_at DESC
                                    """)
                                
                                self.send_json_response({
                                    'success': True,
                                    'data': {
                                        'applications': [dict(app) for app in applications]
                                    }
                                })
                            except Exception as e:
                                self.send_json_response({'success': False, 'error': str(e)}, status=500)
                                
                        elif self.path.startswith('/api/moderation/approve/'):
                            # Одобрить заявку
                            try:
                                app_id = self.path.split('/')[-1]
                                if db_v2.use_postgresql:
                                    db_v2.postgresql_service.execute_sync("""
                                        UPDATE partner_applications 
                                        SET status = 'approved', updated_at = CURRENT_TIMESTAMP
                                        WHERE id = ?
                                    """, (app_id,))
                                else:
                                    db_v2.sqlite_service.execute("""
                                        UPDATE partner_applications 
                                        SET status = 'approved', updated_at = CURRENT_TIMESTAMP
                                        WHERE id = ?
                                    """, (app_id,))
                                
                                self.send_json_response({'success': True, 'message': 'Заявка одобрена'})
                            except Exception as e:
                                self.send_json_response({'success': False, 'error': str(e)}, status=500)
                                
                        elif self.path.startswith('/api/moderation/reject/'):
                            # Отклонить заявку
                            try:
                                app_id = self.path.split('/')[-1]
                                if db_v2.use_postgresql:
                                    db_v2.postgresql_service.execute_sync("""
                                        UPDATE partner_applications 
                                        SET status = 'rejected', updated_at = CURRENT_TIMESTAMP
                                        WHERE id = ?
                                    """, (app_id,))
                                else:
                                    db_v2.sqlite_service.execute("""
                                        UPDATE partner_applications 
                                        SET status = 'rejected', updated_at = CURRENT_TIMESTAMP
                                        WHERE id = ?
                                    """, (app_id,))
                                
                                self.send_json_response({'success': True, 'message': 'Заявка отклонена'})
                            except Exception as e:
                                self.send_json_response({'success': False, 'error': str(e)}, status=500)
                                
                        elif self.path == '/api/admin/users':
                            # Получаем пользователей
                            try:
                                if db_v2.use_postgresql:
                                    users = db_v2.postgresql_service.fetch_all_sync("""
                                        SELECT telegram_id, first_name, last_name, username, 
                                               points_balance, created_at, last_activity
                                        FROM users 
                                        ORDER BY created_at DESC
                                        LIMIT 100
                                    """)
                                else:
                                    users = db_v2.sqlite_service.fetch_all("""
                                        SELECT telegram_id, first_name, last_name, username, 
                                               points_balance, created_at, last_activity
                                        FROM users 
                                        ORDER BY created_at DESC
                                        LIMIT 100
                                    """)
                                
                                self.send_json_response({
                                    'success': True,
                                    'data': {
                                        'users': [dict(user) for user in users]
                                    }
                                })
                            except Exception as e:
                                self.send_json_response({'success': False, 'error': str(e)}, status=500)
                                
                        elif self.path == '/api/admin/tariff-subscriptions':
                            # Получаем подписки на тарифы
                            try:
                                if db_v2.use_postgresql:
                                    subscriptions = db_v2.postgresql_service.fetch_all_sync("""
                                        SELECT ts.id, ts.partner_id, ts.tariff_id, ts.status, 
                                               ts.subscribed_at, ts.expires_at,
                                               p.company_name, pt.name as tariff_name
                                        FROM tariff_subscriptions ts
                                        LEFT JOIN partners_v2 p ON ts.partner_id = p.user_id
                                        LEFT JOIN partner_tariffs pt ON ts.tariff_id = pt.id
                                        ORDER BY ts.subscribed_at DESC
                                    """)
                                else:
                                    subscriptions = db_v2.sqlite_service.fetch_all("""
                                        SELECT ts.id, ts.partner_id, ts.tariff_id, ts.status, 
                                               ts.subscribed_at, ts.expires_at,
                                               p.company_name, pt.name as tariff_name
                                        FROM tariff_subscriptions ts
                                        LEFT JOIN partners_v2 p ON ts.partner_id = p.user_id
                                        LEFT JOIN partner_tariffs pt ON ts.tariff_id = pt.id
                                        ORDER BY ts.subscribed_at DESC
                                    """)
                                
                                self.send_json_response({
                                    'success': True,
                                    'data': {
                                        'subscriptions': [dict(sub) for sub in subscriptions]
                                    }
                                })
                            except Exception as e:
                                self.send_json_response({'success': False, 'error': str(e)}, status=500)
                                
                        elif self.path.startswith('/api/user/stats'):
                            # Получаем статистику для пользовательского кабинета
                            try:
                                # Получаем user_id из параметров
                                user_id = self.path.split('?')[1].split('=')[1] if '?' in self.path else '0'
                                
                                # Получаем баллы пользователя
                                if db_v2.use_postgresql:
                                    points_result = db_v2.postgresql_service.fetch_all_sync("SELECT points_balance FROM users WHERE telegram_id = ?", (user_id,))
                                else:
                                    points_result = db_v2.sqlite_service.fetch_all("SELECT points_balance FROM users WHERE telegram_id = ?", (user_id,))
                                points_balance = points_result[0]['points_balance'] if points_result else 0
                                
                                # Получаем количество карт пользователя
                                if db_v2.use_postgresql:
                                    cards_count = db_v2.postgresql_service.fetch_all_sync("SELECT COUNT(*) as count FROM cards_binding WHERE user_id = ?", (user_id,))[0]['count']
                                else:
                                    cards_count = db_v2.sqlite_service.fetch_all("SELECT COUNT(*) as count FROM cards_binding WHERE user_id = ?", (user_id,))[0]['count']
                                
                                self.send_json_response({
                                    'success': True,
                                    'data': {
                                        'points_balance': points_balance,
                                        'cards_count': cards_count
                                    }
                                })
                            except Exception as e:
                                self.send_json_response({'success': False, 'error': str(e)}, status=500)
                                
                        elif self.path.startswith('/api/user/policy'):
                            # Проверяем принятие политики пользователем
                            try:
                                # Получаем user_id из параметров
                                user_id = self.path.split('?')[1].split('=')[1] if '?' in self.path else '0'
                                
                                # Используем единый DatabaseAdapter
                                from core.database.db_adapter import db_v2
                                
                                query = "SELECT policy_accepted FROM users WHERE telegram_id = ?"
                                result = db_v2.fetch_one(query, (user_id,))
                                policy_accepted = result[0] if result else False
                                
                                self.send_json_response({
                                    'success': True,
                                    'policy_accepted': bool(policy_accepted)
                                })
                            except Exception as e:
                                self.send_json_response({'success': False, 'error': str(e)}, status=500)
                        
                        elif self.path == '/api/admin/stats':
                            # Статистика для админ кабинета
                            try:
                                from core.database.db_adapter import db_v2
                                
                                # Получаем количество пользователей
                                users_query = "SELECT COUNT(*) FROM user_profiles"
                                if db_v2.use_postgresql:
                                    users_result = db_v2.postgresql_service.fetch_all_sync(users_query)
                                    users_count = users_result[0]['count'] if users_result else 0
                                else:
                                    users_result = db_v2.sqlite_service.fetch_all(users_query)
                                    users_count = users_result[0]['count'] if users_result else 0
                                
                                # Получаем количество партнеров
                                partners_query = "SELECT COUNT(*) FROM partners_v2 WHERE status = 'active'"
                                if db_v2.use_postgresql:
                                    partners_result = db_v2.postgresql_service.fetch_all_sync(partners_query)
                                    partners_count = partners_result[0]['count'] if partners_result else 0
                                else:
                                    partners_result = db_v2.sqlite_service.fetch_all(partners_query)
                                    partners_count = partners_result[0]['count'] if partners_result else 0
                                
                                # Получаем количество заявок на модерацию
                                moderation_query = "SELECT COUNT(*) FROM partner_applications WHERE status = 'pending'"
                                if db_v2.use_postgresql:
                                    moderation_result = db_v2.postgresql_service.fetch_all_sync(moderation_query)
                                    moderation_count = moderation_result[0]['count'] if moderation_result else 0
                                else:
                                    moderation_result = db_v2.sqlite_service.fetch_all(moderation_query)
                                    moderation_count = moderation_result[0]['count'] if moderation_result else 0
                                
                                logger.info(f"[API] Admin stats: users={users_count}, partners={partners_count}, moderation={moderation_count}")
                                
                                self.send_json_response({
                                    'success': True,
                                    'data': {
                                        'users_count': users_count,
                                        'partners_count': partners_count,
                                        'moderation_count': moderation_count
                                    }
                                })
                            except Exception as e:
                                logger.error(f"[API] Error loading admin stats: {e}")
                                self.send_json_response({
                                    'success': True,
                                    'data': {
                                        'users_count': 0,
                                        'partners_count': 0,
                                        'moderation_count': 0
                                    }
                                })
                        
                        elif self.path == '/api/admin/users':
                            # Список пользователей для админ кабинета
                            try:
                                from core.database.db_adapter import db_v2
                                
                                # Получаем список пользователей
                                users_query = """
                                    SELECT user_id, first_name, last_name, username, created_at, last_activity
                                    FROM user_profiles 
                                    ORDER BY created_at DESC 
                                    LIMIT 50
                                """
                                if db_v2.use_postgresql:
                                    users = db_v2.postgresql_service.fetch_all_sync(users_query)
                                else:
                                    users = db_v2.sqlite_service.fetch_all(users_query)
                                
                                users_list = []
                                for user in users:
                                    users_list.append({
                                        'id': user[0],
                                        'first_name': user[1] or 'Не указано',
                                        'last_name': user[2] or '',
                                        'username': user[3] or 'Без username',
                                        'created_at': user[4] or 'Не указано',
                                        'last_activity': user[5] or 'Не указано'
                                    })
                                
                                logger.info(f"[API] Loaded {len(users_list)} users for admin")
                                
                                self.send_json_response({
                                    'success': True,
                                    'data': {
                                        'users': users_list,
                                        'total': len(users_list)
                                    }
                                })
                            except Exception as e:
                                logger.error(f"[API] Error loading users: {e}")
                                self.send_json_response({
                                    'success': False,
                                    'error': str(e)
                                })
                        
                        elif self.path == '/api/moderation/applications':
                            # Заявки на модерацию партнеров
                            try:
                                from core.database.db_adapter import db_v2
                                
                                # Получаем заявки на модерацию
                                applications_query = """
                                    SELECT user_id, name, phone, email, description, status, created_at
                                    FROM partner_applications 
                                    WHERE status = 'pending'
                                    ORDER BY created_at DESC 
                                    LIMIT 20
                                """
                                if db_v2.use_postgresql:
                                    applications = db_v2.postgresql_service.fetch_all_sync(applications_query)
                                else:
                                    applications = db_v2.sqlite_service.fetch_all(applications_query)
                                
                                applications_list = []
                                for app in applications:
                                    applications_list.append({
                                        'user_id': app[0],
                                        'name': app[1] or 'Не указано',
                                        'phone': app[2] or 'Не указан',
                                        'email': app[3] or 'Не указан',
                                        'description': app[4] or 'Нет описания',
                                        'status': app[5] or 'pending',
                                        'created_at': app[6] or 'Не указано'
                                    })
                                
                                logger.info(f"[API] Loaded {len(applications_list)} partner applications for moderation")
                                
                                self.send_json_response({
                                    'success': True,
                                    'data': {
                                        'applications': applications_list,
                                        'total': len(applications_list)
                                    }
                                })
                            except Exception as e:
                                logger.error(f"[API] Error loading moderation applications: {e}")
                                self.send_json_response({
                                    'success': False,
                                    'error': str(e)
                                })
                        
                        elif self.path == '/api/partner/register':
                            # Регистрация партнера через WebApp
                            try:
                                import json
                                import asyncio
                                from tenacity import retry, wait_exponential, stop_after_attempt
                                
                                content_length = int(self.headers.get('Content-Length', 0))
                                post_data = self.rfile.read(content_length)
                                partner_data = json.loads(post_data.decode('utf-8'))
                                
                                logger.info(f"[API] Partner registration data received: {partner_data}")
                                
                                # Используем единый DatabaseAdapter
                                from core.database.db_adapter import db_v2
                                
                                # Получаем реальный user_id из данных или используем временный
                                real_user_id = partner_data.get('user_id', 7006636786)
                                
                                # Если user_id не передан, пытаемся получить из WebApp данных
                                if real_user_id == 7006636786:
                                    # Получаем user_id из заголовков или других источников
                                    # В реальном WebApp это должно приходить из Telegram
                                    real_user_id = 7006636786  # Пока используем тестовый ID
                                
                                # Сохраняем заявку партнера через DatabaseAdapter (синхронно)
                                query = """
                                    INSERT INTO partner_applications 
                                    (user_id, name, phone, email, description, status, created_at)
                                    VALUES ($1, $2, $3, $4, $5, 'pending', NOW())
                                    ON CONFLICT (user_id) DO UPDATE SET
                                    name = EXCLUDED.name,
                                    phone = EXCLUDED.phone,
                                    email = EXCLUDED.email,
                                    description = EXCLUDED.description,
                                    status = 'pending',
                                    updated_at = NOW()
                                """
                                
                                params = (
                                    real_user_id,
                                    partner_data.get('name', ''),
                                    partner_data.get('phone', ''),
                                    partner_data.get('email', ''),
                                    partner_data.get('description', '')
                                )
                                
                                # Проверяем есть ли уже заявка от этого пользователя
                                check_query = "SELECT id FROM partner_applications WHERE user_id = $1"
                                if db_v2.use_postgresql:
                                    existing = db_v2.postgresql_service.fetch_one_sync(check_query, (real_user_id,))
                                else:
                                    existing = db_v2.sqlite_service.fetch_one(check_query, (real_user_id,))
                                
                                if existing:
                                    # Обновляем существующую заявку
                                    update_query = """
                                        UPDATE partner_applications SET
                                        name = $2, phone = $3, email = $4, description = $5,
                                        status = 'pending', updated_at = NOW()
                                        WHERE user_id = $1
                                    """
                                    if db_v2.use_postgresql:
                                        db_v2.postgresql_service.execute_sync(update_query, params)
                                    else:
                                        db_v2.sqlite_service.execute(update_query, params)
                                    logger.info(f"[API] Partner application updated for user {real_user_id}")
                                else:
                                    # Создаем новую заявку
                                    if db_v2.use_postgresql:
                                        db_v2.postgresql_service.execute_sync(query, params)
                                    else:
                                        db_v2.sqlite_service.execute(query, params)
                                    logger.info(f"[API] Partner application saved successfully for user {real_user_id}")
                                
                                # Уведомляем админа о новой заявке (синхронно)
                                try:
                                    from core.settings import settings
                                    import requests
                                    
                                    admin_id = settings.admin_id
                                    bot_token = settings.bot_token
                                    
                                    if admin_id and bot_token:
                                        # Отправляем уведомление через Telegram Bot API напрямую
                                        message_text = (
                                            f"🆕 <b>Новая заявка на регистрацию партнера!</b>\n\n"
                                            f"👤 <b>Пользователь:</b> Пользователь\n"
                                            f"🆔 <b>ID:</b> {real_user_id}\n\n"
                                            f"📝 <b>Данные заявки:</b>\n"
                                            f"• Название: {partner_data.get('name', 'Не указано')}\n"
                                            f"• Телефон: {partner_data.get('phone', 'Не указан')}\n"
                                            f"• Email: {partner_data.get('email', 'Не указан')}\n"
                                            f"• Время: {partner_data.get('timestamp', 'Не указано')}"
                                        )
                                        
                                        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                                        data = {
                                            'chat_id': admin_id,
                                            'text': message_text,
                                            'parse_mode': 'HTML'
                                        }
                                        
                                        response = requests.post(url, data=data, timeout=10)
                                        if response.status_code == 200:
                                            logger.info(f"[API] ✅ Admin {admin_id} notified about partner application from user {real_user_id}")
                                        else:
                                            logger.error(f"[API] Failed to send notification: {response.text}")
                                    else:
                                        logger.warning(f"[API] ⚠️ Admin ID or bot token not configured")
                                        
                                except Exception as notify_error:
                                    logger.error(f"[API] Failed to notify admin: {notify_error}")
                                
                                self.send_json_response({
                                    'success': True,
                                    'message': 'Заявка партнера сохранена'
                                })
                            except Exception as e:
                                logger.error(f"[API] Error saving partner application: {e}")
                                self.send_json_response({'success': False, 'error': str(e)}, status=500)
                            
                        else:
                            self.send_error(404, "API endpoint not found")
                            
                    except Exception as e:
                        logger.error(f"API error: {e}")
                        self.send_json_response({'success': False, 'error': str(e)}, status=500)
                
                def send_json_response(self, data, status=200):
                    self.send_response(status)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                    self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                    self.end_headers()
                    
                    response_json = json.dumps(data, ensure_ascii=False, indent=2)
                    self.wfile.write(response_json.encode('utf-8'))
            
            httpd = HTTPServer(("0.0.0.0", port), CustomHTTPRequestHandler)
            logger.info(f"Web server with API started on port {port}")
            httpd.serve_forever()
        
        web_thread = threading.Thread(target=start_web_server)
        web_thread.daemon = True
        web_thread.start()
        
        # === ИНТЕГРАЦИЯ MULTI-PLATFORM API ===
        if MULTI_PLATFORM_AVAILABLE:
            try:
                # Инициализация multi-platform системы
                enhanced_unified_db.init_databases()
                logger.info("✅ Multi-platform system initialized")
                
                # Запуск мониторинга в фоне
                async def start_monitoring():
                    try:
                        from monitoring.system_monitor import SystemMonitor
                        monitor = SystemMonitor()
                        await monitor.run_monitoring_loop()
                    except Exception as e:
                        logger.error(f"Monitoring failed: {e}")
                
                # Создаем задачу мониторинга, но не ждем её завершения
                try:
                    # Проверяем есть ли активный event loop
                    try:
                        loop = asyncio.get_running_loop()
                        loop.create_task(start_monitoring())
                        logger.info("🔍 Multi-platform monitoring started")
                    except RuntimeError:
                        # Нет активного event loop, создаем новый
                        asyncio.create_task(start_monitoring())
                        logger.info("🔍 Multi-platform monitoring started (new loop)")
                except Exception as e:
                    logger.warning(f"⚠️  Failed to start monitoring: {e}")
                
            except Exception as e:
                logger.error(f"Failed to initialize multi-platform system: {e}")
        
        # Start bot (блокирующий)
        asyncio.run(main())
            
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped")
    except Exception as e:
        logger.exception("Fatal error in main()")
        raise
