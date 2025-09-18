"""
Minimal test to verify the test infrastructure works.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

class TestMinimal:
    """Minimal test cases to verify test infrastructure."""
    
    @pytest.mark.asyncio
    async def test_minimal_async(self):
        """Test that async tests work."""
        mock = AsyncMock()
        mock.return_value = "test"
        
        result = await mock()
        assert result == "test"
        mock.assert_awaited_once()
    
    def test_minimal_sync(self):
        """Test that sync tests work."""
        assert 1 + 1 == 2
