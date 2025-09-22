"""
Commands handlers
"""
from aiogram import Router, Bot
from aiogram.types import BotCommand

router = Router()

async def set_commands(bot: Bot):
    """Set bot commands"""
    commands = [
        BotCommand(command="start", description="🚀 Запустить бота"),
        BotCommand(command="help", description="📋 Помощь"),
    ]
    await bot.set_my_commands(commands)
