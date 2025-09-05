#!/usr/bin/env python3
import os
import sys
import asyncio
import logging
import uvicorn
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = str(Path(__file__).parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.handlers.RotatingFileHandler(
            'app.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
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
    return railway_env is not None

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
        app_url = f"https://{os.getenv('RAILWAY_STATIC_URL', 'your-app.railway.app')}"
        logger.info(f"🌐 Railway detected, using webhook: {app_url}")
        os.environ['WEBHOOK_URL'] = app_url
        os.environ['DISABLE_POLLING'] = 'true'
        logger.info("✅ Webhook mode enabled")
    else:
        logger.info("💻 Local environment, using polling")
        logger.info("✅ Polling mode enabled")

# Try to import web app with delay to avoid circular imports
try:
    import time
    time.sleep(1)  # Даем время для завершения инициализации
    from web.main import app
    WEB_IMPORTED = True
except ImportError as e:
    logger.warning(f"Failed to import web app: {e}")
    WEB_IMPORTED = False

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
            except Exception as e:
                logger.error(f"❌ Failed to clear webhook: {e}")
                logger.error("💡 Webhook cleanup failed, bot may have conflicts")
        else:
            logger.error("❌ BOT_TOKEN not found in environment variables!")
            logger.error("💡 Please set BOT_TOKEN in Railway Dashboard -> Variables")

        # Try to import bot from the new structure
        logger.info("📦 Importing bot module...")
        from bot.bot import start as start_bot
        logger.info("✅ Bot module imported successfully")

        logger.info("🚀 Starting bot...")
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
    if not WEB_IMPORTED:
        logger.warning("Веб-приложение не импортировано, пропускаем запуск веб-сервера")
        return
        
    port = int(os.getenv("PORT", 8080))
    config = uvicorn.Config(
        app,
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
    tasks = []
    
    # Add bot task if BOT_TOKEN is set
    bot_token = os.getenv("BOT_TOKEN")
    logger.info(f"🔍 Checking BOT_TOKEN in main(): present={bool(bot_token)}")
    if bot_token:
        logger.info("🤖 BOT_TOKEN found, adding bot task...")
        logger.info(f"🔑 BOT_TOKEN length: {len(bot_token)}")
        tasks.append(asyncio.create_task(run_bot()))
    else:
        logger.error("❌ BOT_TOKEN not found in environment!")
        logger.error("💡 Please check Railway Variables for BOT_TOKEN")
    
    # Add web server task if web app is available
    if WEB_IMPORTED:
        tasks.append(asyncio.create_task(run_web_server()))
    
    if not tasks:
        logger.error("Нет доступных сервисов для запуска")
        return
    
    # Wait for all tasks to complete
    await asyncio.gather(*tasks, return_exceptions=True)

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
