"""
KARMABOT1 - Enhanced main entry point with backward compatibility
Integrates all new components while preserving existing functionality
"""
import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ContentType
from aiogram.filters import Command, CommandStart
from aiogram.client.bot import DefaultBotProperties

# Core imports
from core.settings import settings
from core.utils.commands import set_commands
from core.filters.iscontact import IsTrueContact
from core.utils.locales_v2 import get_text, get_all_texts

# Database services
from core.database.migrations import ensure_database_ready
from core.database.db_v2 import db_v2

# Enhanced services
from core.services.card_renderer import card_service
from core.keyboards.reply_v2 import get_main_menu_reply, get_return_to_main_menu
from core.services.profile import profile_service
from core.middlewares.locale import LocaleMiddleware

# Handlers - Legacy (always enabled)
from core.handlers.basic import (
    get_start, get_photo, get_hello, get_inline, feedback_user,
    hiw_user, main_menu, user_regional_rest,
    get_location, get_video, get_file, language_callback, main_menu_callback
)
from core.handlers.basic import router as basic_router
from core.handlers.callback import (
    rests_by_district_handler, rest_near_me_handler,
    rests_by_kitchen_handler, location_handler, router as callback_router
)
from core.handlers.contact import get_true_contact, get_fake_contact

# Legacy windows (backward compatibility)
from core.windows.qr import generate_qrcode, qr_code_check
from core.windows.restorans import (
    restoran_2_10_1_0, restoran_2_10_1_1, qr_code_postman
)
from core.windows.main_menu import main_menu_text

# Enhanced handlers (feature-flagged)
from core.handlers.partner import get_partner_router
from core.handlers.moderation import get_moderation_router

# Enhanced category handlers
from core.handlers.category_handlers_v2 import (
    show_categories_v2, show_nearest_v2, handle_location_v2, 
    category_selected_v2, get_category_router
)

logger = logging.getLogger(__name__)

async def init_test_data():
    """Initialize test data if no categories exist (backward compatible)"""
    try:
        categories = db_v2.get_categories()
        if not categories:
            logger.info("Initializing test data...")
            
            # Add legacy test place for backward compatibility
            db_v2.add_legacy_place(
                name="Moc Quan",
                category="🍜 Рестораны",
                address="Нячанг, ул. Морская, 123",
                discount="10%",
                link="https://example.com",
                qr_code="https://example.com/qr.png"
            )
            
            logger.info("Test data initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize test data: {e}")

async def setup_enhanced_handlers(dp: Dispatcher):
    """Setup enhanced handlers based on feature flags"""
    
    # Always include legacy callback router
    dp.include_router(callback_router)
    
    # Enhanced category handling (always enabled, backward compatible)
    category_router = get_category_router()
    dp.include_router(category_router)
    
    # Partner FSM (feature-flagged)
    if settings.features.partner_fsm:
        partner_router = get_partner_router()
        dp.include_router(partner_router)
        logger.info("✅ Partner FSM enabled")
    else:
        logger.info("⚠️ Partner FSM disabled")
    
    # Moderation (feature-flagged)
    if settings.features.moderation:
        moderation_router = get_moderation_router()
        dp.include_router(moderation_router)
        logger.info("✅ Moderation enabled")
    else:
        logger.info("⚠️ Moderation disabled")

