"""
Tests for the admin_queue_delete handler.
"""
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Set up test environment
os.environ["BOT_TOKEN"] = "test_token"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

# Mock settings before importing any application code
class MockSettings:
    class Features:
        moderation = True
        partner_fsm = True
    
    class Bots:
        admin_id = 12345

# Apply mocks
import sys
sys.modules['core.settings'] = MagicMock()
sys.modules['core.settings'].settings = MockSettings()
sys.modules['core.settings'].settings.features = MockSettings.Features()
sys.modules['core.settings'].settings.bots = MockSettings.Bots()

# Now import the handler
from core.handlers.admin_cabinet import admin_queue_delete

# Test fixtures
@pytest.fixture
def mock_callback():
    """Create a mock CallbackQuery object."""
    class MockCallbackQuery:
        def __init__(self, data):
            self.data = data
            self.from_user = MagicMock(id=12345)  # Admin user
            self.answer = AsyncMock()
            self.message = MagicMock()
            self.message.edit_text = AsyncMock()
            self.message.answer = AsyncMock()
    
    return MockCallbackQuery("adm:q:del:confirm:123:1")  # card_id=123, page=1

# Test cases
@pytest.mark.asyncio
async def test_admin_queue_delete_success(mock_callback):
    """Test successful card deletion from moderation queue."""
    # Setup mocks
    with patch('core.handlers.admin_cabinet.admins_service') as mock_admins, \
         patch('core.handlers.admin_cabinet.db_v2') as mock_db, \
         patch('core.handlers.admin_cabinet._render_queue_page') as mock_render:
        
        # Configure mocks
        mock_admins.is_admin.return_value = True
        mock_db.delete_card.return_value = True
        
        # Execute
        await admin_queue_delete(mock_callback)
        
        # Assertions
        mock_admins.is_admin.assert_called_once_with(12345)
        mock_db.delete_card.assert_called_once_with(123)
        mock_render.assert_called_once_with(mock_callback.message, 12345, page=1, edit=True)
        mock_callback.answer.assert_called_once_with("🗑 Карточка удалена", show_alert=False)

@pytest.mark.asyncio
async def test_admin_queue_delete_not_admin(mock_callback):
    """Test deletion attempt by non-admin user."""
    # Setup mocks
    with patch('core.handlers.admin_cabinet.admins_service') as mock_admins:
        # Configure mocks
        mock_admins.is_admin.return_value = False
        
        # Execute
        await admin_queue_delete(mock_callback)
        
        # Assertions
        mock_callback.answer.assert_called_once_with("❌ Доступ запрещён")
        mock_admins.is_admin.assert_called_once_with(12345)

@pytest.mark.asyncio
async def test_admin_queue_delete_moderation_disabled(mock_callback):
    """Test deletion attempt when moderation is disabled."""
    # Save original value
    original_value = sys.modules['core.settings'].settings.features.moderation
    
    try:
        # Setup test
        sys.modules['core.settings'].settings.features.moderation = False
        
        # Execute
        await admin_queue_delete(mock_callback)
        
        # Assertions
        mock_callback.answer.assert_called_once_with("🚧 Модуль модерации отключён.")
    finally:
        # Restore original value
        sys.modules['core.settings'].settings.features.moderation = original_value

@pytest.mark.asyncio
async def test_admin_queue_delete_invalid_format(mock_callback):
    """Test deletion with invalid callback data format."""
    # Setup
    mock_callback.data = "invalid:format"
    
    # Execute
    await admin_queue_delete(mock_callback)
    
    # Assertions
    mock_callback.answer.assert_called_once_with("❌ Ошибка формата данных", show_alert=True)

if __name__ == "__main__":
    pytest.main(["-v", __file__])
