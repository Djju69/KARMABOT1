"""
Main bot module for KarmaBot.
This module initializes the bot instance and sets up the dispatcher.
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = str(Path(__file__).parent.parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.handlers.RotatingFileHandler(
            'bot.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
    ]
)
logger = logging.getLogger(__name__)

# Global bot and dispatcher instances
bot = None
dp = None

# Log Python and path info
logger.info(f"Python: {sys.version}")
logger.info(f"Current directory: {os.getcwd()}")
logger.info(f"Files in directory: {os.listdir('.')}")

# Import aiogram after path setup
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramConflictError, TelegramBadRequest
from aiogram.fsm.context import FSMContext

# Import middlewares
from core.middleware import setup_rbac_middleware, setup_2fa_middleware
from core.middleware.privacy_policy import PrivacyPolicyMiddleware

# Initialize bot with default properties
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is not set")
    
logger.info(f"Initializing bot with token: {BOT_TOKEN[:10]}...{BOT_TOKEN[-5:] if BOT_TOKEN else 'MISSING'}")

# Create global bot and dispatcher instances
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

dp = Dispatcher()

try:
    
    # Setup middlewares
    # Ensure SQLite user_roles exists to avoid 'no such table' during RBAC
    try:
        from core.database import db_v2
        from core.database.roles import ensure_sqlite_user_roles_table
        ensure_sqlite_user_roles_table(db_v2)
        logger.info("✅ Ensured user_roles table exists (SQLite)")
    except Exception as e:
        logger.warning(f"Could not ensure user_roles table: {e}")

    # КРИТИЧЕСКИ ВАЖНО: Privacy Policy middleware должен быть ПЕРВЫМ
    dp.message.middleware(PrivacyPolicyMiddleware())
    dp.callback_query.middleware(PrivacyPolicyMiddleware())
    logger.info("🔒 Privacy Policy Middleware registered - ALL actions now protected")
    
    setup_rbac_middleware(dp)
    setup_2fa_middleware(dp)
    
    # Add test command handler
    @dp.message(Command("start"))
    async def cmd_start(message: types.Message, state: FSMContext):
        logger.info(f"Received /start from user {message.from_user.id}")
        try:
            # Delegate to main start flow to show reply menu
            from core.handlers.basic import get_start
            await get_start(message, bot, state)
        except Exception as e:
            logger.warning(f"Fallback start handler due to error: {e}")
            await message.answer("🚀 Бот запущен и работает!")
    
    # Import and include other handlers
    try:
        # Register command handlers (e.g., /clear_cache)
        try:
            from core.handlers.commands import register_commands
            register_commands(dp)
            logger.info("✅ Command handlers registered")
        except Exception as e:
            logger.warning(f"⚠️ Failed to register command handlers: {e}")

        # Import 2FA handlers
        from core.handlers.two_factor_handlers import handlers as two_factor_handlers
        for handler in two_factor_handlers:
            dp.include_router(handler)
            
        # Import admin audit handlers
        from core.handlers.admin_audit_handlers import handlers as admin_audit_handlers
        for handler in admin_audit_handlers:
            dp.include_router(handler)
            
        # Import individual routers with error handling
        routers = []
        
        # Helper function to safely import and get router
        def get_router(module_name):
            try:
                module = __import__(f'core.handlers.{module_name}', fromlist=[module_name])
                # Skip modules that don't have routers
                if module_name == 'commands':
                    logger.info("ℹ️  Skipping commands module as it doesn't have a router")
                    return None
                    
                # Try common router attribute names
                dynamic_names = [
                    'router',
                    'message_router',
                    'command_router',
                    'main_router',
                    f'{module_name}_router',   # e.g. language_router, profile_router
                    'profile_router',
                    'partner_router',
                    'activity_router',
                    'language_router',
                    'main_menu_router',
                    'category_router',
                    'plastic_cards_router',    # Добавляем роутер для карм и карт
                    'cabinet_router',          # Добавляем роутер для личного кабинета
                ]
                for attr in dynamic_names:
                    if hasattr(module, attr):
                        router = getattr(module, attr)
                        logger.info(f"✅ Found router {attr} in {module_name}")
                        return router
                logger.warning(f"⚠️ No router found in {module_name}")
                return None
            except ImportError as e:
                logger.warning(f"⚠️ Failed to import {module_name}: {e}")
                return None
        
        # Список модулей обработчиков (без commands)
        # Обновлено: используем актуальные имена и v2-версии где нужно
        handler_modules = [
            'help_with_ai',         # Справка + AI агент — первыми
            'callback',             # Колбэки (язык/политика) — до текстовых
            'language',             # Язык — до главного меню
            'main_menu_router',     # ГЛАВНОЕ МЕНЮ — раньше остальных, чтобы кнопки не перехватывались
            'basic',
            'profile',
            'partner',
            'activity',
            'admin_cabinet',
            'category_handlers_v2', # Категории
            'plastic_cards_router', # Карты
            'cabinet_router',       # Личный кабинет
            'partner_fsm_router',   # FSM партнёров
            'partner_confirmation_router',
            'broadcast_router',
            'loyalty_settings_router'
        ]
        
        # Get all available routers
        for module_name in handler_modules:
            router = get_router(module_name)
            if router:
                routers.append(router)
        
        # Include all found routers
        for router in routers:
            try:
                if router:
                    dp.include_router(router)
                    logger.info(f"✅ Successfully included router from {router}")
            except Exception as e:
                logger.error(f"❌ Failed to include router {router}: {e}", exc_info=True)

        # Diagnostic: log unhandled updates (at the very end)
        @dp.update()
        async def _log_unhandled(update: types.Update):
            try:
                logger.warning("⚠️ Unhandled update: %s", update)
            except Exception:
                pass
        
        # Set up commands directly since commands.py doesn't have a router
        async def setup_commands():
            try:
                from core.handlers.commands import set_commands
                await set_commands(bot)
                logger.info("✅ Bot commands set up successfully")
                return True
            except Exception as e:
                logger.error(f"❌ Failed to set up bot commands: {e}", exc_info=True)
                return False
                
        # Run command setup in the event loop
        import asyncio
        asyncio.create_task(setup_commands())
        
        logger.info(f"✅ All routers initialized. Total routers: {len(routers)}")
        
    except ImportError as e:
        logger.error(f"Failed to import handlers: {e}", exc_info=True)
        logger.warning("Running in limited mode with only basic commands")
    
    # This will be called from start.py
    async def start():
        """Start the bot with conflict/logged-out auto-recovery"""
        import asyncio
        import os
        max_retries = 10
        attempt = 0
        
        # Assign SUPER_ADMIN role to configured admin in SQLite runtime (best-effort)
        try:
            from core.settings import settings as _settings
            admin_id = getattr(_settings.bots, 'admin_id', None)
            if isinstance(admin_id, int) and admin_id > 0:
                from core.database import role_repository
                from core.database.roles import RoleEnum
                await role_repository.set_user_role(int(admin_id), RoleEnum.SUPER_ADMIN)
                logger.info("✅ Ensured SUPER_ADMIN role for admin_id=%s", admin_id)
        except Exception as _e:
            logger.warning("Could not assign SUPER_ADMIN role at startup: %s", _e)
        
        # Check if we should use webhook mode
        webhook_url = os.getenv('WEBHOOK_URL')
        disable_polling = os.getenv('DISABLE_POLLING', 'false').lower() == 'true'
        
        if webhook_url and disable_polling:
            logger.info("🚀 Starting bot with webhook...")
            try:
                # Preflight: ensure bot is not in 'Logged out' state
                try:
                    await bot.get_me()
                except TelegramBadRequest as pre:
                    if "Logged out" in str(pre):
                        logger.warning(f"Bot is 'Logged out' (preflight). Retrying...")
                        await asyncio.sleep(5)
                        await bot.get_me()
                    else:
                        raise

                # Set webhook
                await bot.set_webhook(
                    url=webhook_url,
                    allowed_updates=["message", "callback_query"]
                )
                logger.info("✅ Webhook set up successfully")
                
                # Start webhook (aiogram 3.x syntax)
                # В webhook режиме бот работает через веб-сервер, не нужно запускать polling
                logger.info("✅ Webhook mode activated - bot ready to receive updates")
                
            except Exception as e:
                logger.error(f"❌ Webhook startup error: {e}", exc_info=True)
                raise
        else:
            logger.info("🚀 Starting bot with polling...")
            while True:
                try:
                    # Preflight: ensure bot is not in 'Logged out' state
                    try:
                        await bot.get_me()
                    except TelegramBadRequest as pre:
                        if "Logged out" in str(pre):
                            attempt += 1
                            wait_s = min(60 + attempt * 10, 180)
                            logger.warning(f"Bot is 'Logged out' (preflight). Retry in {wait_s}s (attempt {attempt}/{max_retries})")
                            await asyncio.sleep(wait_s)
                            if attempt >= max_retries:
                                logger.critical("Exceeded max retries due to 'Logged out'. Aborting.")
                                raise
                            continue
                        else:
                            raise

                    await dp.start_polling(bot, skip_updates=True)
                    return
                except TelegramConflictError as e:
                    attempt += 1
                    logger.error(
                        f"TelegramConflictError on polling (attempt {attempt}/{max_retries}): {e}",
                        exc_info=False,
                    )
                    # Try to cleanup conflicts and retry
                    try:
                        logger.info("🧹 deleteWebhook(drop_pending_updates=True)")
                        await bot.delete_webhook(drop_pending_updates=True)
                    except Exception as ce:
                        logger.warning(f"delete_webhook failed: {ce}")
                    if attempt >= max_retries:
                        logger.critical("Exceeded max retries due to conflicts. Aborting.")
                        raise
                    logger.info("⏳ Waiting 3s before retry...")
                    await asyncio.sleep(3)
                    continue
                except TelegramBadRequest as e:
                    if "Logged out" in str(e):
                        attempt += 1
                        wait_s = min(60 + attempt * 10, 180)
                        logger.warning(f"Bot is 'Logged out'. Retry in {wait_s}s (attempt {attempt}/{max_retries})")
                        if attempt >= max_retries:
                            logger.critical("Exceeded max retries due to 'Logged out'. Aborting.")
                            raise
                        await asyncio.sleep(wait_s)
                        continue
                    raise
                except Exception as e:
                    logger.critical(f"Bot polling failed: {e}", exc_info=True)
                    raise
    
    # For direct execution
    if __name__ == "__main__":
        logger.info("Starting bot in direct execution mode")
        import asyncio
        asyncio.run(start())
        
except Exception as e:
    logger.critical(f"Failed to initialize bot: {e}", exc_info=True)
    raise

# Export bot and dispatcher for webhook usage
__all__ = ['bot', 'dp']
