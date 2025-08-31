import asyncio   
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ContentType
from aiogram.filters import Command, CommandStart
from aiogram.client.bot import DefaultBotProperties

from core.settings import settings
from core.utils.commands import set_commands
from core.filters.iscontact import IsTrueContact
from core.utils.locales import translations

from core.database.db import db

# Инициализация тестовых данных, если нет категорий
if not db.get_categories():
    db.add_category("🍜 Рестораны")
    db.add_place(
        name="Moc Quan",
        category="🍜 Рестораны",
        address="Нячанг, ул. Морская, 123",
        discount="10%",
        link="https://example.com",
        qr_code="https://example.com/qr.png"
    )

# Basic handlers with minimal imports
get_start = None
get_photo = None
get_hello = None
get_inline = None
feedback_user = None
hiw_user = None
main_menu = None
user_regional_rest = None
get_location = None
get_video = None
get_file = None
language_callback = None
main_menu_callback = None
test_menu_command = None

# Lazy imports to avoid circular dependencies
def _import_handlers():
    global get_start, get_photo, get_hello, get_inline, feedback_user
    global hiw_user, main_menu, user_regional_rest, get_location
    global get_video, get_file, language_callback, main_menu_callback, test_menu_command
    
    from core.handlers.basic import (
        get_start as _get_start,
        get_photo as _get_photo,
        get_hello as _get_hello,
        get_inline as _get_inline,
        feedback_user as _feedback_user,
        hiw_user as _hiw_user,
        main_menu as _main_menu,
        user_regional_rest as _user_regional_rest,
        get_location as _get_location,
        get_video as _get_video,
        get_file as _get_file,
        language_callback as _language_callback,
        main_menu_callback as _main_menu_callback,
        test_menu_command as _test_menu_command
    )
    
    # Assign to globals
    get_start = _get_start
    get_photo = _get_photo
    get_hello = _get_hello
    get_inline = _get_inline
    feedback_user = _feedback_user
    hiw_user = _hiw_user
    main_menu = _main_menu
    user_regional_rest = _user_regional_rest
    get_location = _get_location
    get_video = _get_video
    get_file = _get_file
    language_callback = _language_callback
    main_menu_callback = _main_menu_callback
    test_menu_command = _test_menu_command
from core.handlers.main_menu_router import main_menu_router  # Импортируем роутер меню
from core.handlers.callback import (
    rests_by_district_handler, rest_near_me_handler,
    rests_by_kitchen_handler, location_handler, router as callback_router
)
from core.handlers.contact import get_true_contact, get_fake_contact
from core.windows.qr import generate_qrcode, qr_code_check
from core.windows.restorans import (
    restoran_2_10_1_0, restoran_2_10_1_1, qr_code_postman
)
from core.handlers.category_handlers import (
    show_categories, show_nearest, handle_location, category_selected
)

from core.keyboards.reply import get_return_to_main_menu
from core.windows.main_menu import main_menu_text

# Формируем множества локализованных текстов для фильтров (для регистрации хендлеров)
localized_texts = {
    'back_to_main': {translations[lang]['back_to_main'] for lang in translations},
    'categories_button': {translations[lang]['choose_category'] for lang in translations},
    'show_nearest': {translations[lang]['show_nearest'] for lang in translations},
    'choose_language': {translations[lang]['choose_language'] for lang in translations},
}

async def start_bot(bot: Bot):
    await set_commands(bot)
    await bot.send_message(settings.bots.admin_id, " Бот запущен")

async def stop_bot(bot: Bot):
    await bot.send_message(settings.bots.admin_id, " Бот остановлен")

