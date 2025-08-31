#!/usr/bin/env python3
import os
import asyncio
import logging
import uvicorn
from web.main import app

# Базовая настройка логирования
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

async def run_bot():
    """Запуск телеграм бота"""
    try:
        # ПРЯМОЙ ИМПОРТ БОТА - ОСНОВНОЙ ПУТЬ
        from bot.bot import bot
        logger.info("✅ Бот импортирован, запускаем...")
        await bot.start()
        
    except ImportError as e:
        logger.error(f"❌ Ошибка импорта бота (основной путь): {e}")
        
        # АЛЬТЕРНАТИВНЫЙ ПУТЬ 1
        try:
            from bot import bot
            logger.info("✅ Бот импортирован (альтернативный путь 1)")
            await bot.start()
            
        except ImportError:
            # АЛЬТЕРНАТИВНЫЙ ПУТЬ 2 - ПРЯМОЙ ДОСТУП
            try:
                import sys
                sys.path.append('/app')
                from bot.bot import bot
                logger.info("✅ Бот импортирован (прямой доступ)")
                await bot.start()
                
            except ImportError as e2:
                logger.error(f"❌ Все попытки импорта провалились: {e2}")
                raise

async def run_web_server():
    """Запуск веб-сервера"""
    port = int(os.getenv("PORT", 8080))
    config = uvicorn.Config(app, host="0.0.0.0", port=port)
    server = uvicorn.Server(config)
    logger.info(f"✅ Запускаем веб-сервер на порту {port}...")
    await server.serve()

async def main():
    """Одновременный запуск бота и веб-сервера"""
    # Создаем задачи для параллельного выполнения
    bot_task = asyncio.create_task(run_bot())
    web_task = asyncio.create_task(run_web_server())
    
    # Ожидаем завершения всех задач
    await asyncio.gather(bot_task, web_task)

if __name__ == "__main__":
    logger.info("🚀 Запускаем и бота, и веб-сервер одновременно!")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Приложение остановлено пользователем")
    except Exception as e:
        logger.critical(f"Критическая ошибка: {e}", exc_info=True)
        sys.exit(1)
