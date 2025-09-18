"""
Simplified tests for admin_queue_delete handler.
These tests don't depend on the application's settings module.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

class TestAdminQueueDeleteSimple:
    """Test cases for admin_queue_delete handler (simplified version)."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test environment."""
        # Create mocks
        self.mock_db = MagicMock()
        self.mock_db.delete_card = AsyncMock(return_value=True)
        
        self.mock_admins = MagicMock()
        self.mock_admins.is_admin.return_value = True
        
        self.mock_profile = MagicMock()
        self.mock_profile.get_lang.return_value = 'ru'
        
        # Create callback mock
        self.callback = AsyncMock()
        self.callback.data = "adm:q:del:confirm:123:1"
        self.callback.from_user.id = 12345
        self.callback.answer = AsyncMock()
        self.callback.message = AsyncMock()
        
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
        await self.handler(self.callback, None)
        
        # Assertions
        self.mock_admins.is_admin.assert_called_once_with(12345)
        self.mock_db.delete_card.assert_called_once_with(123)
        self.callback.answer.assert_called_once_with("🗑 Карточка удалена", show_alert=False)
