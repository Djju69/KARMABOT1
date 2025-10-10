"""
Bot и Dispatcher instances
ВАЖНО: Сохраняет всю логику из main_v2.py
"""
import logging
import os
from typing import Optional
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

logger = logging.getLogger(__name__)

_bot: Optional[Bot] = None
_dispatcher: Optional[Dispatcher] = None

def create_bot() -> Bot:
    """
    Создать Bot instance
    
    На основе main_v2.py строки 419-422:
    async with Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    ) as bot:
    """
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise ValueError("❌ BOT_TOKEN required!")
    
    logger.info("🤖 Creating Bot...")
    
    # Точно как в main_v2.py
    bot = Bot(
        token=token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    logger.info(f"✅ Bot created: {token[:10]}...")
    return bot

def create_dispatcher() -> Dispatcher:
    """
    Создать Dispatcher instance
    
    На основе main_v2.py строки 335, 573, 601:
    dp = Dispatcher()
    
    В main_v2.py НЕТ указания storage, используем MemoryStorage по умолчанию
    """
    logger.info("📡 Creating Dispatcher...")
    
    # В main_v2.py нет указания storage, используем MemoryStorage
    storage = MemoryStorage()
    
    dp = Dispatcher(storage=storage)
    
    logger.info("✅ Dispatcher created")
    return dp

def get_bot() -> Bot:
    global _bot
    if _bot is None:
        _bot = create_bot()
    return _bot

def get_dispatcher() -> Dispatcher:
    global _dispatcher
    if _dispatcher is None:
        _dispatcher = create_dispatcher()
    return _dispatcher

async def shutdown():
    """Очистка ресурсов"""
    global _bot, _dispatcher
    
    if _bot:
        await _bot.session.close()
        _bot = None
    
    if _dispatcher:
        await _dispatcher.storage.close()
        _dispatcher = None
    
    logger.info("🧹 Cleanup complete")
