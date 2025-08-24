from __future__ import annotations

from aiogram import Bot
from aiogram.types import BotCommand

# WARNING: TABOO — DO NOT CHANGE BOT COMMANDS WITHOUT OWNER'S EXPLICIT APPROVAL.
# Strictly limited set of commands. No extras, no duplicates.

COMMANDS_I18N = {
    "en": [
        ("start", "Restart"),
        ("add_partner", "Add partner"),
        ("webapp", "Open WebApp"),
        ("city", "Change city"),
        ("help", "Help/FAQ"),
        ("policy", "Privacy policy"),
        ("clear_cache", "Clear cache (admin)"),
    ],
    "ru": [
        ("start", "Перезапуск"),
        ("add_partner", "Добавить партнёра"),
        ("webapp", "Открыть WebApp"),
        ("city", "Сменить город"),
        ("help", "Помощь/FAQ"),
        ("policy", "Показать политику конфиденциальности"),
        ("clear_cache", "Очистить кэш (админ)"),
    ],
    "vi": [
        ("start", "Khởi động lại"),
        ("add_partner", "Thêm đối tác"),
        ("webapp", "Mở WebApp"),
        ("city", "Đổi thành phố"),
        ("help", "Trợ giúp / FAQ"),
        ("policy", "Chính sách bảo mật"),
        ("clear_cache", "Xóa bộ nhớ đệm (admin)"),
    ],
    "ko": [
        ("start", "재시작"),
        ("add_partner", "파트너 추가"),
        ("webapp", "WebApp 열기"),
        ("city", "도시 변경"),
        ("help", "도움말 / FAQ"),
        ("policy", "개인정보 처리방침"),
        ("clear_cache", "캐시 삭제 (관리자)"),
    ],
}

async def set_commands(bot: Bot) -> None:
    # Overwrite default (no language_code)
    default_cmds = [BotCommand(command=c, description=d) for c, d in COMMANDS_I18N["en"]]
    await bot.set_my_commands(default_cmds)

    # Overwrite per-language commands (clears extras in Telegram client menus)
    for lang, pairs in COMMANDS_I18N.items():
        cmds = [BotCommand(command=c, description=d) for c, d in pairs]
        await bot.set_my_commands(cmds, language_code=lang)

__all__ = ["set_commands"]
