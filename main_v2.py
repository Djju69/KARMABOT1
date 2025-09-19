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

from core.settings import Settings, get_settings, Features
from core.database.migrations import ensure_database_ready

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
        main_menu_router,
    )
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
    # 8) Ping/catch-alls LAST
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
        # Start simple web server in background thread
        import threading
        from http.server import HTTPServer, SimpleHTTPRequestHandler
        import os
        
        def start_web_server():
            port = int(os.getenv("PORT", 8080))
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
                        import json
                        import sys
                        import os
                        
                        # Добавляем путь к корню проекта
                        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                        
                        from core.database.db_adapter import db_v2
                        
                        if self.path == '/api/moderation/applications':
                            # Получаем заявки партнеров
                            applications = db_v2.execute_query("""
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
                            db_v2.execute_query("""
                                UPDATE partner_applications 
                                SET status = 'approved', updated_at = CURRENT_TIMESTAMP
                                WHERE id = ?
                            """, (app_id,))
                            
                            self.send_json_response({'success': True, 'message': 'Заявка одобрена'})
                            
                        elif self.path.startswith('/api/moderation/reject/'):
                            app_id = self.path.split('/')[-1]
                            db_v2.execute_query("""
                                UPDATE partner_applications 
                                SET status = 'rejected', updated_at = CURRENT_TIMESTAMP
                                WHERE id = ?
                            """, (app_id,))
                            
                            self.send_json_response({'success': True, 'message': 'Заявка отклонена'})
                            
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
        
        # Start bot
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped")
    except Exception as e:
        logger.exception("Fatal error in main()")
        raise
