"""
Command handlers and utilities for the bot
"""
import logging
from aiogram import Bot, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import BotCommand, BotCommandScopeDefault, Message
from aiogram.fsm.context import FSMContext

async def set_commands(bot: Bot) -> None:
    """
    Set up the bot's commands in the Telegram interface
    
    Args:
        bot: The bot instance
    """
    commands = [
        BotCommand(command="start", description="Главное меню"),
        BotCommand(command="help", description="Помощь"),
        BotCommand(command="profile", description="Мой профиль"),
        BotCommand(command="menu", description="Открыть меню"),
    ]
    
    try:
        await bot.set_my_commands(commands, scope=BotCommandScopeDefault())
    except Exception as e:
        print(f"Error setting bot commands: {e}")
        raise

# Алиасы для обратной совместимости
def register_commands(router):
    """
    Регистрация обработчиков команд
    
    Args:
        router: Роутер для регистрации обработчиков
    """
    from aiogram.filters import Command, CommandStart
    from aiogram.types import Message
    
    @router.message(CommandStart())
    @router.message(Command("help"))
    async def cmd_start(message: Message, bot: Bot, state: FSMContext):
        """Обработчик команд /start и /help"""
        from .basic import get_start
        
        try:
            await get_start(message, bot, state)
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error in cmd_start: {e}", exc_info=True)
            await message.reply("Произошла ошибка при обработке команды. Пожалуйста, попробуйте позже.")
    
    @router.message(Command("profile"))
    async def cmd_profile(message: Message, bot: Bot, state: FSMContext):
        """Обработчик команды /profile"""
        from .basic import open_cabinet
        
        try:
            await open_cabinet(message, bot, state)
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error in cmd_profile: {e}", exc_info=True)
            await message.reply("Произошла ошибка при открытии профиля. Пожалуйста, попробуйте позже.")
    
    return router
