from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
import os
import logging

def build_bot() -> Bot:
    """Создание и настройка бота"""
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        raise ValueError("BOT_TOKEN is required")
    
    bot = Bot(
        token=bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    logging.info("Bot created successfully")
    return bot

def build_dispatcher() -> Dispatcher:
    """Создание и настройка диспетчера"""
    dp = Dispatcher()
    
    # Импорт и регистрация роутеров
    try:
        from core.handlers.basic import router as basic_router
        dp.include_router(basic_router)
        logging.info("Basic router registered")
    except ImportError as e:
        logging.warning(f"Basic router not found: {e}")
    
    # Регистрация главного меню
    try:
        from core.handlers.main_menu_router import main_menu_router
        dp.include_router(main_menu_router)
        logging.info("Main menu router registered")
    except ImportError as e:
        logging.warning(f"Main menu router not found: {e}")
    
    # Регистрация обработчиков траты баллов
    try:
        from core.handlers.spend import router as spend_router
        dp.include_router(spend_router)
        logging.info("Spend points router registered")
    except ImportError as e:
        logging.warning(f"Spend points router not found: {e}")
    
    # Регистрация истории операций
    try:
        from core.handlers.history import router as history_router
        dp.include_router(history_router)
        logging.info("History router registered")
    except ImportError as e:
        logging.warning(f"History router not found: {e}")
    
    # Обработчики колбэков
    try:
        from core.handlers.callback import router as callback_router
        dp.include_router(callback_router)
        logging.info("Callback router registered")
    except ImportError as e:
        logging.warning(f"Callback router not found: {e}")
    
    # Админ-панель
    try:
        from core.handlers.admin_cabinet import router as admin_router
        dp.include_router(admin_router)
        logging.info("Admin cabinet router registered")
    except ImportError as e:
        logging.warning(f"Admin cabinet router not found: {e}")
    
    # Регистрация профиля
    try:
        from core.handlers.profile import profile_router
        dp.include_router(profile_router)
        logging.info("Profile router registered")
    except ImportError as e:
        logging.warning(f"Profile router not found: {e}")

    # Регистрация языка
    try:
        from core.handlers.language import language_router
        dp.include_router(language_router)
        logging.info("Language router registered")
    except ImportError as e:
        logging.warning(f"Language router not found: {e}")

    # Роутеры-фабрики (если включены соответствующие фичи)
    if getattr(settings.features, 'partner_fsm', False):
        try:
            from core.handlers.partner import partner_router
            dp.include_router(partner_router)
            logging.info("Partner router registered")
        except ImportError as e:
            logging.warning(f"Partner router not found: {e}")

    try:
        from core.handlers.activity import activity_router
        dp.include_router(activity_router)
        logging.info("Activity router registered")
    except ImportError as e:
        logging.warning(f"Activity router not found: {e}")
    
    try:
        from core.handlers.category_handlers_v2 import get_category_router
        dp.include_router(get_category_router())
        logging.info("Category router registered")
    except ImportError as e:
        logging.warning(f"Category router not found: {e}")
    
    logging.info("Dispatcher configured successfully")
    return dp
