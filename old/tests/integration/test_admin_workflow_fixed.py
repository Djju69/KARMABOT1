"""Integration tests for admin panel workflows."""
import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime, timedelta
from aiogram import Dispatcher, Bot
from aiogram.types import Update, Message, User, Chat, CallbackQuery
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey


def create_mock_update(text: str, user_id: int, message_id: int = 1, is_callback: bool = False):
    """Create a mock Telegram update for testing.
    
    Args:
        text: Message text or callback data
        user_id: Sender's user ID
        message_id: Message ID (default: 1)
        is_callback: Whether this is a callback query (default: False)
    """
    user = User(
        id=user_id,
        is_bot=False,
        first_name="Test",
        last_name="User",
        username="testuser"
    )
    
    if is_callback:
        message = Message(
            message_id=message_id,
            date=datetime.now(),
            chat=Chat(id=user_id, type="private"),
            from_user=user
        )
        callback_query = CallbackQuery(
            id="test_callback",
            from_user=user,
            chat_instance="test_chat",
            message=message,
            data=text
        )
        return Update(update_id=message_id, callback_query=callback_query)
    else:
        message = Message(
            message_id=message_id,
            date=datetime.now(),
            chat=Chat(id=user_id, type="private"),
            from_user=user,
            text=text
        )
        return Update(update_id=message_id, message=message)


async def process_update(dp: Dispatcher, update: Update, mock_bot=None):
    """Process an update through the dispatcher and return the response.
    
    Args:
        dp: Dispatcher instance
        update: Update to process
        mock_bot: Optional pre-configured mock bot
        
    Returns:
        str: Response text or None if no response was generated
    """
    print("\n=== Starting process_update ===")
    print(f"Update type: {update.message.text if update.message else update.callback_query.data}")
    
    # Use provided mock_bot or create a new mock
    bot = mock_bot or AsyncMock(spec=Bot)
    bot.token = "test_token"
    
    # Mock bot methods that might be called
    bot.send_message = AsyncMock()
    bot.answer_callback_query = AsyncMock()
    bot.edit_message_text = AsyncMock()
    
    try:
        # Create FSM context
        user_id = update.message.from_user.id if update.message else update.callback_query.from_user.id
        chat_id = update.message.chat.id if update.message else update.callback_query.message.chat.id
        
        print(f"Processing update for user_id={user_id}, chat_id={chat_id}")
        
        storage_key = StorageKey(
            bot_id=bot.id,
            chat_id=chat_id,
            user_id=user_id
        )
        
        fsm_context = FSMContext(
            storage=dp.storage,
            key=storage_key
        )
        
        print("Dispatching update...")
        # Process the update
        await dp.feed_update(bot=bot, update=update, **{"state": fsm_context})
        
        # Debug output
        print(f"bot.send_message called: {bot.send_message.called}")
        if bot.send_message.called:
            print(f"Call args: {bot.send_message.call_args}")
        
        # Return the last sent message text if available
        if bot.send_message.called:
            last_call = bot.send_message.call_args[0]
            print(f"Returning response: {last_call[1] if len(last_call) > 1 else last_call[0]}")
            return last_call[1] if len(last_call) > 1 else last_call[0]
        
        print("No response generated")
        return None
    except Exception as e:
        print(f"Error in process_update: {e}")
        import traceback
        traceback.print_exc()
        return None


class ResponseMiddleware:
    """Middleware to capture the response from the bot."""
    
    def __init__(self, response_handler):
        self.response_handler = response_handler
    
    async def __call__(self, handler, event, data):
        result = await handler(event, data)
        if result:
            await self.response_handler(
                data.get("bot"),
                data.get("event_update"),
                **result
            )
        return result


# Test data
TEST_ADMIN = {
    'id': 1,
    'username': 'testadmin',
    'role': 'admin',
    'is_active': True,
    'created_at': datetime.utcnow() - timedelta(days=30)
}

TEST_LISTING = {
    'id': 1,
    'name': 'Test Listing',
    'status': 'pending',
    'category': 'test',
    'created_at': datetime.utcnow() - timedelta(days=1),
    'updated_at': datetime.utcnow() - timedelta(hours=1)
}

