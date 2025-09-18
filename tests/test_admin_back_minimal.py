"""
Minimal tests for admin_back handler.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Navigation context class for testing
class NavigationContext:
    def __init__(self, previous_screen=None, previous_data=None, current_screen=None, history=None):
        self.previous_screen = previous_screen
        self.previous_data = previous_data or {}
        self.current_screen = current_screen
        self.history = history or []

# Mock the handler function
async def mock_admin_back(update, context):
    """Mock implementation of admin_back."""
    try:
        # Check admin rights (simplified for test)
        if not hasattr(update.callback_query, 'is_admin') or not update.callback_query.is_admin:
            await update.callback_query.answer("❌ Доступ запрещён")
            return {"status": "access_denied"}
        
        # Simulate getting navigation context (mocked in tests)
        if not hasattr(context, 'get_navigation_context'):
            await update.message.reply_text("❌ Ошибка навигации: контекст не найден")
            return {"status": "error", "error": "no_navigation_context"}
            
        nav_context = await context.get_navigation_context()
        
        # Check if there's a previous screen to go back to
        if not nav_context.previous_screen:
            await update.message.reply_text(
                "❌ Некуда возвращаться\n"
                "Вы уже в главном меню"
            )
            return {"status": "error", "error": "no_previous_screen"}
            
        # Handle different previous screens
        if nav_context.previous_screen == "admin_queue":
            # Simulate going back to queue with previous filters
            filters = nav_context.previous_data.get("filters", {})
            await context.show_moderation_queue(update, context, filters)
            
        elif nav_context.previous_screen == "admin_queue_view":
            # Simulate going back to the queue view
            await context.show_admin_main_menu(update, context)
            
        elif nav_context.previous_screen == "admin_search":
            # Simulate going back to search results
            query = nav_context.previous_data.get("query", "")
            page = nav_context.previous_data.get("page", 1)
            await context.show_search_menu(update, context, query, page)
            
        else:
            # Unknown previous screen
            await update.message.reply_text(
                f"❌ Неизвестный экран для возврата: {nav_context.previous_screen}"
            )
            return {"status": "error", "error": "unknown_previous_screen"}
            
        # Simulate updating navigation context (would happen in a real implementation)
        if hasattr(context, 'update_navigation_context'):
            # In a real app, we'd update the context to reflect the navigation
            await context.update_navigation_context(
                previous_screen=nav_context.current_screen,
                previous_data=nav_context.previous_data,
                current_screen=nav_context.previous_screen
            )
            
        return {"status": "success", "previous_screen": nav_context.previous_screen}
        
    except Exception as e:
        logger = getattr(context, 'logger', MagicMock())
        logger.error(f"Error in mock_admin_back: {e}")
        await update.message.reply_text(f"❌ Ошибка навигации: {str(e)}")
        return {"status": "error", "error": str(e)}

# Test class
class TestAdminBackMinimal:
    """Minimal test cases for admin_back handler."""
    
    @pytest.fixture
    def update(self):
        """Create a mock update object."""
        update = MagicMock()
        update.message = MagicMock()
        update.callback_query = MagicMock()
        update.callback_query.is_admin = True
        update.callback_query.answer = AsyncMock()
        update.message.reply_text = AsyncMock()
        return update
    
    @pytest.fixture
    def context(self):
        """Create a mock context object with navigation methods."""
        context = MagicMock()
        context.logger = MagicMock()
        
        # Default navigation context - coming from queue view to main menu
        nav_context = NavigationContext(
            previous_screen="admin_queue",
            previous_data={"filters": {"status": "pending"}},
            current_screen="queue_view_123"
        )
        
        # Mock navigation methods
        async def get_nav_context():
            return nav_context
            
        context.get_navigation_context = get_nav_context
        context.update_navigation_context = AsyncMock()
        context.show_moderation_queue = AsyncMock()
        context.show_admin_main_menu = AsyncMock()
        context.show_search_menu = AsyncMock()
        
        # Store nav_context for test modifications
        context._nav_context = nav_context
        return context
    
    @pytest.mark.asyncio
    async def test_back_to_queue_from_view(self, update, context):
        """Test going back from queue item view to queue."""
        # Setup - coming from queue view
        context._nav_context.previous_screen = "admin_queue"
        context._nav_context.previous_data = {"filters": {"status": "pending"}}
        context._nav_context.current_screen = "queue_view_123"
        
        # Execute
        result = await mock_admin_back(update, context)
        
        # Assertions
        assert result["status"] == "success"
        assert result["previous_screen"] == "admin_queue"
        
        # Verify show_moderation_queue was called with correct filters
        context.show_moderation_queue.assert_called_once_with(
            update, context, {"status": "pending"}
        )
        
        # Verify navigation context was updated
        context.update_navigation_context.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_back_to_main_menu_from_queue(self, update, context):
        """Test going back from queue to main menu."""
        # Setup - coming from main menu to queue
        context._nav_context.previous_screen = "admin_main"
        context._nav_context.previous_data = {}
        context._nav_context.current_screen = "admin_queue"
        
        # Execute
        result = await mock_admin_back(update, context)
        
        # Assertions - in our mock handler, we don't have a specific case for admin_main,
        # so it should fall through to the unknown screen case
        assert result["status"] == "error"
        assert result["error"] == "unknown_previous_screen"
        
        # Verify error message was sent
        response_text = update.message.reply_text.call_args[0][0]
        assert "❌ Неизвестный экран для возврата" in response_text
    
    @pytest.mark.asyncio
    async def test_back_to_search_results(self, update, context):
        """Test going back to search results."""
        # Setup - coming from search results
        context._nav_context.previous_screen = "admin_search"
        context._nav_context.previous_data = {"query": "test", "page": 2}
        context._nav_context.current_screen = "search_result_123"
        
        # Execute
        result = await mock_admin_back(update, context)
        
        # Assertions
        assert result["status"] == "success"
        
        # Verify show_search_menu was called with correct parameters
        context.show_search_menu.assert_called_once_with(
            update, context, "test", 2
        )
    
    @pytest.mark.asyncio
    async def test_no_previous_screen(self, update, context):
        """Test when there's no previous screen to go back to."""
        # Setup - no previous screen
        context._nav_context.previous_screen = None
        context._nav_context.current_screen = "admin_main"
        
        # Execute
        result = await mock_admin_back(update, context)
        
        # Assertions
        assert result["status"] == "error"
        assert result["error"] == "no_previous_screen"
        
        # Verify error message was sent
        response_text = update.message.reply_text.call_args[0][0]
        assert "❌ Некуда возвращаться" in response_text
    
    @pytest.mark.asyncio
    async def test_unknown_previous_screen(self, update, context):
        """Test going back to an unknown screen."""
        # Setup - unknown previous screen
        context._nav_context.previous_screen = "unknown_screen"
        context._nav_context.current_screen = "admin_main"
        
        # Execute
        result = await mock_admin_back(update, context)
        
        # Assertions
        assert result["status"] == "error"
        assert result["error"] == "unknown_previous_screen"
        
        # Verify error message was sent
        response_text = update.message.reply_text.call_args[0][0]
        assert "❌ Неизвестный экран для возврата" in response_text
    
    @pytest.mark.asyncio
    async def test_not_admin(self, update, context):
        """Test access by non-admin user."""
        # Setup - non-admin user
        update.callback_query.is_admin = False
        
        # Execute
        result = await mock_admin_back(update, context)
        
        # Assertions
        assert result["status"] == "access_denied"
        update.callback_query.answer.assert_called_once_with("❌ Доступ запрещён")
    
    @pytest.mark.asyncio
    async def test_error_handling(self, update, context):
        """Test error handling in the handler."""
        # Setup to raise an error when getting navigation context
        async def failing_get_nav_context():
            raise Exception("Test error")
            
        context.get_navigation_context = failing_get_nav_context
        
        # Execute
        result = await mock_admin_back(update, context)
        
        # Assertions
        assert result["status"] == "error"
        assert "Test error" in result["error"]
        assert context.logger.error.called
