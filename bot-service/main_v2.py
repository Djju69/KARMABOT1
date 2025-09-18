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

async def main():
    """Main entry point"""
    token = resolve_bot_token(settings)
    logger.info("🔑 Environment: %s", settings.environment)
    logger.info("🔑 Using bot token: %s", _mask(token))

    bot = Bot(token=token)
    dp = Dispatcher()

    # Include all routers
    from core.handlers import (
        basic_router, 
        callback_router, 
        main_menu_router, 
        language_router,
        partner_router
    )
    
    # AI Support routers
    from core.handlers.help_with_ai import router as help_with_ai_router
    from core.handlers.ai_help import ai_help_router
    from core.handlers.settings_router import router as settings_router
    from core.handlers.support_ai import router as support_ai_router
    from core.handlers.commands import router as commands_router
    
    # AI Support routers (with feature flags) — ПОДКЛЮЧАЕМ ПЕРВЫМИ для приоритета /help и «❓ Помощь»
    from core.settings import settings
    logger.info(f"🔍 Support AI feature flag: {settings.features.support_ai}")
    if settings.features.support_ai:
        try:
            dp.include_router(help_with_ai_router)  # перехват /help и '❓ Помощь'
            dp.include_router(ai_help_router)
            dp.include_router(settings_router)
            dp.include_router(support_ai_router)
            logger.info("✅ AI Support routers included (before main routers)")
        except Exception as e:
            logger.error(f"❌ Error including AI routers: {e}")
    else:
        logger.warning("⚠️ AI Support feature is disabled")

    # Основные роутеры — после AI, чтобы не перехватывать /help раньше
    dp.include_router(commands_router)
    dp.include_router(basic_router)
    dp.include_router(callback_router)
    
    # ИИ помощник для админов
    try:
        from core.handlers.ai_assistant_router import router as ai_assistant_router
        dp.include_router(ai_assistant_router)
        logger.info("✅ AI Assistant router included")
    except Exception as e:
        logger.warning(f"AI Assistant router not included: {e}")
    
    # Живые дашборды для админов
    try:
        from core.handlers.live_dashboard_router import router as live_dashboard_router
        dp.include_router(live_dashboard_router)
        logger.info("✅ Live Dashboard router included")
    except Exception as e:
        logger.warning(f"Live Dashboard router not included: {e}")
    # QR handlers (explicit router for /qr_codes and qr_* callbacks)
    try:
        from core.handlers.qr_code_handlers import router as qr_code_router
        dp.include_router(qr_code_router)
    except Exception as e:
        logger.warning("QR router not included: %s", e)
    # Referral handlers
    try:
        from core.handlers.referral_handlers import router as referral_router
        dp.include_router(referral_router)
    except Exception as e:
        logger.warning("Referral router not included: %s", e)
    dp.include_router(main_menu_router)
    dp.include_router(language_router)
    
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

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped")
    except Exception as e:
        logger.exception("Fatal error in main()")
        raise
