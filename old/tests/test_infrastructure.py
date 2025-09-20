"""
Test infrastructure verification.

This test verifies that the test infrastructure is working correctly.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

class TestInfrastructure:
    """Test cases for verifying the test infrastructure."""
    
    @pytest.mark.asyncio
    async def test_async_mocks(self):
        """Test that async mocks work correctly."""
        mock = AsyncMock()
        mock.return_value = "test"
        
        result = await mock()
        assert result == "test"
        mock.assert_awaited_once()
    
    def test_sync_mocks(self):
        """Test that sync mocks work correctly."""
        mock = MagicMock()
        mock.some_method.return_value = 42
        
        result = mock.some_method()
        assert result == 42
        mock.some_method.assert_called_once()
    
    def test_patching(self):
        """Test that patching works correctly."""
        class TestClass:
            def method(self):
                return "original"
        
        test_obj = TestClass()
        assert test_obj.method() == "original"
        
        with patch.object(TestClass, 'method', return_value="mocked"):
            assert test_obj.method() == "mocked"
        
        assert test_obj.method() == "original"

class TestMockTelegramUpdate:
    """Test the MockTelegramUpdate helper class."""
    
    @pytest.mark.asyncio
    async def test_callback_query(self):
        """Test callback query handling."""
        from tests.test_helpers import MockTelegramUpdate
        
        update = MockTelegramUpdate(callback_data="test:data", user_id=12345)
        
        assert update.callback_query.data == "test:data"
        assert update.callback_query.from_user.id == 12345
        
        await update.callback_query.answer("Test")
        update.callback_query.answer.assert_awaited_once_with("Test")
    
    @pytest.mark.asyncio
    async def test_message(self):
        """Test message handling."""
        from tests.test_helpers import MockTelegramUpdate
        
        update = MockTelegramUpdate(message_text="Hello, world!", user_id=54321)
        
        assert update.message.text == "Hello, world!"
        assert update.message.from_user.id == 54321
        
        await update.message.answer("Reply")
        update.message.answer.assert_awaited_once_with("Reply")

class TestMockDatabase:
    """Test the MockDatabase helper class."""
    
    @pytest.mark.asyncio
    async def test_delete_card(self):
        """Test delete_card method."""
        from tests.test_helpers import MockDatabase
        
        db = MockDatabase()
        result = await db.delete_card(123)
        
        assert result is True
        db.delete_card.assert_awaited_once_with(123)
    
    @pytest.mark.asyncio
    async def test_get_card(self):
        """Test get_card method."""
        from tests.test_helpers import MockDatabase
        
        db = MockDatabase()
        result = await db.get_card(123)
        
        assert result == {"id": 123, "title": "Test Card"}
        db.get_card.assert_awaited_once_with(123)
