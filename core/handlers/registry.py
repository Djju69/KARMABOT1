"""
Handlers Registry
Централизованная регистрация всех handlers из main_v2.py
"""
import logging
from aiogram import Dispatcher
from core.settings import get_settings

logger = logging.getLogger(__name__)

def register_all_handlers(dp: Dispatcher):
    """
    Зарегистрировать все handlers в правильном порядке
    
    Порядок из main_v2.py:
    1. main_menu -> basic -> callback -> categories -> profile -> cabinet -> activity 
    2. partner/moderation -> admin -> ping (last)
    """
    logger.info("📝 Registering all handlers...")
    
    try:
        # === БАЗОВЫЕ HANDLERS ===
        from core.handlers import (
            basic_router,
            callback_router,
        )
        from core.handlers.main_menu_router import main_menu_router
        from core.handlers.category_handlers_v2 import get_category_router
        from core.handlers.profile import get_profile_router
        from core.handlers.cabinet_router import get_cabinet_router
        from core.handlers.activity import get_activity_router
        from core.handlers.moderation import get_moderation_router
        from core.handlers.admin_cabinet import get_admin_cabinet_router
        from core.handlers import ping
        
        # === СПЕЦИАЛИЗИРОВАННЫЕ HANDLERS ===
        from core.handlers.partner import partner_router as partner_router_instance
        from core.handlers.loyalty_settings_router import router as loyalty_settings_router
        from core.handlers.tariff_admin_router import router as tariff_admin_router
        from core.handlers.tariffs_user_router import router as tariffs_user_router
        from core.handlers.language_router import router as language_router
        from core.handlers.gamification_router import router as gamification_router
        from core.handlers.temp_catalog_fix import temp_router
        
        # === РЕГИСТРАЦИЯ В ПРАВИЛЬНОМ ПОРЯДКЕ ===
        
        # 1) Main menu first
        dp.include_router(main_menu_router)
        logger.info("✅ Main menu router registered")
        
        # 2) Basic and callback
        dp.include_router(basic_router)
        dp.include_router(callback_router)
        logger.info("✅ Basic and callback routers registered")
        
        # 3) Categories
        dp.include_router(get_category_router())
        logger.info("✅ Category router registered")
        
        # 4) Profile and cabinet
        prof = get_profile_router()
        if prof:
            dp.include_router(prof)
        dp.include_router(get_cabinet_router())
        logger.info("✅ Profile and cabinet routers registered")
        
        # 5) Activity
        dp.include_router(get_activity_router())
        logger.info("✅ Activity router registered")
        
        # 6) Partner router
        dp.include_router(partner_router_instance)
        logger.info("✅ Partner router registered")
        
        # 7) Moderation and admin (under feature flag if needed)
        settings = get_settings()
        if getattr(settings.features, "moderation", True):
            dp.include_router(get_moderation_router())
            dp.include_router(get_admin_cabinet_router())
            logger.info("✅ Moderation and admin routers registered")
        
        # 8) Loyalty settings FSM
        dp.include_router(loyalty_settings_router)
        logger.info("✅ Loyalty settings router registered")
        
        # 9) Tariff management (admin only)
        dp.include_router(tariff_admin_router)
        logger.info("✅ Tariff admin router registered")
        
        # 9.1) Tariff commands for all users
        dp.include_router(tariffs_user_router)
        logger.info("✅ Tariffs user router registered")
        
        # 9.2) Language selection router
        dp.include_router(language_router)
        logger.info("✅ Language router registered")
        
        # 9.3) Gamification router
        dp.include_router(gamification_router)
        logger.info("✅ Gamification router registered")
        
        # 10) ВРЕМЕННЫЙ роутер для исправления каталога
        dp.include_router(temp_router)
        logger.info("✅ Temp catalog fix router registered")
        
        # 11) Ping/catch-alls LAST
        dp.include_router(ping.router)
        logger.info("✅ Ping router registered")
        
        logger.info("🎉 All handlers registered successfully!")
        
    except ImportError as e:
        logger.error(f"❌ Failed to import handler: {e}")
        raise
    except Exception as e:
        logger.error(f"❌ Failed to register handlers: {e}")
        raise
