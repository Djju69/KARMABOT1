#!/usr/bin/env python3
print("="*60)
print("🚨 START.PY — simplified startup logs")
print("⏰ TIME:", __import__('datetime').datetime.now())
print("="*60)

import os
import sys
import asyncio
import logging
import uvicorn
from pathlib import Path
from datetime import datetime

print("✅ IMPORTS LOADED SUCCESSFULLY")

# ENV теперь читаем только из окружения (без форса)
print("🔧 ENV DETECTED:")
print(f"  RAILWAY_ENVIRONMENT: {os.getenv('RAILWAY_ENVIRONMENT')}")
print(f"  DISABLE_POLLING: {os.getenv('DISABLE_POLLING')}")
print(f"  RAILWAY_STATIC_URL: {os.getenv('RAILWAY_STATIC_URL')}")
print("="*60)

# Add project root to path
project_root = str(Path(__file__).parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Configure logging with UTF-8 encoding
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.handlers.RotatingFileHandler(
            'app.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
    ]
)
logger = logging.getLogger(__name__)

def is_railway_environment():
    """Проверка запуска на Railway"""
    railway_env = os.getenv('RAILWAY_ENVIRONMENT')
    railway_url = os.getenv('RAILWAY_STATIC_URL')
    logger.info(f"🔍 RAILWAY_ENVIRONMENT: '{railway_env}'")
    logger.info(f"🔍 RAILWAY_STATIC_URL: '{railway_url}'")

    return bool(railway_env)

def validate_environment():
    """Проверка обязательных переменных окружения"""
    required_vars = ['BOT_TOKEN', 'REDIS_URL', 'DATABASE_URL']
    missing_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        else:
            # Логируем что переменная есть (без значения)
            logger.info(f"✅ {var}: {'*' * min(len(value), 10)}...")
    
    if missing_vars:
        logger.error(f"❌ Отсутствуют обязательные переменные: {', '.join(missing_vars)}")
        logger.error("Добавьте их в Railway Dashboard -> Variables")
        sys.exit(1)
    
    logger.info("✅ Все переменные окружения настроены")
    
    # Настройка для Railway
    if is_railway_environment():
        raw_url = os.getenv('RAILWAY_STATIC_URL')
        if raw_url:
            app_url = raw_url if raw_url.startswith(('http://', 'https://')) else f"https://{raw_url}"
            webhook_url = f"{app_url}/webhook"
            logger.info(f"🌐 Railway detected, webhook URL: {webhook_url}")
            os.environ['WEBHOOK_URL'] = webhook_url
        else:
            logger.warning("RAILWAY_STATIC_URL is not set; webhook URL cannot be constructed")
    else:
        logger.info("💻 Local environment: polling mode")

# Try to import web app with delay to avoid circular imports
APP = None
try:
    import time
    time.sleep(1)  # Даем время для завершения инициализации
    from web.main import app as web_app
    APP = web_app
    WEB_IMPORTED = True
except Exception as e:
    logger.warning(f"Failed to import web app: {e}")
    WEB_IMPORTED = False
    # Fallback to minimal health app to satisfy Railway healthcheck
    try:
        from health_app import app as health_app
        APP = health_app
        logger.info("Using fallback health_app for healthcheck")
    except Exception as ee:
        logger.warning(f"Fallback health_app unavailable: {ee}")

