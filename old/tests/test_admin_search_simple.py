"""
Simple tests for admin_search handler.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Test data
TEST_USER_ID = 12345

# Mock the handler function
async def mock_admin_search(callback, context):
    """Mock implementation of admin_search."""
    # This is a simplified version of the handler for testing
    try:
        # Check admin rights
        if not await admins_service.is_admin(callback.from_user.id):
            await callback.answer("❌ Доступ запрещён")
            return {
                "status": "error",
                "error": "access_denied"
            }
            
        # Check moderation feature
        if not settings.features.moderation:
            await callback.answer("🚧 Модуль модерации отключён.")
            return {
                "status": "error",
                "error": "moderation_disabled"
            }
            
        # Get user language
        lang = await profile_service.get_lang(callback.from_user.id)
        
        # Return success response with search menu
        return {
            "status": "success",
            "user_id": callback.from_user.id,
            "lang": lang
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

# Test class
class TestAdminSearchSimple:
    """Simple test cases for admin_search handler."""
    
    @pytest.fixture
    def callback(self):
        """Create a mock callback object."""
        callback = AsyncMock()
        callback.data = "adm:search"
        callback.from_user.id = TEST_USER_ID
        callback.answer = AsyncMock()
        callback.message = AsyncMock()
        callback.message.edit_text = AsyncMock()
        return callback
    
    @pytest.mark.asyncio
    async def test_successful_search_menu(self, callback):
        """Test successful display of search menu."""
        # Mock dependencies
        mock_admins = MagicMock()
        mock_admins.is_admin = AsyncMock(return_value=True)
        
        mock_settings = MagicMock()
        mock_settings.features.moderation = True
        
        mock_profile = MagicMock()
        mock_profile.get_lang = AsyncMock(return_value="ru")
        
        # Patch dependencies
        with patch('core.handlers.admin_cabinet.admins_service', mock_admins), \
             patch('core.handlers.admin_cabinet.settings', mock_settings), \
             patch('core.handlers.admin_cabinet.profile_service', mock_profile):
            
            # Import the handler after patching
            from core.handlers.admin_cabinet import admin_search
            
            # Execute
            await admin_search(callback)
            
            # Assertions
            mock_admins.is_admin.assert_called_once_with(TEST_USER_ID)
            mock_profile.get_lang.assert_called_once_with(TEST_USER_ID)
            callback.answer.assert_called_once()
            assert callback.message.edit_text.called or callback.message.answer.called
    
    @pytest.mark.asyncio
    async def test_not_admin(self, callback):
        """Test access by non-admin user."""
        # Setup
        mock_admins = MagicMock()
        mock_admins.is_admin = AsyncMock(return_value=False)
        
        with patch('core.handlers.admin_cabinet.admins_service', mock_admins):
            # Import the handler after patching
            from core.handlers.admin_cabinet import admin_search
            
            # Execute
            await admin_search(callback)
            
            # Assertions
            callback.answer.assert_called_once_with("❌ Доступ запрещён")
    
    @pytest.mark.asyncio
    async def test_moderation_disabled(self, callback):
        """Test when moderation is disabled."""
        # Setup
        mock_admins = MagicMock()
        mock_admins.is_admin = AsyncMock(return_value=True)
        
        mock_settings = MagicMock()
        mock_settings.features.moderation = False
        
        with patch('core.handlers.admin_cabinet.admins_service', mock_admins), \
             patch('core.handlers.admin_cabinet.settings', mock_settings):
            
            # Import the handler after patching
            from core.handlers.admin_cabinet import admin_search
            
            # Execute
            await admin_search(callback)
            
            # Assertions
            callback.answer.assert_called_once_with("🚧 Модуль модерации отключён.")
    
    @pytest.mark.asyncio
    async def test_error_handling(self, callback):
        """Test error handling in the handler."""
        # Setup to raise an exception
        mock_admins = MagicMock()
        mock_admins.is_admin = AsyncMock(side_effect=Exception("Test error"))
        
        with patch('core.handlers.admin_cabinet.admins_service', mock_admins), \
             patch('core.handlers.admin_cabinet.logger') as mock_logger:
            
            # Import the handler after patching
            from core.handlers.admin_cabinet import admin_search
            
            # Execute
            await admin_search(callback)
            
            # Assertions
            mock_logger.error.assert_called()
            callback.answer.assert_called_once_with(
                "❌ Произошла ошибка при загрузке поиска. Пожалуйста, попробуйте ещё раз.",
                show_alert=True
            )
