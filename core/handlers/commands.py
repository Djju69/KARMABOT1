"""
Command handlers and utilities for the bot
"""
from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeDefault

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
    from aiogram import F
    from aiogram.filters import Command
    from aiogram.types import Message
    
    @router.message(Command("start", "help"))
    async def cmd_start(message: Message):
        """Обработчик команд /start и /help"""
        from .basic import start_cmd
        from ..compat import call_compat
        
        # Получаем бота из контекста
        from aiogram import Bot
        from aiogram.fsm.context import FSMContext
        
        bot = Bot.get_current()
        state = FSMContext(
            storage=router.fsm.storage,
            key=router.fsm.storage_key,
            user=message.from_user.id,
            chat=message.chat.id
        )
        
        await call_compat(start_cmd, message, bot, state)
    
    @router.message(Command("profile"))
    async def cmd_profile(message: Message):
        """Обработчик команды /profile"""
        from .basic import show_profile
        from ..compat import call_compat
        
        bot = Bot.get_current()
        state = FSMContext(
            storage=router.fsm.storage,
            key=router.fsm.storage_key,
            user=message.from_user.id,
            chat=message.chat.id
        )
        
        await call_compat(show_profile, message, bot, state)
    
    return router
