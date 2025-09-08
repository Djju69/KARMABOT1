"""
Command handlers and utilities for the bot
"""
import logging
from aiogram import Bot, Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import BotCommand, BotCommandScopeDefault, Message, CallbackQuery
from core.utils.locales_v2 import get_text
from core.security.roles import Role
from core.security.roles import get_user_role
from core.services.cache import cache_service
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
        """Показать выбор города"""
        from ..keyboards.inline_v2 import get_cities_inline
        await message.answer(
            "🌆 <b>Выберите город:</b>\n\n"
            "Выберите город для просмотра доступных заведений и предложений.",
            reply_markup=get_cities_inline(),
            parse_mode="HTML"
        )

    @router.message(Command("policy"))
    async def cmd_policy(message: Message):
        await message.answer("📄 Политика конфиденциальности: ссылка будет добавлена позже.")

    @router.message(Command("add"))
    async def cmd_add(message: Message, state: FSMContext):
        """/add - команда для добавления партнеров и карточек товаров"""
        try:
            # Проверяем, не является ли пользователь уже партнером
            from core.database.db_v2 import get_connection
            
            with get_connection() as conn:
                cursor = conn.execute(
                    "SELECT id, status FROM partners WHERE contact_telegram = ?",
                    (message.from_user.id,)
                )
                existing_partner = cursor.fetchone()
            
            if existing_partner:
                status_text = {
                    'pending': '⏳ Ожидает рассмотрения',
                    'approved': '✅ Одобрен',
                    'rejected': '❌ Отклонен',
                    'suspended': '⏸️ Приостановлен'
                }.get(existing_partner[1], '❓ Неизвестный статус')
                
                await message.answer(
                    f"🤝 <b>Статус партнерства</b>\n\n"
                    f"📋 Ваша заявка на партнерство уже подана.\n"
                    f"📊 Статус: {status_text}\n\n"
                    f"💡 Если у вас есть вопросы, обратитесь в поддержку.",
                    parse_mode='HTML'
                )
                return
            
            # Начинаем процесс регистрации партнера
            from core.fsm.partner_registration import start_partner_registration
            await start_partner_registration(message, state)
            
        except Exception as e:
            logger.error(f"Error in cmd_add: {e}")
            await message.answer("❌ Ошибка при запуске регистрации партнера. Попробуйте позже.")

    @router.message(Command("clear_cache"))
    async def cmd_clear_cache(message: Message):
        # RBAC: only ADMIN/SUPER_ADMIN
        role = await get_user_role(message.from_user.id)
        role_name = getattr(role, "name", str(role)).lower()
        if role_name not in ("admin", "super_admin"):
            await message.answer("⛔ Недостаточно прав")
            return
        # Очистка типовых ключей кэша (безопасно и точечно)
        try:
            uid = message.from_user.id
            # RBAC роль
            await cache_service.delete(f"rbac:role:{uid}")
            # Карта привязки
            await cache_service.delete(f"card_bind_wait:{uid}")
            # Лояльность: баланс и история
            await cache_service.delete(f"loyalty:balance:{uid}")
            for limit in (5, 10, 20, 50, 100):
                await cache_service.delete(f"loyalty:tx_history:{uid}:{limit}")
            # Нотификации
            await cache_service.delete(f"notify:{uid}:on")
            await cache_service.delete(f"notify:{uid}:off")
            # Попытка вызвать массовую очистку по маске, если реализована
            try:
                await getattr(cache_service, "delete_by_mask")("*")  # type: ignore[attr-defined]
            except Exception:
                pass
            await message.answer("🧹 Кэш очищен! Удалены ключи кэша для пользователя и системы")
        except Exception as e:
            logging.getLogger(__name__).error(f"clear_cache failed: {e}")
            await message.answer("⚠️ Ошибка при очистке кэша")

    @router.callback_query(F.data.startswith("city:set:"))
    async def handle_city_selection(callback: CallbackQuery, state: FSMContext):
        """Обработчик выбора города"""
        try:
            await callback.answer()
            
            # Извлекаем ID города из callback_data
            city_id = int(callback.data.split(":")[-1])
            
            # Маппинг ID городов на названия
            cities = {
                1: "Нячанг",
                2: "Дананг", 
                3: "Хошимин",
                4: "Фукуок"
            }
            
            city_name = cities.get(city_id, "Неизвестный город")
            
            # Сохраняем выбранный город в состояние пользователя
            await state.update_data(selected_city_id=city_id, selected_city_name=city_name)
            
            # Обновляем сообщение
            await callback.message.edit_text(
                f"✅ <b>Город выбран: {city_name}</b>\n\n"
                f"Теперь вы можете просматривать заведения и предложения в городе {city_name}.\n\n"
                f"Используйте команду /city для смены города.",
                parse_mode="HTML"
            )
            
        except Exception as e:
            logging.getLogger(__name__).error(f"city selection failed: {e}")
            await callback.answer("❌ Ошибка при выборе города")
    
    return router
