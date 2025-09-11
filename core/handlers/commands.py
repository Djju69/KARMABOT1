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

logger = logging.getLogger(__name__)
router = Router()

async def set_commands(bot: Bot) -> None:
    """
    Set up the bot's commands in the Telegram interface
    
    Args:
        bot: The bot instance
    """
    # v4.2.5 commands (exact list, no extras)
    base = [
        ("start", "commands.start"),
        ("add_card", "commands.add_card"),
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
        """/help — Справка с кнопкой запуска AI"""
        try:
            from core.services.help_service import HelpService
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            help_service = HelpService()

            help_message = await help_service.get_help_message(message.from_user.id)

            # Добавляем кнопку запуска AI агента (идентично help_with_ai)
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="🤖 Спросить AI агента", callback_data="ai_agent:start")]]
            )
            await message.answer(
                help_message,
                reply_markup=keyboard,
                parse_mode="HTML",
                disable_web_page_preview=True
            )
        except Exception as e:
            logger.error(f"Error in cmd_help: {e}", exc_info=True)
            await message.answer("❌ Произошла ошибка при загрузке справочной информации. Попробуйте позже.")

@router.message(Command("test_help"))
async def cmd_test_help(message: Message):
    """Тестовая команда для проверки ссылок"""
    try:
        from core.services.help_service import HelpService
        help_service = HelpService()
        
        # Получаем тестовое сообщение
        test_message = help_service.test_help_message()
        
        # Отправляем с HTML
        await message.answer(
            test_message,
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        
    except Exception as e:
        logger.error(f"Error in cmd_test_help: {e}", exc_info=True)
        await message.answer(f"❌ Ошибка теста: {e}")
    
    @router.message(Command("webapp"))
    async def cmd_webapp(message: Message):
        """Открыть WebApp личный кабинет"""
        try:
            # Получаем URL WebApp из настроек
            webapp_url = getattr(settings, 'webapp_url', 'https://web-production-d51c7.up.railway.app/webapp')
            
            # Создаем кнопку WebApp
            from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
            
            webapp_keyboard = ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(
                        text="🌐 Открыть Личный кабинет",
                        web_app=WebAppInfo(url=webapp_url)
                    )]
                ],
                resize_keyboard=True,
                one_time_keyboard=True
            )
            
            await message.answer(
                "🌐 <b>Личный кабинет WebApp</b>\n\n"
                "Откройте полноценный личный кабинет в браузере с удобным интерфейсом:\n\n"
                "• 📊 Дашборд и статистика\n"
                "• 🏪 Управление карточками (для партнеров)\n"
                "• 📋 Модерация (для админов)\n"
                "• ⚙️ Настройки системы\n\n"
                "Нажмите кнопку ниже для открытия:",
                reply_markup=webapp_keyboard,
                parse_mode="HTML"
            )
            
        except Exception as e:
            logger.error(f"Error in cmd_webapp: {e}", exc_info=True)
            await message.answer("❌ WebApp временно недоступен. Попробуйте позже.")

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
        await message.answer(
            "📄 <b>Политика конфиденциальности</b>\n\n"
            "Текст политики доступен по ссылке:\n"
            "<a href=\"/static/docs/policy.html\">/static/docs/policy.html</a>",
            parse_mode="HTML",
            disable_web_page_preview=True,
        )

# Удалено: обработчик /add не используется. Используйте /add_card (см. partner_router).

@router.message(Command("create_test_data"))
async def cmd_create_test_data(message: Message, state: FSMContext):
    """/create_test_data - команда для создания тестовых данных (только для админов)"""
    try:
        # Проверяем права администратора
        from core.security.roles import get_user_role
        user_role = await get_user_role(message.from_user.id)
        role_name = getattr(user_role, "name", str(user_role)).lower()
        
        if role_name not in ("admin", "super_admin"):
            await message.answer("⛔ Недостаточно прав. Только администраторы могут создавать тестовые данные.")
            return
        
        await message.answer("🔄 Создание тестовых данных...")
        
        # Создаем тестовые данные
        from core.services.test_data_creator import test_data_creator
        success = await test_data_creator.create_test_partners()
        
        if success:
            await message.answer(
                "✅ <b>Тестовые данные созданы успешно!</b>\n\n"
                "📊 <b>Создано:</b>\n"
                "• 5 тестовых партнеров\n"
                "• 36 тестовых заведений (по 2 в каждую подкатегорию)\n"
                "• Все заведения отправлены на модерацию\n\n"
                "🏷️ <b>Категории с тестовыми данными:</b>\n"
                "• 🍜 Рестораны (6 заведений)\n"
                "• 🧘 SPA и массаж (6 заведений)\n"
                "• 🛵 Аренда байков (6 заведений)\n"
                "• 🏨 Отели (6 заведений)\n"
                "• 🗺️ Экскурсии (6 заведений)\n"
                "• 🛍 Магазины и услуги (6 заведений)\n\n"
                "💡 <b>Что дальше:</b>\n"
                "• Проверьте дашборд - должны появиться заведения на модерации\n"
                "• Используйте кнопку '📋 Модерация' для просмотра\n"
                "• Заведения появятся в категориях после одобрения",
                parse_mode='HTML'
            )
        else:
            await message.answer("❌ Ошибка при создании тестовых данных.")
            
    except Exception as e:
        logger.error(f"Error in cmd_create_test_data: {e}")
        await message.answer("❌ Ошибка при создании тестовых данных.")

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
            
            # КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Сохраняем город в базу данных
            from ..services.profile import profile_service
            await profile_service.set_city_id(callback.from_user.id, city_id)
            
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
