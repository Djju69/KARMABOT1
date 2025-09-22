"""
Basic handlers for KARMABOT1
"""
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()

@router.message(Command("start"))
async def start_handler(message: Message):
    """Start command handler"""
    await message.answer("🚀 Добро пожаловать в KARMABOT1!")

@router.message(Command("help"))
async def help_handler(message: Message):
    """Help command handler"""
    await message.answer("📋 Помощь по командам бота")
