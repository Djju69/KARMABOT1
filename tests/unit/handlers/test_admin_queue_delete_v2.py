"""
Tests for the admin queue delete handler.
"""
import pytest
from unittest.mock import patch, MagicMock

from tests.test_helpers import (
    MockTelegramUpdate,
    MockTelegramContext,
    MockDatabase,
    MockAdminService,
    MockProfileService
)

class TestAdminQueueDelete:
    """Test cases for admin_queue_delete handler."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test environment."""
        # Create mocks
        self.mock_db = MockDatabase()
        self.mock_admins = MockAdminService(is_admin=True)
        self.mock_profile = MockProfileService()
        
        # Create test data
        self.test_card_id = 123
        self.test_page = 1
        self.test_user_id = 12345
        self.callback_data = f"adm:q:del:confirm:{self.test_card_id}:{self.test_page}"
        
        # Create update and context
        self.update = MockTelegramUpdate(callback_data=self.callback_data, user_id=self.test_user_id)
        self.context = MockTelegramContext()
        
        # Import handler with mocks
        with patch('core.handlers.admin_cabinet.db_v2', self.mock_db), \
             patch('core.handlers.admin_cabinet.admins_service', self.mock_admins), \
             patch('core.handlers.admin_cabinet.profile_service', self.mock_profile):
            from core.handlers.admin_cabinet import admin_queue_delete
            self.handler = admin_queue_delete
        
        return self
    
    @pytest.mark.asyncio
    async def test_successful_deletion(self, setup):
        """Test successful card deletion."""
        # Execute
        await self.handler(self.update.callback_query, self.context)
        
        # Assertions
        self.mock_admins.is_admin.assert_called_once_with(self.test_user_id)
        self.mock_db.delete_card.assert_called_once_with(self.test_card_id)
        self.update.callback_query.answer.assert_called_once_with("🗑 Карточка удалена", show_alert=False)
    
    @pytest.mark.asyncio
    async def test_not_admin(self, setup):
        """Test access by non-admin user."""
        # Setup
        self.mock_admins.is_admin.return_value = False
        
        # Execute
        await self.handler(self.update.callback_query, self.context)
        
        # Assertions
        self.update.callback_query.answer.assert_called_once_with("❌ Доступ запрещён")
        self.mock_db.delete_card.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_invalid_callback_data(self, setup):
        """Test with invalid callback data format."""
        # Setup
        self.update.callback_query.data = "invalid:format"
        
        # Execute
        await self.handler(self.update.callback_query, self.context)
        
        # Assertions
        self.update.callback_query.answer.assert_called_once_with("❌ Ошибка формата данных", show_alert=True)
        self.mock_db.delete_card.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_database_error(self, setup):
        """Test handling of database errors."""
        # Setup
        self.mock_db.delete_card.return_value = False
        
        # Execute
        await self.handler(self.update.callback_query, self.context)
        
        # Assertions
        self.update.callback_query.answer.assert_called_once_with("❌ Ошибка при удалении карточки", show_alert=True)
