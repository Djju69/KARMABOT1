"""
Tests for the admin queue delete handler.
"""
import pytest
import logging
from unittest.mock import AsyncMock, MagicMock, patch

# Test data
TEST_CARD_ID = 123
TEST_PAGE = 1
TEST_USER_ID = 12345
TEST_CALLBACK_DATA = f"adm:q:del:confirm:{TEST_CARD_ID}:{TEST_PAGE}"

# Mock classes
class MockBot:
    """Mock Bot class for testing."""
    async def edit_message_text(self, *args, **kwargs):
        """Mock edit_message_text method."""
        pass

class MockDB:
    """Mock database class for testing."""
    def delete_card(self, card_id):
        """Mock delete_card method."""
        return True

class MockAdminsService:
    """Mock admins service for testing."""
    def is_admin(self, user_id):
        """Mock is_admin method."""
        return True

class MockSettings:
    """Mock settings for testing."""
    class Features:
        """Mock features settings."""
        moderation = True
    
    features = Features()

# Mock the logger
logger = logging.getLogger(__name__)

# Import the handler with mocks
with patch('core.handlers.admin_cabinet.db_v2', MockDB()), \
     patch('core.handlers.admin_cabinet.admins_service', MockAdminsService()), \
     patch('core.handlers.admin_cabinet.settings', MockSettings()):
    from core.handlers.admin_cabinet import admin_queue_delete

class TestAdminQueueDelete:
    """Test cases for admin_queue_delete handler."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test environment."""
        # Create mocks
        self.mock_db = MockDB()
        self.mock_admins = MockAdminsService()
        self.mock_settings = MockSettings()
        
        # Create callback mock
        self.callback = AsyncMock()
        self.callback.data = TEST_CALLBACK_DATA
        self.callback.from_user.id = TEST_USER_ID
        self.callback.answer = AsyncMock()
        self.callback.message = AsyncMock()
        self.callback.message.edit_text = AsyncMock()
        
        # Save original handler
        self.original_handler = admin_queue_delete
        
        # Apply patches
        self.patchers = [
            patch('core.handlers.admin_cabinet.db_v2', self.mock_db),
            patch('core.handlers.admin_cabinet.admins_service', self.mock_admins),
            patch('core.handlers.admin_cabinet.settings', self.mock_settings),
            patch('core.handlers.admin_cabinet.logger', logger)
        ]
        
        for patcher in self.patchers:
            patcher.start()
        
        yield self
        
        # Clean up
        for patcher in self.patchers:
            patcher.stop()
    
    @pytest.mark.asyncio
    async def test_successful_deletion(self, caplog):
        """Test successful card deletion."""
        # Setup
        self.mock_admins.is_admin = MagicMock(return_value=True)
        self.mock_db.delete_card = MagicMock(return_value=True)
        
        # Execute
        await admin_queue_delete(self.callback, None)
        
        # Assertions
        self.mock_admins.is_admin.assert_called_once_with(TEST_USER_ID)
        self.mock_db.delete_card.assert_called_once_with(TEST_CARD_ID)
        self.callback.answer.assert_called_once_with("🗑 Карточка удалена", show_alert=False)
    
    @pytest.mark.asyncio
    async def test_not_admin(self):
        """Test access by non-admin user."""
        # Setup
        self.mock_admins.is_admin = MagicMock(return_value=False)
        
        # Execute
        await admin_queue_delete(self.callback, None)
        
        # Assertions
        self.callback.answer.assert_called_once_with("❌ Доступ запрещён")
        assert not self.mock_db.delete_card.called
    
    @pytest.mark.asyncio
    async def test_moderation_disabled(self):
        """Test when moderation is disabled."""
        # Setup
        self.mock_settings.features.moderation = False
        
        # Execute
        await admin_queue_delete(self.callback, None)
        
        # Assertions
        self.callback.answer.assert_called_once_with("🚧 Модуль модерации отключён.")
        assert not self.mock_db.delete_card.called
    
    @pytest.mark.asyncio
    async def test_invalid_format(self):
        """Test with invalid callback data format."""
        # Setup
        self.callback.data = "invalid:format"
        
        # Execute
        await admin_queue_delete(self.callback, None)
        
        # Assertions
        self.callback.answer.assert_called_once_with("❌ Ошибка формата данных", show_alert=True)
        assert not self.mock_db.delete_card.called
    
    @pytest.mark.asyncio
    async def test_database_error(self, caplog):
        """Test handling of database errors."""
        # Setup
        self.mock_admins.is_admin = MagicMock(return_value=True)
        self.mock_db.delete_card = MagicMock(side_effect=Exception("Database error"))
        
        # Execute
        with caplog.at_level(logging.ERROR):
            await admin_queue_delete(self.callback, None)
        
        # Assertions
        self.callback.answer.assert_called_once_with(
            "❌ Произошла ошибка при удалении карточки. Пожалуйста, попробуйте ещё раз.",
            show_alert=True
        )
        assert "Error in admin_queue_delete" in caplog.text
        assert "Database error" in caplog.text
