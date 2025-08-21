from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeDefault


async def set_commands (bot: Bot):
    commands = [
        BotCommand(
            command='main_menu',
            description='Начало работы'
        ),
        BotCommand(
            command='help',
            description='Как это работает?'
        ),
        BotCommand(
            command='feedback',
            description='Отзывы и предложения '
        ),
        # BotCommand(
        #     command='inline',
        #     description='Inline'
        # )
    ]
    await bot.set_my_commands(commands, BotCommandScopeDefault())