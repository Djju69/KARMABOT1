"""
Isolated tests for admin_search handler.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Test data
TEST_USER_ID = 12345

# Mock classes
class MockAdminsService:
    """Mock admins service for testing."""
    def is_admin(self, user_id):
        """Mock is_admin method."""
        return True

class MockProfileService:
    """Mock profile service for testing."""
    async def get_lang(self, user_id):
        """Mock get_lang method."""
        return "ru"

class MockSettings:
    """Mock settings for testing."""
    class Features:
        """Mock features settings."""
        moderation = True
    
    features = Features()

# Test class
class TestAdminSearchIsolated:
    """Isolated test cases for admin_search handler."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test environment."""
        # Create mocks
        self.mock_admins = MockAdminsService()
        self.mock_profile = MockProfileService()
        self.mock_settings = MockSettings()
        
        # Create callback mock
        self.callback = AsyncMock()
        self.callback.data = "adm:search"
        self.callback.from_user.id = TEST_USER_ID
        self.callback.answer = AsyncMock()
        self.callback.message = AsyncMock()
        self.callback.message.edit_text = AsyncMock()
        
        # Mock the _search_keyboard function
        self.mock_search_keyboard = MagicMock()
        
        # Import the handler with mocks
        with patch('core.handlers.admin_cabinet.admins_service', self.mock_admins), \
             patch('core.handlers.admin_cabinet.profile_service', self.mock_profile), \
             patch('core.handlers.admin_cabinet.settings', self.mock_settings), \
             patch('core.handlers.admin_cabinet._search_keyboard', self.mock_search_keyboard):
            
            # Import the handler after patching
            from core.handlers.admin_cabinet import admin_search
            self.handler = admin_search
        
        return self
    
    @pytest.mark.asyncio
    async def test_successful_search_menu(self):
        """Test successful display of search menu."""
        # Execute
        await self.handler(self.callback)
        
        # Assertions
        self.callback.answer.assert_called_once()
        assert self.callback.message.edit_text.called or self.callback.message.answer.called
    
    @pytest.mark.asyncio
    async def test_not_admin(self):
        """Test access by non-admin user."""
        # Setup
        self.mock_admins.is_admin = MagicMock(return_value=False)
        
        # Execute
        await self.handler(self.callback)
        
        # Assertions
        self.callback.answer.assert_called_once_with("❌ Доступ запрещён")
    
    @pytest.mark.asyncio
    async def test_moderation_disabled(self):
        """Test when moderation is disabled."""
        # Setup
        self.mock_settings.features.moderation = False
        
        # Execute
        await self.handler(self.callback)
        
        # Assertions
        self.callback.answer.assert_called_once_with("🚧 Модуль модерации отключён.")
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling in the handler."""
        # Setup to raise an exception
        self.mock_admins.is_admin = MagicMock(side_effect=Exception("Test error"))
        
        # Execute
        await self.handler(self.callback)
        
        # Assertions
        self.callback.answer.assert_called_once_with(
            "❌ Произошла ошибка при загрузке поиска. Пожалуйста, попробуйте ещё раз.",
            show_alert=True
        )
