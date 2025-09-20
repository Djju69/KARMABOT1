"""
Tests for the admin queue delete handler.
"""
import pytest
import logging
import sys
from unittest.mock import AsyncMock, MagicMock, patch, Mock

# Add the project root to the Python path
sys.path.insert(0, 'C:\\Users\\d9955\\CascadeProjects\\KARMABOT1-fixed')

# Test data
TEST_CARD_ID = 123
TEST_PAGE = 1
TEST_USER_ID = 12345
TEST_CALLBACK_DATA = f"adm:q:del:confirm:{TEST_CARD_ID}:{TEST_PAGE}"

# Mock modules that would be imported by the handler
sys.modules['core.handlers.admin_cabinet'] = Mock()
sys.modules['core.handlers.admin_cabinet'].settings = Mock()
sys.modules['core.handlers.admin_cabinet'].settings.features = Mock(moderation=True)
sys.modules['core.handlers.admin_cabinet'].db_v2 = Mock()
sys.modules['core.handlers.admin_cabinet'].admins_service = Mock()
sys.modules['core.handlers.admin_cabinet'].logger = logging.getLogger(__name__)

class TestAdminQueueDelete:
    """Test cases for admin_queue_delete handler."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test environment."""
        # Create mocks
        self.mock_db = Mock()
        self.mock_db.delete_card = AsyncMock(return_value=True)
        
        self.mock_admins = Mock()
        self.mock_admins.is_admin = AsyncMock(return_value=True)
        
        # Create callback mock
        self.callback = AsyncMock()
        self.callback.data = TEST_CALLBACK_DATA
        self.callback.from_user.id = TEST_USER_ID
        self.callback.answer = AsyncMock()
        self.callback.message = AsyncMock()
        
        # Patch the imports
        self.patchers = [
            patch('core.handlers.admin_cabinet.db_v2', self.mock_db),
            patch('core.handlers.admin_cabinet.admins_service', self.mock_admins),
            patch('core.handlers.admin_cabinet.settings', Mock(features=Mock(moderation=True)))
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
        
        return self
    
    @pytest.mark.asyncio
    async def test_successful_deletion(self, setup, caplog):
        """Test successful card deletion."""
        # Setup
        self.mock_admins.is_admin.return_value = True
        self.mock_db.delete_card.return_value = True
        
        # Execute
        with caplog.at_level(logging.INFO):
            await self.handler(self.callback, None)
        
        # Assertions
        self.mock_admins.is_admin.assert_called_once_with(TEST_USER_ID)
        self.mock_db.delete_card.assert_called_once_with(TEST_CARD_ID)
        self.callback.answer.assert_called_once_with("🗑 Карточка удалена", show_alert=False)
        
        # Verify logging
        assert f"admin.delete: moderator={TEST_USER_ID} card={TEST_CARD_ID} ok=True" in caplog.text
    
    @pytest.mark.asyncio
    async def test_not_admin(self, setup):
        """Test access by non-admin user."""
        # Setup
        self.mock_admins.is_admin.return_value = False
        
        # Execute
        await self.handler(self.callback, None)
        
        # Assertions
        self.callback.answer.assert_called_once_with("❌ Доступ запрещён")
        self.mock_db.delete_card.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_moderation_disabled(self, setup):
        """Test when moderation is disabled."""
        # Setup
        self.mock_admins.is_admin.return_value = True
        with patch('core.handlers.admin_cabinet.settings', Mock(features=Mock(moderation=False))):
            # Re-import the handler with the new settings
            from core.handlers.admin_cabinet import admin_queue_delete
            self.handler = admin_queue_delete
        
        # Execute
        await self.handler(self.callback, None)
        
        # Assertions
        self.callback.answer.assert_called_once_with("🚧 Модуль модерации отключён.")
        self.mock_db.delete_card.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_invalid_format(self, setup, caplog):
        """Test with invalid callback data format."""
        # Setup
        self.callback.data = "invalid:format"
        
        # Execute
        with caplog.at_level(logging.ERROR):
            await self.handler(self.callback, None)
        
        # Assertions
        self.callback.answer.assert_called_once_with("❌ Ошибка формата данных", show_alert=True)
        self.mock_db.delete_card.assert_not_called()
        assert "Invalid callback data format: invalid:format" in caplog.text
    
    @pytest.mark.asyncio
    async def test_missing_parts_in_callback(self, setup, caplog):
        """Test with missing parts in callback data."""
        # Setup
        self.callback.data = "adm:q:del:confirm:123"  # Missing page
        
        # Execute
        with caplog.at_level(logging.ERROR):
            await self.handler(self.callback, None)
        
        # Assertions
        self.callback.answer.assert_called_once_with("❌ Ошибка формата данных", show_alert=True)
        self.mock_db.delete_card.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_invalid_card_id_format(self, setup, caplog):
        """Test with non-numeric card ID."""
        # Setup
        self.callback.data = "adm:q:del:confirm:not_an_integer:1"
        
        # Execute
        with caplog.at_level(logging.ERROR):
            await self.handler(self.callback, None)
        
        # Assertions
        self.callback.answer.assert_called_once_with("❌ Ошибка формата данных", show_alert=True)
        self.mock_db.delete_card.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_database_error(self, setup, caplog):
        """Test handling of database errors."""
        # Setup
        self.mock_admins.is_admin.return_value = True
        self.mock_db.delete_card.side_effect = Exception("Database error")
        
        # Execute
        with caplog.at_level(logging.ERROR):
            await self.handler(self.callback, None)
        
        # Assertions
        self.callback.answer.assert_called_once_with(
            "❌ Произошла ошибка при удалении карточки. Пожалуйста, попробуйте ещё раз.",
            show_alert=True
        )
        assert "Error in admin_queue_delete" in caplog.text
        assert "Database error" in caplog.text
