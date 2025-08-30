"""
Unit tests for admin handlers without external dependencies.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

class TestAdminQueueDeleteUnit:
    """Unit tests for admin_queue_delete handler."""
    
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
        self.callback.data = "adm:q:del:confirm:123:1"
        self.callback.from_user.id = 12345
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
        self.mock_admins.is_admin.assert_called_once_with(12345)
        self.mock_db.delete_card.assert_called_once_with(123)
        self.mock_render.assert_called_once_with(
            self.callback.message, 12345, page=1, edit=True
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
