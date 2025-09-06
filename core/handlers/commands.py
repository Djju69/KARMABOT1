"""
Command handlers and utilities for the bot
"""
import logging
from aiogram import Bot, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import BotCommand, BotCommandScopeDefault, Message
from core.utils.locales_v2 import get_text
from core.security.roles import Role
from core.security.roles import get_user_role
from aiogram.fsm.context import FSMContext

async def set_commands(bot: Bot) -> None:
    """
    Set up the bot's commands in the Telegram interface
    
    Args:
        bot: The bot instance
    """
    # v4.2.5 commands (exact list, no extras)
    base = [
        ("start", "commands.start"),
        ("add", "commands.add_partner"),  # /add partner — Telegram не поддерживает пробелы
        ("webapp", "commands.webapp"),
        ("city", "commands.city"),
        ("help", "commands.help"),
        ("policy", "commands.policy"),
        ("clear_cache", "commands.clear_cache"),
    ]

    def build(locale: str):
        return [BotCommand(command=cmd, description=get_text(text_key, locale) or cmd) for cmd, text_key in base]

    try:
        # Register per-locale command sets; replaces existing lists for these locales
        for lc in ("ru", "en", "vi", "ko"):
            await bot.set_my_commands(build(lc), scope=BotCommandScopeDefault(), language_code=lc)
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
    async def cmd_start(message: Message, bot: Bot, state: FSMContext):
        """/start — перезапуск и показ главного меню"""
        from .basic import get_start
        try:
            await get_start(message, bot, state)
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error in cmd_start: {e}", exc_info=True)
            await message.reply("Произошла ошибка при обработке команды. Пожалуйста, попробуйте позже.")

    @router.message(Command("help"))
    async def cmd_help(message: Message):
        """/help — Помощь/FAQ (заглушка)"""
        await message.answer("❓ Помощь: раздел FAQ скоро будет обновлён.")
    
    @router.message(Command("webapp"))
    async def cmd_webapp(message: Message):
        await message.answer("🔗 WebApp скоро будет доступен")

    @router.message(Command("city"))
    async def cmd_city(message: Message):
        await message.answer("🌆 Смена города скоро будет доступна")

    @router.message(Command("policy"))
    async def cmd_policy(message: Message):
        await message.answer("📄 Политика конфиденциальности: ссылка будет добавлена позже.")

    @router.message(Command("add"))
    async def cmd_add(message: Message, state: FSMContext):
        """/add partner — Telegram без пробелов, используем /add для запуска мастера"""
        try:
            from .partner import start_add_card
            await start_add_card(message, state)
        except Exception:
            await message.answer("➕ Добавление партнёрской карточки скоро будет доступно.")

    @router.message(Command("clear_cache"))
    async def cmd_clear_cache(message: Message):
        # RBAC: only ADMIN/SUPER_ADMIN
        role = await get_user_role(message.from_user.id)
        if role.name.lower() not in ("admin", "super_admin"):
            await message.answer("⛔ Недостаточно прав")
            return
        # TODO: hook cache service clearing if present
        await message.answer("🧹 Кэш очищен")
    
    return router