async def setup_legacy_handlers(dp: Dispatcher):
    """Setup legacy handlers for backward compatibility"""
    
    # Include basic router to activate new Phase 1 handlers defined via decorators
    dp.include_router(basic_router)

    # Localized text sets for filters (backward compatible)
    localized_texts = {
        'back_to_main': {get_text('back_to_main', lang) for lang in ['ru', 'en', 'vi', 'ko']},
        'categories_button': {get_text('choose_category', lang) for lang in ['ru', 'en', 'vi', 'ko']},
        'show_nearest': {get_text('show_nearest', lang) for lang in ['ru', 'en', 'vi', 'ko']},
        'choose_language': {get_text('choose_language', lang) for lang in ['ru', 'en', 'vi', 'ko']},
        'profile': {get_text('profile', lang) for lang in ['ru', 'en', 'vi', 'ko']},
        'help': {get_text('help', lang) for lang in ['ru', 'en', 'vi', 'ko']},
    }
    
    # Start and language handlers
    dp.message.register(get_start, CommandStart())
    dp.message.register(get_start, F.text.in_(localized_texts['choose_language']))
    dp.callback_query.register(language_callback, F.data.startswith("lang_"))
    
    # Help, feedback, main menu
    dp.message.register(hiw_user, Command(commands='help'))
    dp.message.register(hiw_user, F.text.in_(localized_texts['help']))
    dp.message.register(feedback_user, Command(commands='feedback'))
    dp.message.register(main_menu, Command(commands='main_menu'))
    dp.message.register(main_menu, F.text.in_(localized_texts['back_to_main']))
    
    # Legacy restaurant handlers (preserve exact patterns)
    dp.message.register(restoran_2_10_1_0, F.text == 'Hải sản Mộc quán Nha Trang🦞')
    dp.callback_query.register(restoran_2_10_1_0, F.data == 'restoran_2_10_1_0')
    dp.message.register(restoran_2_10_1_1, F.text == 'Тест рест')
    dp.callback_query.register(restoran_2_10_1_1, F.data == 'restoran_2_10_1_1')
    
    # QR-код postman (legacy)
    dp.message.register(qr_code_postman, F.text == 'Нажмите здесь')
    dp.callback_query.register(qr_code_postman, F.data == 'callback_data')
    
    # Enhanced category handlers (backward compatible)
    dp.message.register(show_categories_v2, F.text.in_(localized_texts['categories_button']))
    dp.message.register(show_nearest_v2, F.text.in_(localized_texts['show_nearest']))
    dp.message.register(handle_location_v2, F.content_type == ContentType.LOCATION)
    dp.message.register(category_selected_v2, F.text.regexp(r'^.+\s.+$'))
    
    # Profile handler (feature-flagged)
    if settings.features.new_menu:
        from core.handlers.profile import handle_profile
        dp.message.register(handle_profile, F.text.in_(localized_texts['profile']))
    
    # Regional restaurants
    dp.message.register(user_regional_rest, F.text == 'Выбор ресторана по районам🌆')
    dp.callback_query.register(rest_near_me_handler, F.data == 'rest_near_me')
    dp.callback_query.register(rests_by_district_handler, F.data == 'rests_by_district')
    dp.callback_query.register(rests_by_kitchen_handler, F.data == 'rests_by_kitchen')
    
    # Main menu callback handler
    dp.callback_query.register(
        main_menu_callback,
        F.data.in_({
            "show_categories", "rests_by_district", "rest_near_me", 
            "change_language", "back_to_main", "profile"
        })
    )
    
    # Content handlers
    dp.message.register(get_hello, F.text.lower().startswith('привет'))
    dp.message.register(get_photo, F.content_type == ContentType.PHOTO)
    dp.message.register(get_true_contact, F.content_type == ContentType.CONTACT, IsTrueContact())
    dp.message.register(get_fake_contact, F.content_type == ContentType.CONTACT)
    dp.message.register(get_location, F.content_type == ContentType.LOCATION)
    dp.message.register(get_video, F.content_type == ContentType.VIDEO)
    dp.message.register(get_file, F.content_type == ContentType.ANIMATION)
    
    # Additional return to menu handler (safety net)
    dp.message.register(main_menu, F.text.in_(localized_texts['back_to_main']))

async def start_bot(bot: Bot):
    """Bot startup handler"""
    await set_commands(bot)
    
    startup_message = "🚀 **KARMABOT1 запущен**\n\n"
    startup_message += f"🔧 **Конфигурация:**\n"
    startup_message += f"   • Среда: {settings.environment}\n"
    startup_message += f"   • База: {settings.database.url}\n\n"
    startup_message += f"🎛️ **Фича-флаги:**\n"
    startup_message += f"   • Partner FSM: {'✅' if settings.features.partner_fsm else '❌'}\n"
    startup_message += f"   • Moderation: {'✅' if settings.features.moderation else '❌'}\n"
    startup_message += f"   • New Menu: {'✅' if settings.features.new_menu else '❌'}\n"
    startup_message += f"   • QR WebApp: {'✅' if settings.features.qr_webapp else '❌'}\n"
    
    await bot.send_message(settings.bots.admin_id, startup_message)

async def stop_bot(bot: Bot):
    """Bot shutdown handler"""
    await bot.send_message(settings.bots.admin_id, "❌ **KARMABOT1 остановлен**")

async def start():
    """Main entry point"""
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format="%(asctime)s - [%(levelname)s] - %(name)s - (%(filename)s).%(funcName)s(%(lineno)d) - %(message)s"
    )
    
    logger.info("🚀 Starting KARMABOT1...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Feature flags: {settings.features}")
    
    # Ensure database is ready
    if not ensure_database_ready():
        logger.error("❌ Database initialization failed!")
        return
    
    # Initialize test data
    await init_test_data()
    
    # Setup bot
    default_properties = DefaultBotProperties(parse_mode='HTML')
    bot = Bot(token=settings.bots.bot_token, default=default_properties)
    dp = Dispatcher()
    
    # Connect services
    await profile_service.connect(redis_url=settings.database.redis_url)
    
    # Middlewares
    dp.update.middleware(LocaleMiddleware())
    
    # Setup handlers
    await setup_enhanced_handlers(dp)
    await setup_legacy_handlers(dp)
    
    # Startup and shutdown handlers
    dp.startup.register(start_bot)
    dp.shutdown.register(stop_bot)
    
    logger.info("✅ All handlers registered successfully")
    
    try:
        logger.info("🔄 Starting polling...")
        # Ensure no webhook is set before long polling to prevent conflicts
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"❌ Bot crashed: {e}")
        raise
    finally:
        await bot.session.close()
        logger.info("🔒 Bot session closed")

if __name__ == '__main__':
    try:
        asyncio.run(start())
    except KeyboardInterrupt:
        logger.info("👋 Bot stopped by user")
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
        raise
