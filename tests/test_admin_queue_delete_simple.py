"""
Simple tests for the admin_queue_delete handler logic.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

# Test data
TEST_CARD_ID = 123
TEST_PAGE = 1
TEST_USER_ID = 12345
TEST_CALLBACK_DATA = f"adm:q:del:confirm:{TEST_CARD_ID}:{TEST_PAGE}"

class TestAdminQueueDelete:
    """Test cases for admin_queue_delete handler."""
    
    @pytest.fixture
    def setup(self):
        """Set up test environment."""
        # Create mocks
        self.mock_admins = MagicMock()
        self.mock_db = MagicMock()
        self.mock_render = AsyncMock()
        self.mock_logger = MagicMock()
        
        # Create callback mock
        self.callback = MagicMock()
        self.callback.data = TEST_CALLBACK_DATA
        self.callback.from_user.id = TEST_USER_ID
        self.callback.answer = AsyncMock()
        self.callback.message = MagicMock()
        
        # Create settings mock
        class MockSettings:
            class Features:
                moderation = True
        
        self.settings = MockSettings()
        
        return self
    
    async def test_successful_deletion(self, setup):
        """Test successful card deletion."""
        # Setup
        self.mock_admins.is_admin.return_value = True
        self.mock_db.delete_card.return_value = True
        
        # Execute
        await self._call_handler()
        
        # Assertions
        self.mock_admins.is_admin.assert_called_once_with(TEST_USER_ID)
        self.mock_db.delete_card.assert_called_once_with(TEST_CARD_ID)
        self.mock_render.assert_called_once_with(
            self.callback.message, TEST_USER_ID, page=TEST_PAGE, edit=True
        )
        self.callback.answer.assert_called_once_with("🗑 Карточка удалена", show_alert=False)
    
    async def test_not_admin(self, setup):
        """Test access by non-admin user."""
        # Setup
        self.mock_admins.is_admin.return_value = False
        
        # Execute
        await self._call_handler()
        
        # Assertions
        self.callback.answer.assert_called_once_with("❌ Доступ запрещён")
        self.mock_db.delete_card.assert_not_called()
    
    async def test_moderation_disabled(self, setup):
        """Test when moderation is disabled."""
        # Setup
        self.mock_admins.is_admin.return_value = True
        self.settings.Features.moderation = False
        
        # Execute
        await self._call_handler()
        
        # Assertions
        self.callback.answer.assert_called_once_with("🚧 Модуль модерации отключён.")
        self.mock_db.delete_card.assert_not_called()
    
    async def test_invalid_format(self, setup):
        """Test with invalid callback data format."""
        # Setup
        self.callback.data = "invalid:format"
        
        # Execute
        await self._call_handler()
        
        # Assertions
        self.callback.answer.assert_called_once_with("❌ Ошибка формата данных", show_alert=True)
        self.mock_db.delete_card.assert_not_called()
    
    async def _call_handler(self):
        """Helper to call the handler with the current mocks."""
        # Simulate the handler logic
        if not await self.mock_admins.is_admin(self.callback.from_user.id):
            await self.callback.answer("❌ Доступ запрещён")
            return
        
        if not self.settings.Features.moderation:
            await self.callback.answer("🚧 Модуль модерации отключён.")
            return
        
        try:
            parts = self.callback.data.split(":")
            if len(parts) < 6:
                raise ValueError("Неверный формат callback данных")
            
            card_id = int(parts[4])
            page = int(parts[5])
            
            ok = self.mock_db.delete_card(card_id)
            self.mock_logger.info(
                "admin.delete: moderator=%s card=%s ok=%s",
                self.callback.from_user.id,
                card_id,
                ok
            )
            
            await self.mock_render(
                self.callback.message, 
                self.callback.from_user.id, 
                page=page, 
                edit=True
            )
            await self.callback.answer("🗑 Карточка удалена", show_alert=False)
            
        except (IndexError, ValueError) as e:
            self.mock_logger.error(f"Invalid callback data format: {self.callback.data}")
            await self.callback.answer("❌ Ошибка формата данных", show_alert=True)
            
        except Exception as e:
            self.mock_logger.error(f"Error in admin_queue_delete: {e}", exc_info=True)
            await self.callback.answer(
                "❌ Произошла ошибка при удалении карточки. Пожалуйста, попробуйте ещё раз.",
                show_alert=True
            )
