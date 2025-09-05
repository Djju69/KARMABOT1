#!/usr/bin/env python3
import os
import sys
import asyncio
import logging
import uvicorn
from pathlib import Path

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
    return os.getenv('RAILWAY_ENVIRONMENT') is not None

def validate_environment():
    """Проверка обязательных переменных окружения"""
    required_vars = ['BOT_TOKEN', 'REDIS_URL']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
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
    else:
        logger.info("💻 Local environment, using polling")

# Try to import web app
try:
    from web.main import app
    WEB_IMPORTED = True
except ImportError as e:
    logger.warning(f"Failed to import web app: {e}")
    WEB_IMPORTED = False

async def run_bot():
    """Запуск телеграм бота"""
    try:
        # Try to import bot from the new structure
        from bot.bot import start as start_bot
        logger.info("✅ Бот импортирован, запускаем...")
        await start_bot()
        
    except ImportError as e:
        logger.error(f"❌ Ошибка импорта бота: {e}", exc_info=True)
        raise

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
    validate_environment()  # Проверяем переменные окружения
    tasks = []
    
    # Add bot task if BOT_TOKEN is set
    if os.getenv("BOT_TOKEN"):
        tasks.append(asyncio.create_task(run_bot()))
    else:
        logger.warning("BOT_TOKEN не установлен, пропускаем запуск бота")
    
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
