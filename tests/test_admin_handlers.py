"""
Simplified tests for admin panel handlers.
"""
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Mock environment variables
os.environ["BOT_TOKEN"] = "test_token"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

# Mock settings before importing any application code
from unittest.mock import MagicMock
import sys

class MockSettings:
    class Features:
        moderation = True
        partner_fsm = True
    
    class Bots:
        admin_id = 12345

sys.modules['core.settings'] = MagicMock()
sys.modules['core.settings'].settings = MockSettings()
sys.modules['core.settings'].settings.features = MockSettings.Features()
sys.modules['core.settings'].settings.bots = MockSettings.Bots()

# Mock the aiogram imports
class MockMessage:
    def __init__(self, message_id=1, chat=None, from_user=None):
        self.message_id = message_id
        self.chat = chat or MagicMock(id=123)
        self.from_user = from_user or MagicMock(id=123)
        self.edit_text = AsyncMock()
        self.answer = AsyncMock()
        self.reply = AsyncMock()

class MockCallbackQuery:
    def __init__(self, data, message=None, from_user=None):
        self.data = data
        self.message = message or MockMessage()
        self.from_user = from_user or MagicMock(id=123)
        self.answer = AsyncMock()

# Test cases for admin_queue_delete
@pytest.mark.asyncio
async def test_admin_queue_delete_success():
    """Test successful card deletion from moderation queue."""
    # Setup
    from core.handlers.admin_cabinet import admin_queue_delete
    
    # Create test data
    callback = MockCallbackQuery("adm:q:del:confirm:123:1")  # card_id=123, page=1
    
    # Mock dependencies
    with patch('core.handlers.admin_cabinet.admins_service') as mock_admins, \
         patch('core.handlers.admin_cabinet.settings') as mock_settings, \
         patch('core.handlers.admin_cabinet.db_v2') as mock_db, \
         patch('core.handlers.admin_cabinet._render_queue_page') as mock_render:
        
        # Configure mocks
        mock_admins.is_admin.return_value = True
        mock_settings.features.moderation = True
        mock_db.delete_card.return_value = True
        
        # Execute
        await admin_queue_delete(callback)
        
        # Assertions
        mock_db.delete_card.assert_called_once_with(123)
        mock_render.assert_called_once()
        callback.answer.assert_called_once_with("🗑 Карточка удалена", show_alert=False)

# Test cases for admin_search
@pytest.mark.asyncio
async def test_admin_search_success():
    """Test successful admin search initialization."""
    # Setup
    from core.handlers.admin_cabinet import admin_search
    
    # Create test data
    callback = MockCallbackQuery("adm:search")
    
    # Mock dependencies
    with patch('core.handlers.admin_cabinet.admins_service') as mock_admins, \
         patch('core.handlers.admin_cabinet.settings') as mock_settings, \
         patch('core.handlers.admin_cabinet.profile_service') as mock_profile, \
         patch('core.handlers.admin_cabinet.get_text') as mock_get_text, \
         patch('core.handlers.admin_cabinet._search_keyboard') as mock_keyboard:
        
        # Configure mocks
        mock_admins.is_admin.return_value = True
        mock_settings.features.moderation = True
        mock_profile.get_lang.return_value = 'ru'
        mock_get_text.return_value = 'Search menu'
        mock_keyboard.return_value = 'test_keyboard'
        
        # Execute
        await admin_search(callback)
        
        # Assertions
        callback.message.edit_text.assert_called_once()
        mock_keyboard.assert_called_once()

if __name__ == "__main__":
    pytest.main(["-v", __file__])