class TestAdminPanelIntegration:
    """Integration tests for admin panel workflows."""
    
    @pytest.fixture(autouse=True)
    def setup_mocks(self):
        """Setup common mocks for all tests."""
        # Mock the admin service
        self.auth_patcher = patch('core.services.admins.admins_service.is_admin', AsyncMock(return_value=True))
        
        # Mock settings
        self.settings_patcher = patch('core.settings.settings')
        self.mock_settings = self.settings_patcher.start()
        
        # Configure mock settings
        self.mock_settings.features.moderation = True
        self.mock_settings.bots.admin_id = str(TEST_ADMIN['id'])
        
        # Mock the profile service
        self.profile_patcher = patch('core.services.profile_service.get_lang', AsyncMock(return_value='ru'))
        self.mock_get_lang = self.profile_patcher.start()
        
        # Start the auth patcher
        self.mock_is_admin = self.auth_patcher.start()
        
        yield
        
        # Cleanup
        self.auth_patcher.stop()
        self.settings_patcher.stop()
        self.profile_patcher.stop()

    @pytest.fixture(scope="function")
    async def setup_router(self):
        """Create a fresh router instance for each test."""
        print("\n=== Setting up router ===")
        
        # Create a fresh dispatcher for this test
        dp = Dispatcher(storage=MemoryStorage())
        
        # Get a fresh router instance
        from core.handlers import admin_cabinet
        from core.settings import settings
        from importlib import reload
        
        # Enable moderation feature
        settings.features.moderation = True
        print(f"Moderation feature enabled: {settings.features.moderation}")
        
        # Reload the module to get a fresh router with updated settings
        reload(admin_cabinet)
        print("Reloaded admin_cabinet module")
        
        # Get the router directly instead of using get_admin_cabinet_router
        admin_router = admin_cabinet.router
        print(f"Got admin router: {admin_router}")
        print(f"Router name: {admin_router.name}")
        print(f"Router handlers: {admin_router.message.handlers}")
        
        # Clear any existing routers
        dp.sub_routers.clear()
        print("Cleared existing routers")
        
        # Include the router in the dispatcher
        dp.include_router(admin_router)
        print(f"Included admin router. Dispatcher routers: {dp.sub_routers}")
        
        # Verify router is registered
        from aiogram.dispatcher.router import Router
        def print_routers(router: Router, level=0):
            indent = '  ' * level
            print(f"{indent}- {router.name} (handlers: {len(router.message.handlers)})")
            for sub_router in router.sub_routers:
                print_routers(sub_router, level + 1)
        
        print("\nRouter hierarchy:")
        print_routers(dp)
        
        return dp
        
    @pytest.mark.asyncio
    async def test_moderation_workflow(self, test_database, setup_router):
        """Test complete moderation workflow."""
        dp = setup_router
    
        # Enable moderation feature for testing
        from core.settings import settings
        settings.features.moderation = True

        # Create a mock bot
        mock_bot = AsyncMock(spec=Bot)
        mock_bot.send_message = AsyncMock()
        mock_bot.id = 1  # Add bot ID for FSM context

        # Add test listing
        await test_database.execute(
            """
            INSERT INTO listings (id, name, status, category, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                TEST_LISTING['id'],
                TEST_LISTING['name'],
                TEST_LISTING['status'],
                TEST_LISTING['category'],
                TEST_LISTING['created_at'].isoformat(),
                TEST_LISTING['updated_at'].isoformat()
            )
        )

        # Mock admin checks and other dependencies
        with patch('core.services.admins.admins_service.is_admin', AsyncMock(return_value=True)), \
             patch('core.database.db_v2.db_v2.get_connection', return_value=test_database), \
             patch('core.services.profile.profile_service.get_lang', AsyncMock(return_value='ru')):
            
            # Get the command handler directly
            from core.handlers.admin_cabinet import open_admin_cabinet
            
            # Create a mock message
            message = AsyncMock()
            message.text = "/admin"
            message.from_user.id = TEST_ADMIN['id']
            message.chat.id = 1
            message.answer = AsyncMock()
            
            # Call the handler directly
            await open_admin_cabinet(
                message=message,
                bot=mock_bot,
                state=FSMContext(
                    storage=dp.storage,
                    key=StorageKey(bot_id=1, chat_id=1, user_id=TEST_ADMIN['id'])
                )
            )
            
            # Verify the handler was called and captured the response
            message.answer.assert_called_once()
            args, kwargs = message.answer.call_args
            response_text = kwargs.get("text", "")
            
            # Verify the response contains the expected text
            assert "Панель администратора" in response_text, f"Expected 'Панель администратора' in response, got: {response_text}"
            
            # Verify the keyboard is included in the response
            assert "reply_markup" in kwargs, "No reply_markup in the response"
            
            # Now test with the router
            # Reset mocks
            message.answer.reset_mock()
            
            # Create a new update and process it
            update = create_mock_update("/admin", user_id=TEST_ADMIN['id'])
            response = await process_update(dp, update, mock_bot)
            
            # Since process_update doesn't return the response, we need to check the mock
            assert mock_bot.send_message.called, "Bot's send_message was not called"
            call_args = mock_bot.send_message.call_args[1]
            assert "text" in call_args, "No text in the bot's response"
            assert "Панель администратора" in call_args["text"], "Admin panel title not found in response"
            
            # Test queue view
            update = create_mock_update("/admin_queue", user_id=TEST_ADMIN['id'])
            response = await process_update(dp, update, mock_bot)
            
            assert response is not None
            assert "Очередь модерации" in response
            assert TEST_LISTING['name'] in response
            
            # Test listing approval
            update = create_mock_update(
                f"approve_{TEST_LISTING['id']}", 
                user_id=TEST_ADMIN['id'],
                is_callback=True
            )
            response = await process_update(dp, update, mock_bot)
            
            assert response is not None
            assert "одобрено" in response.lower()
            
            # Verify listing is no longer in queue
            update = create_mock_update("/admin_queue", user_id=TEST_ADMIN['id'])
            response = await process_update(dp, update, mock_bot)
            
            # Verify queue doesn't contain our test listing anymore
            assert response is not None
            assert TEST_LISTING['name'] not in response
        
    
    @pytest.mark.asyncio
    async def test_admin_management_workflow(self, test_database, setup_router):
        """Test admin management workflow (for superadmins)."""
        dp = setup_router
        
        # Enable moderation feature for testing
        from core.settings import settings
        settings.features.moderation = True
    
        # Create a mock bot
        mock_bot = AsyncMock(spec=Bot)
        mock_bot.send_message = AsyncMock()
        
        # Update test admin to be superadmin (by setting admin_id)
        from core.settings import settings
        settings.bots.admin_id = str(TEST_ADMIN['id'])
        
        # Add a test admin to manage
        test_admin_id = 2
        await test_database.execute(
            """
            INSERT OR REPLACE INTO users (id, username, role, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                test_admin_id,
                'testadmin2',
                'admin',
                1,
                datetime.utcnow().isoformat(),
                datetime.utcnow().isoformat()
            )
        )
        
        # Mock admin checks and other dependencies
        with patch('core.services.admins.admins_service.is_admin', AsyncMock(return_value=True)), \
             patch('core.database.db_v2.db_v2.get_connection', return_value=test_database):
            
            # Test admin search
            update = create_mock_update("/admin_search testadmin2", user_id=TEST_ADMIN['id'])
            response = await process_update(dp, update, mock_bot)
            
            assert response is not None
            assert "Поиск администраторов" in response
            assert "testadmin2" in response
            
            # Test admin panel access
            update = create_mock_update("/admin", user_id=TEST_ADMIN['id'])
            response = await process_update(dp, update, mock_bot)
            assert response is not None
            assert "Панель администратора" in response
    
    @pytest.mark.asyncio
    async def test_report_generation_workflow(self, test_database, setup_router):
        """Test report generation workflow."""
        dp = setup_router
        
        # Enable moderation feature for testing
        from core.settings import settings
        settings.features.moderation = True
    
        # Create a mock bot
        mock_bot = AsyncMock(spec=Bot)
        mock_bot.send_message = AsyncMock()
        
        # Set test admin as superadmin
        from core.settings import settings
        settings.bots.admin_id = str(TEST_ADMIN['id'])
        
        # Create test listing
        listing_data = (
            'test-listing-1',
            'Test Listing 1',
            'published',
            'test',
            datetime.utcnow().isoformat(),
            datetime.utcnow().isoformat()
        )
        
        # Create test listing in database
        await test_database.execute("""
            CREATE TABLE IF NOT EXISTS listings (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                status TEXT NOT NULL,
                category TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        await test_database.execute(
            """
            INSERT OR REPLACE INTO listings 
            (id, name, status, category, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            listing_data
        )
        
        # Mock admin checks and other dependencies
        with patch('core.services.admins.admins_service.is_admin', AsyncMock(return_value=True)), \
             patch('core.database.db_v2.db_v2.get_connection', return_value=test_database):
            
            # Test admin panel access
            update = create_mock_update("/admin", user_id=TEST_ADMIN['id'])
            response = await process_update(dp, update, mock_bot)
            assert response is not None
            assert "Панель администратора" in response
            
            # Test report generation
            update = create_mock_update("Сгенерировать отчет", user_id=TEST_ADMIN['id'])
            response = await process_update(dp, update, mock_bot)
            
            # Check if report was generated or if we got a message about reports
            assert response is not None
            assert any(phrase in response for phrase in ["Отчет", "Статистика", "отчетов"])
            assert "Панель администратора" in response
            
            # Go to reports section
            update = create_mock_update("Отчеты", user_id=TEST_ADMIN['id'])
            response = await process_update(dp, update)
            assert response is not None
            assert "Генерация отчетов" in response
            
            # Test daily report
            update = create_mock_update("Ежедневный отчет", user_id=TEST_ADMIN['id'])
            response = await process_update(dp, update)
            assert response is not None
            assert "Ежедневный отчет" in response
            
            # Go back to reports
            update = create_mock_update("Назад к отчетам", user_id=TEST_ADMIN['id'])
            response = await process_update(dp, update)
            
            # Test weekly report
            update = create_mock_update("Недельный отчет", user_id=TEST_ADMIN['id'])
            response = await process_update(dp, update)
            assert response is not None
            assert "Недельный отчет" in response
            
            # Go back to reports
            update = create_mock_update("Назад к отчетам", user_id=TEST_ADMIN['id'])
            response = await process_update(dp, update)
            
            # Test monthly report
            update = create_mock_update("Месячный отчет", user_id=TEST_ADMIN['id'])
            response = await process_update(dp, update)
            assert response is not None
            assert "Месячный отчет" in response