async def run_bot():
    """Запуск телеграм бота"""
    logger.info("🤖 === BOT STARTUP BEGIN ===")
    logger.info("🤖 Starting bot initialization...")
    try:
        # Clear webhook before starting bot to avoid conflicts
        logger.info("🧹 Clearing webhook to avoid conflicts...")
        bot_token = os.getenv('BOT_TOKEN')
        logger.info(f"🔍 BOT_TOKEN present: {bool(bot_token)}")

        if bot_token:
            logger.info(f"🔑 Bot token length: {len(bot_token)}")
            # Try curl method first (more reliable)
            try:
                import subprocess
                logger.info("🌐 Trying curl method for webhook cleanup...")
                result = subprocess.run([
                    'curl', '-s', '-X', 'POST',
                    f'https://api.telegram.org/bot{bot_token}/deleteWebhook?drop_pending_updates=true'
                ], capture_output=True, text=True, timeout=10)

                if result.returncode == 0 and '"ok":true' in result.stdout:
                    logger.info("✅ Webhook cleared successfully via curl")
                else:
                    logger.warning(f"⚠️ Curl method failed: {result.stdout}")
                    # Fallback to aiogram method
                    logger.info("🤖 Trying aiogram method...")
                    from aiogram import Bot
                    bot = Bot(token=bot_token)
                    await bot.delete_webhook(drop_pending_updates=True)
                    await bot.session.close()
                    logger.info("✅ Webhook cleared successfully via aiogram")

                # Avoid logOut/close to prevent 'Logged out' state from Telegram
            except Exception as e:
                logger.error(f"❌ Failed to clear webhook: {e}")
                logger.error("💡 Webhook cleanup failed, bot may have conflicts")
        else:
            logger.error("❌ BOT_TOKEN not found in environment variables!")
            logger.error("💡 Please set BOT_TOKEN in Railway Dashboard -> Variables")

        # Запускаем бота через main_v2 (polling-режим, как в рабочей конфигурации)
        logger.info("📦 Importing main_v2 (legacy stable entrypoint)...")
        from main_v2 import main as start_bot
        logger.info("✅ main_v2 imported successfully")

        # Запускаем бота (режим определяется в main_v2.py)
        logger.info("🚀 Starting bot via main_v2.main()...")
        await start_bot()

    except ImportError as e:
        logger.error(f"❌ Bot import error: {e}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"❌ Bot startup error: {e}", exc_info=True)
        # Не останавливаем приложение, продолжаем с веб-сервером
        logger.warning("⚠️ Bot failed to start, continuing with web server")

async def run_web_server():
    """Запуск веб-сервера"""
    if APP is None:
        logger.warning("Нет доступного ASGI-приложения для веб-сервера (web/health). Пропуск запуска")
        return
        
    port = int(os.getenv("PORT", 8080))
    config = uvicorn.Config(
        APP,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
    server = uvicorn.Server(config)
    logger.info(f"✅ Запускаем веб-сервер на порту {port}...")
    await server.serve()

async def main():
    """Одновременный запуск бота и веб-сервера"""
    logger.info("🚀 Starting main application...")
    print("🚨 DEBUG: Code updated at", datetime.now())  # Debug print
    validate_environment()  # Проверяем переменные окружения
    logger.info("✅ Environment validation passed")

    # ПРОВЕРКА РЕЖИМА ЗАПУСКА
    is_railway = is_railway_environment()
    logger.info(f"🎯 Deployment mode: {'RAILWAY' if is_railway else 'LOCAL'}")

    # Railway: health server + polling (single mode, no contradictions in logs)
    if is_railway:
        bot_token = os.getenv("BOT_TOKEN")
        if not bot_token:
            logger.error("❌ BOT_TOKEN not found for Railway polling!")
            logger.error("💡 Please check Railway Variables for BOT_TOKEN")
            return

        # Запускаем веб-сервер (web.main или health_app) и бота параллельно
        # ВАЖНО: сначала поднимем веб, затем с задержкой бота, чтобы избежать гонок
        web_task = asyncio.create_task(run_web_server())
        await asyncio.sleep(2)
        bot_task = asyncio.create_task(run_bot())
        await asyncio.gather(web_task, bot_task)

    # Local: polling only
    else:
        logger.info("💻 LOCAL MODE: Starting polling only")
        bot_token = os.getenv("BOT_TOKEN")
        if bot_token:
            logger.info("🤖 BOT_TOKEN found, starting polling...")
            await run_bot()
        else:
            logger.error("❌ BOT_TOKEN not found for local polling!")
            logger.error("💡 Set BOT_TOKEN environment variable")
            return

if __name__ == "__main__":
    logger.info("🚀 Запускаем сервисы...")
    
    # Print environment info
    logger.info(f"Python: {sys.version}")
    logger.info(f"Current directory: {os.getcwd()}")
    logger.info(f"Files in directory: {os.listdir('.')}")
    
    if os.path.exists('bot'):
        logger.info("Bot directory exists")
        logger.info(f"Files in bot directory: {os.listdir('bot')}")
    else:
        logger.error("Bot directory does not exist!")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Приложение остановлено пользователем")
    except Exception as e:
        logger.critical(f"Критическая ошибка: {e}", exc_info=True)
        sys.exit(1)

