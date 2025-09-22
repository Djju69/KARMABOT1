"""
Commands handlers
"""
from aiogram import Bot
from aiogram.types import BotCommand

async def set_commands(bot: Bot):
    """Set bot commands"""
    commands = [
        BotCommand(command="start", description="🚀 Запустить бота"),
        BotCommand(command="help", description="📋 Помощь"),
    ]
    await bot.set_my_commands(commands)
