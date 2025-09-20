"""
Tests for the admin queue delete handler using direct testing approach.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

# Test data
TEST_CARD_ID = 123
TEST_PAGE = 1
TEST_USER_ID = 12345
TEST_CALLBACK_DATA = f"adm:q:del:confirm:{TEST_CARD_ID}:{TEST_PAGE}"

# Mock classes for testing
class MockSettings:
    class Features:
        moderation = True
    
    features = Features()

class MockAdminsService:
    def is_admin(self, user_id):
        return True

class MockDB:
    def delete_card(self, card_id):
        return True

# Create a test class
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
        
        # Patch the handler's dependencies
        self.patchers = [
            patch('core.handlers.admin_cabinet.db_v2', self.mock_db),
            patch('core.handlers.admin_cabinet.admins_service', self.mock_admins),
            patch('core.handlers.admin_cabinet.settings', self.mock_settings),
        ]
        
        # Apply patches
        for patcher in self.patchers:
            patcher.start()
        
        # Import the handler after patching
        from core.handlers.admin_cabinet import admin_queue_delete
        self.handler = admin_queue_delete
        
        yield self
        
        # Clean up patches
        for patcher in self.patchers:
            patcher.stop()
    
    @pytest.mark.asyncio
    async def test_successful_deletion(self):
        """Test successful card deletion."""
        # Setup
        self.mock_db.delete_card = MagicMock(return_value=True)
        
        # Execute
        await self.handler(self.callback, None)
        
        # Assertions
        self.mock_db.delete_card.assert_called_once_with(TEST_CARD_ID)
        self.callback.answer.assert_called_once_with("🗑 Карточка удалена", show_alert=False)
    
    @pytest.mark.asyncio
    async def test_not_admin(self):
        """Test access by non-admin user."""
        # Setup
        self.mock_admins.is_admin = MagicMock(return_value=False)
        
        # Execute
        await self.handler(self.callback, None)
        
        # Assertions
        self.callback.answer.assert_called_once_with("❌ Доступ запрещён")
        assert not hasattr(self.mock_db, 'delete_card') or not self.mock_db.delete_card.called
    
    @pytest.mark.asyncio
    async def test_moderation_disabled(self):
        """Test when moderation is disabled."""
        # Setup
        self.mock_settings.features.moderation = False
        
        # Execute
        await self.handler(self.callback, None)
        
        # Assertions
        self.callback.answer.assert_called_once_with("🚧 Модуль модерации отключён.")
        assert not hasattr(self.mock_db, 'delete_card') or not self.mock_db.delete_card.called
    
    @pytest.mark.asyncio
    async def test_invalid_format(self):
        """Test with invalid callback data format."""
        # Setup
        self.callback.data = "invalid:format"
        
        # Execute
        await self.handler(self.callback, None)
        
        # Assertions
        self.callback.answer.assert_called_once_with("❌ Ошибка формата данных", show_alert=True)
        assert not hasattr(self.mock_db, 'delete_card') or not self.mock_db.delete_card.called
    
    @pytest.mark.asyncio
    async def test_database_error(self):
        """Test handling of database errors."""
        # Setup
        self.mock_db.delete_card = MagicMock(side_effect=Exception("Database error"))
        
        # Execute
        await self.handler(self.callback, None)
        
        # Assertions
        self.callback.answer.assert_called_once_with(
            "❌ Произошла ошибка при удалении карточки. Пожалуйста, попробуйте ещё раз.",
            show_alert=True
        )
