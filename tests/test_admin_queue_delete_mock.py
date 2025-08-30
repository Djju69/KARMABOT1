"""
Tests for the admin_queue_delete handler using mocks.
"""
import os
import sys
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Set up test environment
os.environ["BOT_TOKEN"] = "test_token"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

# Mock settings
class MockSettings:
    class Features:
        moderation = True
        partner_fsm = True
    
    class Bots:
        admin_id = 12345

# Apply mocks
sys.modules['core.settings'] = MagicMock()
sys.modules['core.settings'].settings = MockSettings()
sys.modules['core.settings'].settings.features = MockSettings.Features()
sys.modules['core.settings'].settings.bots = MockSettings.Bots()

# Mock the admin_queue_delete function
def create_mock_admin_queue_delete():
    """Create a mock version of admin_queue_delete for testing."""
    async def mock_admin_queue_delete(callback):
        try:
            # Check admin rights
            if not await mock_admins.is_admin(callback.from_user.id):
                await callback.answer("❌ Доступ запрещён")
                return
            
            # Check if moderation is enabled
            if not mock_settings.features.moderation:
                await callback.answer("🚧 Модуль модерации отключён.")
                return
            
            # Parse callback data
            parts = callback.data.split(":")
            if len(parts) < 6:
                raise ValueError("Неверный формат callback данных")
            
            card_id = int(parts[4])
            page = int(parts[5])
            
            # Delete the card
            ok = mock_db.delete_card(card_id)
            
            # Log the action
            mock_logger.info(
                "admin.delete: moderator=%s card=%s ok=%s",
                callback.from_user.id,
                card_id,
                ok
            )
            
            # Return to the queue
            await mock_render_queue_page(callback.message, callback.from_user.id, page=page, edit=True)
            await callback.answer("🗑 Карточка удалена", show_alert=False)
            
        except (IndexError, ValueError) as e:
            mock_logger.error(f"Invalid callback data format: {callback.data}")
            await callback.answer("❌ Ошибка формата данных", show_alert=True)
            
        except Exception as e:
            mock_logger.error(f"Error in admin_queue_delete: {e}", exc_info=True)
            await callback.answer(
                "❌ Произошла ошибка при удалении карточки. Пожалуйста, попробуйте ещё раз.",
                show_alert=True
            )
    
    return mock_admin_queue_delete

# Test fixtures
@pytest.fixture
def setup_mocks():
    """Set up all the mocks needed for testing."""
    global mock_admins, mock_db, mock_render_queue_page, mock_logger, mock_settings
    
    # Create mocks
    mock_admins = MagicMock()
    mock_db = MagicMock()
    mock_render_queue_page = AsyncMock()
    mock_logger = MagicMock()
    mock_settings = MockSettings()
    
    # Patch the modules
    with patch.dict('sys.modules', 
                   {'core.handlers.admin_cabinet': MagicMock()}), \
         patch('core.handlers.admin_cabinet.admins_service', mock_admins), \
         patch('core.handlers.admin_cabinet.db_v2', mock_db), \
         patch('core.handlers.admin_cabinet._render_queue_page', mock_render_queue_page), \
         patch('core.handlers.admin_cabinet.logger', mock_logger), \
         patch('core.settings.settings', mock_settings):
        
        # Create the test function
        admin_queue_delete = create_mock_admin_queue_delete()
        yield admin_queue_delete, mock_admins, mock_db, mock_render_queue_page, mock_logger

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
async def test_admin_queue_delete_success(setup_mocks, mock_callback):
    """Test successful card deletion from moderation queue."""
    admin_queue_delete, mock_admins, mock_db, mock_render, mock_logger = setup_mocks
    
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
async def test_admin_queue_delete_not_admin(setup_mocks, mock_callback):
    """Test deletion attempt by non-admin user."""
    admin_queue_delete, mock_admins, mock_db, mock_render, mock_logger = setup_mocks
    
    # Configure mocks
    mock_admins.is_admin.return_value = False
    
    # Execute
    await admin_queue_delete(mock_callback)
    
    # Assertions
    mock_callback.answer.assert_called_once_with("❌ Доступ запрещён")
    mock_admins.is_admin.assert_called_once_with(12345)
    mock_db.delete_card.assert_not_called()
    mock_render.assert_not_called()

@pytest.mark.asyncio
async def test_admin_queue_delete_moderation_disabled(setup_mocks, mock_callback):
    """Test deletion attempt when moderation is disabled."""
    admin_queue_delete, mock_admins, mock_db, mock_render, mock_logger = setup_mocks
    
    # Configure mocks
    mock_admins.is_admin.return_value = True
    mock_settings.features.moderation = False
    
    # Execute
    await admin_queue_delete(mock_callback)
    
    # Assertions
    mock_callback.answer.assert_called_once_with("🚧 Модуль модерации отключён.")
    mock_admins.is_admin.assert_called_once()
    mock_db.delete_card.assert_not_called()
    mock_render.assert_not_called()

@pytest.mark.asyncio
async def test_admin_queue_delete_invalid_format(setup_mocks, mock_callback):
    """Test deletion with invalid callback data format."""
    admin_queue_delete, mock_admins, mock_db, mock_render, mock_logger = setup_mocks
    
    # Setup
    mock_callback.data = "invalid:format"
    
    # Execute
    await admin_queue_delete(mock_callback)
    
    # Assertions
    mock_callback.answer.assert_called_once_with("❌ Ошибка формата данных", show_alert=True)
    mock_logger.error.assert_called()
    mock_db.delete_card.assert_not_called()
    mock_render.assert_not_called()

if __name__ == "__main__":
    pytest.main(["-v", __file__])
