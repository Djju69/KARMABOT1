"""
Main bot module for KarmaBot.
This module initializes the bot instance and sets up the dispatcher.
"""
import os
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

logger = logging.getLogger(__name__)

# Initialize bot with default properties
bot = Bot(
    token=os.getenv("BOT_TOKEN"),
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

dp = Dispatcher()

# Import handlers to register them
from core.handlers import (
    basic, commands, callback, contact, lang, main_menu_router,
    profile, partner, activity, admin_cabinet, category_handlers
)

# Setup routers
dp.include_router(basic.router)
dp.include_router(commands.router)
dp.include_router(callback.router)
dp.include_router(contact.router)
dp.include_router(lang.router)
dp.include_router(main_menu_router.router)
dp.include_router(profile.router)
dp.include_router(partner.router)
dp.include_router(activity.router)
dp.include_router(admin_cabinet.router)
dp.include_router(category_handlers.router)

# This will be called from start.py
async def start():
    """Start the bot"""
    logger.info("Starting bot...")
    await dp.start_polling(bot, skip_updates=True)
