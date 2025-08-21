from __future__ import annotations

from aiogram import Bot
from aiogram.types import BotCommand

# Minimal command setup compatible with aiogram v3
# Registers basic commands for multiple languages used by the bot

COMMANDS_I18N = {
    "en": [
        ("start", "Start the bot"),
        ("help", "Show help"),
        ("menu", "Open main menu"),
        ("language", "Choose language"),
    ],
    "ru": [
        ("start", "Запустить бота"),
        ("help", "Помощь"),
        ("menu", "Главное меню"),
        ("language", "Выбрать язык"),
    ],
    "vi": [
        ("start", "Bắt đầu bot"),
        ("help", "Trợ giúp"),
        ("menu", "Mở menu chính"),
        ("language", "Chọn ngôn ngữ"),
    ],
    "ko": [
        ("start", "봇 시작"),
        ("help", "도움말"),
        ("menu", "메인 메뉴 열기"),
        ("language", "언어 선택"),
    ],
}

async def set_commands(bot: Bot) -> None:
    # Default (no language_code): let Telegram pick client language
    default_cmds = [BotCommand(command=c, description=d) for c, d in COMMANDS_I18N["en"]]
    await bot.set_my_commands(default_cmds)

    # Per-language commands
    for lang, pairs in COMMANDS_I18N.items():
        cmds = [BotCommand(command=c, description=d) for c, d in pairs]
        await bot.set_my_commands(cmds, language_code=lang)

__all__ = ["set_commands"]