async def start():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - [%(levelname)s] - %(name)s - (%(filename)s).%(funcName)s(%(lineno)d) - %(message)s"
    )

    default_properties = DefaultBotProperties(parse_mode=ParseMode.HTML)
    bot = Bot(token=settings.bots.bot_token, default=default_properties)
    dp = Dispatcher()

    # Регистрируем роутеры и хендлеры
    from core.handlers import (
        basic,
        callback,
        profile,
        partner,
        activity,
        admin_cabinet,
        category_handlers
    )
    
    # Включаем все роутеры
    dp.include_router(basic.router)
    dp.include_router(callback_router)
    dp.include_router(main_menu_router)
    
    # Включаем фичевые роутеры
    for getr in (
        getattr(profile, "get_profile_router", None),
        getattr(partner, "get_partner_router", None),
        getattr(activity, "get_activity_router", None),
        getattr(category_handlers, "get_category_router", None),
    ):
        if callable(getr):
            r = getr()
            if r:
                dp.include_router(r)

    # Импортируем обработчики при первом запуске
    _import_handlers()
    
    # Старт, смена языка
    dp.message.register(
        lambda message, bot, state: get_start(message, bot, state), 
        CommandStart()
    )
    dp.message.register(
        lambda message, bot, state: get_start(message, bot, state), 
        F.text.in_(localized_texts['choose_language'])
    )
    dp.callback_query.register(language_callback, F.data.startswith("lang_"))

    # Тестовая команда для отладки меню
    dp.message.register(test_menu_command, Command(commands='test_menu'))
    
    # Добавляем логирование для отладки
    @dp.startup()
    async def on_startup():
        logger.info("Bot started with features: %s", settings.features.dict())
    
    # Помощь, отзывы, главное меню
    dp.message.register(hiw_user, Command(commands='help'))
    dp.message.register(hiw_user, F.text.in_(localized_texts['choose_language']))
    dp.message.register(feedback_user, Command(commands='feedback'))
    dp.message.register(main_menu, Command(commands='main_menu'))
    dp.message.register(main_menu, F.text.in_(localized_texts['back_to_main']))

    # Рестораны - примеры
    dp.message.register(restoran_2_10_1_0, F.text == 'Hải sản Mộc quán Nha Trang')
    dp.message.register(restoran_2_10_1_0, F.text == 'Hải sản Mộc quán Nha Trang🦞')
    dp.callback_query.register(restoran_2_10_1_0, F.data == 'restoran_2_10_1_0')
    dp.message.register(restoran_2_10_1_1, F.text == 'Тест рест')
    dp.callback_query.register(restoran_2_10_1_1, F.data == 'restoran_2_10_1_1')

    # QR-код постман
    dp.message.register(qr_code_postman, F.text == 'Нажмите здесь')
    dp.callback_query.register(qr_code_postman, F.data == 'callback_data')

    # Категории и локация
    dp.message.register(show_categories, F.text.in_(localized_texts['categories_button']))
    dp.message.register(show_nearest, F.text.in_(localized_texts['show_nearest']))
    dp.message.register(handle_location, F.content_type == ContentType.LOCATION)
    dp.message.register(category_selected, F.text.regexp(r'^.+\s.+$'))

    # Выбор районов, ближайшие, кухня
    dp.message.register(user_regional_rest, F.text == 'Выбор ресторана по районам🌆')
    dp.callback_query.register(rest_near_me_handler, F.data == 'rest_near_me')
    dp.callback_query.register(rests_by_district_handler, F.data == 'rests_by_district')
    dp.callback_query.register(rests_by_kitchen_handler, F.data == 'rests_by_kitchen')

    # Обработка callback главного меню
    dp.callback_query.register(
        main_menu_callback,
        F.data.in_({"show_categories", "rests_by_district", "rest_near_me", "change_language", "back_to_main"})
    )

    # Разное
    dp.message.register(get_hello, F.text.lower().startswith('привет'))
    dp.message.register(get_photo, F.content_type == ContentType.PHOTO)
    dp.message.register(get_true_contact, F.content_type == ContentType.CONTACT, IsTrueContact())
    dp.message.register(get_fake_contact, F.content_type == ContentType.CONTACT)
    dp.message.register(get_location, F.content_type == ContentType.LOCATION)
    dp.message.register(get_video, F.content_type == ContentType.VIDEO)
    dp.message.register(get_file, F.content_type == ContentType.ANIMATION)

    # Дополнительный фильтр возврата в меню (на всякий случай)
    dp.message.register(main_menu, F.text.in_(localized_texts['back_to_main']))

    # Стартап и шутдаун
    dp.startup.register(start_bot)
    dp.shutdown.register(stop_bot)

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == '__main__':
    asyncio.run(start())
