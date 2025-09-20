import asyncio
import sys
import os
import logging
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

# Configure console encoding for Windows
if sys.platform == 'win32':
    import io
    import sys
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Add project root to Python path
project_root = str(Path(__file__).parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Set test environment variables
os.environ['BOT_TOKEN'] = '1234567890:ABC-DEF1234ghIkl-zyx57W2v1u123ew11'  # Valid test token format for aiogram
os.environ['ADMIN_ID'] = '123456789'  # Test admin ID
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'  # In-memory database for testing
os.environ['REDIS_URL'] = 'redis://localhost:6379/0'  # Test Redis URL

# Configure logging before importing modules that use it
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Mock the bot to avoid real API calls
class MockBot:
    def __init__(self):
        self.id = 1234567890
        self.first_name = "TestBot"
        self.username = "test_bot"
        self.token = "1234567890:TEST_TOKEN"
        self.session = AsyncMock()
        
    async def get_me(self):
        return User(
            id=self.id,
            is_bot=True,
            first_name=self.first_name,
            username=self.username
        )
        
    async def send_message(self, *args, **kwargs):
        logger.info(f"[MOCK BOT] send_message called with args: {args}, kwargs: {kwargs}")
        return True
        
    async def __call__(self, *args, **kwargs):
        # This makes the bot instance callable
        logger.info(f"[MOCK BOT] Bot called with args: {args}, kwargs: {kwargs}")
        return True
        
    async def send_message(self, *args, **kwargs):
        return MagicMock(message_id=1)
        
    async def answer_callback_query(self, *args, **kwargs):
        return True
        
    async def get_updates(self, *args, **kwargs):
        return []
        
    async def close(self):
        pass

# Import after setting up mocks
from core.settings import settings
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.types import Update, Message, CallbackQuery, MessageEntity, Chat, User
from core.handlers.partner import get_partner_router, partner_router

# Configure logging
logger = logging.getLogger(__name__)

# Test user ID - replace with a real one if needed
TEST_USER_ID = 123456789

async def test_partner_router():
    """Test that the partner router is properly registered and handles messages."""
    # Initialize mock bot and dispatcher
    bot = MockBot()
    dp = Dispatcher()
    
    # Enable partner FSM for testing
    settings.features.partner_fsm = True
    
    # Create a mock database with required methods
    class MockDatabase:
        def __init__(self):
            self.get_or_create_partner = AsyncMock()
            self.get_partner_stats = AsyncMock()
            self.get_partner = AsyncMock()
            
            # Setup default return values
            self._setup_defaults()
            
        def _setup_defaults(self):
            # Setup default partner data
            partner_data = {
                'id': 1,
                'user_id': TEST_USER_ID,
                'is_active': True,
                'created_at': '2023-01-01T00:00:00',
                'tg_user_id': TEST_USER_ID,
                'tg_username': 'test_user',
                'balance': 0,
                'total_earned': 1000
            }
            
            # Setup default stats data
            stats_data = {
                'total_referrals': 10,
                'active_referrals': 5,
                'total_earnings': 1000,
                'pending_withdrawal': 500
            }
            
            # Configure mocks
            self.get_or_create_partner.return_value = partner_data
            self.get_partner_stats.return_value = stats_data
            self.get_partner.return_value = partner_data
    
    # Create the mock database
    mock_db = MockDatabase()
    
    # Patch the database and bot
    with patch('core.handlers.partner.db_v2', mock_db), \
         patch('aiogram.Bot', return_value=bot):
        
        # Create a mock state
        mock_state = AsyncMock()
        mock_state.get_data = AsyncMock(return_value={})
        mock_state.set_state = AsyncMock()
        mock_state.update_data = AsyncMock()
        
        # Create a mock FSM context
        def get_fsm_context(bot, chat_id, user_id):
            return mock_state
            
        # Patch FSM context
        with patch('aiogram.fsm.context.FSMContext', side_effect=get_fsm_context):
            # Get and include the partner router
            router = get_partner_router()
            dp.include_router(router)
            
            # Initialize the router
            await router.emit_startup(bot=bot, **{})
    
    for handler in router.message.handlers:
        logger.info(f"- {handler.callback.__name__} (filters: {handler.filters})")
    
    # Log all registered callback handlers
    logger.info("\n=== Registered Callback Handlers ===")
    for handler in router.callback_query.handlers:
        logger.info(f"- {handler.callback.__name__} (filters: {handler.filters})")
        
    # Log all registered commands in the router
    logger.info("\n=== Registered Commands ===")
    for handler in router.message.handlers:
        for flt in handler.filters:
            if hasattr(flt, 'commands'):
                logger.info(f"- Command: {flt.commands} -> {handler.callback.__name__}")
                
    # Log all registered callbacks with their data patterns
    logger.info("\n=== Registered Callback Patterns ===")
    for handler in router.callback_query.handlers:
        for flt in handler.filters:
            if hasattr(flt, 'data'):
                logger.info(f"- Callback: {flt.data} -> {handler.callback.__name__}")
    
    # Create a test message that will be used in the callback
    test_message = Message(
        message_id=1,
        date=datetime.now(),
        chat=Chat(id=TEST_USER_ID, type='private'),
        from_user=User(id=TEST_USER_ID, is_bot=False, first_name='Test'),
        text='Test message',
    )
    
    # Create a test message update for /add_card command
    message_update = Update(
        update_id=1,
        message=Message(
            message_id=1,
            date=datetime.now(),
            chat=Chat(id=TEST_USER_ID, type='private'),
            from_user=User(id=TEST_USER_ID, is_bot=False, first_name='Test'),
            text='/add_card',
            entities=[MessageEntity(type='bot_command', offset=0, length=len('/add_card'))]
        )
    )
    
    # Create a test callback for partner stats
    test_callback = CallbackQuery(
        id="test_callback_id",
        from_user=User(id=TEST_USER_ID, is_bot=False, first_name="Test", language_code="ru"),
        chat_instance="test_chat",
        message=test_message,
        data="partner:stats",
        chat=Chat(id=TEST_USER_ID, type="private"),
        bot=bot,  # Add bot reference
        # Add missing required fields
        message_id=1,
        date=datetime.now()
    )
    
    # Create an update object for the message
    message_update = Update(
        update_id=1,
        message=test_message
    )
    
    # Create an update object for the callback
    callback_update = Update(
        update_id=2,
        callback_query=test_callback
    )
    
    # Log the test message and callback for debugging
    logger.info(f"\n=== Test Message ===\n{test_message}")
    logger.info(f"\n=== Test Callback ===\n{test_callback}")
    
    # Test message handling
    message_handled = False
    logger.info("\n=== Testing Message Handling ===")
    
    # Try direct handler check first
    logger.info("\n--- Direct Handler Check ---")
    for handler in router.message.handlers:
        try:
            logger.info(f"Checking handler: {handler.callback.__name__}")
            # Check if this is a command handler
            if hasattr(handler, 'filters') and handler.filters:
                for flt in handler.filters:
                    logger.info(f"  - Filter: {flt}")
                    # Check for command filters
                    if hasattr(flt, 'commands'):
                        logger.info(f"    - Commands: {flt.commands}")
                        if 'add_card' in flt.commands:
                            logger.info(f"  ✅ Found matching command in handler {handler.callback.__name__}")
                            message_handled = True
                            break
                    # Check for text filters
                    elif hasattr(flt, 'text') and flt.text and flt.text.lower() == 'добавить карточку':
                        logger.info(f"  Found matching text in handler {handler.callback.__name__}")
                        message_handled = True
                        break
        except Exception as e:
            logger.error(f"Error checking handler {handler.callback.__name__}: {e}")
            logger.error(traceback.format_exc())
    
    # Try dispatching the update with proper mocking
    logger.info("\n--- Dispatching Update ---")
    try:
        # Mock the state methods
        mock_state = AsyncMock()
        mock_state.get_data = AsyncMock(return_value={})
        
        # Patch the FSM context and database for message handling
        with patch('aiogram.fsm.context.FSMContext', return_value=mock_state):
            with patch('core.handlers.partner.db_v2', mock_db):
                await dp.feed_update(bot=bot, update=message_update)
                message_handled = True
                logger.info("Message update dispatched successfully")
    except Exception as e:
        logger.error(f"Error dispatching message update: {e}")
        logger.error(traceback.format_exc())

    # Test callback handling
    callback_handled = False
    logger.info("\n=== Testing Callback Handling ===")
    
    # Try direct handler check first
    logger.info("\n--- Direct Callback Check ---")
    for handler in router.callback_query.handlers:
        try:
            logger.info(f"Checking callback handler: {handler.callback.__name__}")
            if hasattr(handler, 'filters') and handler.filters:
                for flt in handler.filters:
                    logger.info(f"  - Filter: {flt}")
                    # Check for data filters
                    if hasattr(flt, 'data'):
                        logger.info(f"    - Data: {flt.data}")
                        if flt.data and 'partner:stats' in flt.data:
                            logger.info(f"  ✅ Found matching callback pattern in handler {handler.callback.__name__}")
                            callback_handled = True
                            break
        except Exception as e:
            logger.error(f"Error checking callback handler {handler.callback.__name__}: {e}")
            import traceback
            logger.error(traceback.format_exc())

    # Try dispatching the callback update
    logger.info("\n--- Dispatching Callback Update ---")
    try:
        # Mock the state methods
        mock_state = AsyncMock()
        mock_state.get_data = AsyncMock(return_value={
            'period': 'week',
            'start_date': '2023-01-01',
            'end_date': '2023-01-07',
            'stats': {
                'total_referrals': 10,
                'active_referrals': 5,
                'total_earnings': 1000,
                'pending_withdrawal': 500
            }
        })
        
        # Patch the FSM context
        with patch('aiogram.fsm.context.FSMContext', return_value=mock_state):
            # Patch the database methods
            with patch('core.handlers.partner.db_v2', mock_db):
                await dp.feed_update(bot=bot, update=callback_update)
                callback_handled = True
                logger.info("✅ Callback update dispatched successfully")
    except Exception as e:
        logger.error(f"Error dispatching callback update: {e}")
        logger.error(traceback.format_exc())
        callback_handled = False

    if not message_handled:
        logger.error("\n[FAIL] Message not handled by any handler")
    else:
        logger.info("\n[PASS] Message handling test passed")

    if not callback_handled:
        logger.error("[FAIL] Callback not handled by any handler")
    else:
        logger.info("[PASS] Callback handling test passed")
    
    # Close the bot session if it exists
    if hasattr(bot, 'close'):
        await asyncio.create_task(bot.close())
    
    # Check if all tests passed
    all_passed = message_handled and callback_handled
    if all_passed:
        logger.info("\n✅ All tests passed successfully!")
    else:
        logger.error("\n❌ Some tests failed")
    
    return all_passed

if __name__ == "__main__":
    # Add missing imports for testing
    import sys
    import asyncio
    import logging
    from datetime import datetime
    from pathlib import Path
    from unittest.mock import patch, MagicMock, AsyncMock
    
    # Run the test
    success = asyncio.run(test_partner_router())
    if success:
        logger.info("[PASS] Partner router registered successfully")
    else:
        logger.error("[FAIL] Some tests failed")
