from __future__ import annotations

from aiogram import Bot
from aiogram.types import BotCommand

# Minimal command setup compatible with aiogram v3
# Registers basic commands for multiple languages used by the bot

COMMANDS_I18N = {
    "en": [
        ("start", "Restart"),
        ("help", "Help / FAQ"),
        ("faq", "FAQ page"),
        ("menu", "Open main menu"),
        ("profile", "Profile"),
        ("webapp", "Open WebApp"),
        ("add_partner", "Add partner"),
        ("city", "Change city"),
        ("policy", "Privacy policy"),
        ("clear_cache", "Clear cache (admin)"),
    ],
    "ru": [
        ("start", "Перезапуск"),
        ("help", "Помощь/FAQ"),
        ("faq", "FAQ"),
        ("menu", "Главное меню"),
        ("profile", "Личный кабинет"),
        ("webapp", "Открыть WebApp"),
        ("add_partner", "Добавить партнёра"),
        ("city", "Сменить город"),
        ("policy", "Показать политику конфиденциальности"),
        ("clear_cache", "Очистить кэш (админ)"),
    ],
    "vi": [
        ("start", "Khởi động lại"),
        ("help", "Trợ giúp / FAQ"),
        ("faq", "FAQ"),
        ("menu", "Mở menu chính"),
        ("profile", "Hồ sơ"),
        ("webapp", "Mở WebApp"),
        ("add_partner", "Thêm đối tác"),
        ("city", "Đổi thành phố"),
        ("policy", "Chính sách bảo mật"),
        ("clear_cache", "Xóa bộ nhớ đệm (admin)"),
    ],
    "ko": [
        ("start", "재시작"),
        ("help", "도움말 / FAQ"),
        ("faq", "FAQ"),
        ("menu", "메인 메뉴"),
        ("profile", "프로필"),
        ("webapp", "WebApp 열기"),
        ("add_partner", "파트너 추가"),
        ("city", "도시 변경"),
        ("policy", "개인정보 처리방침"),
        ("clear_cache", "캐시 삭제 (관리자)"),
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
