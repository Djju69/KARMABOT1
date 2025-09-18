"""Tests for admin commands."""
import logging
import pytest
from unittest.mock import MagicMock, patch
from aiogram.types import ReplyKeyboardMarkup, Message
from tests.test_utils import BaseBotTest, MockMessage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestAdminCommands(BaseBotTest):
    """Test admin commands."""
    
    @pytest.mark.asyncio
    async def test_admin_command(self, mock_message, mock_bot, fsm_context):
        """Test /admin command."""
        # Arrange
        from core.handlers import admin_cabinet
        mock_message.text = "/admin"
        
        # Act
        await admin_cabinet.open_admin_cabinet(mock_message, mock_bot, fsm_context)
        
        # Assert
        last_call = mock_message.get_last_call()
        assert last_call is not None, "message.answer was not called"
        
        # Check response text
        response_text = last_call['args'][0] if last_call['args'] else last_call['kwargs'].get('text', '')
        logger.info(f"Response text: {response_text}")
        assert "Выберите раздел:" in response_text, \
            f"Response should contain 'Выберите раздел:', got: {response_text}"
            
        # Check keyboard
        reply_markup = last_call['kwargs'].get('reply_markup')
        assert isinstance(reply_markup, ReplyKeyboardMarkup), \
            "Response should include a keyboard"
            
    @pytest.mark.asyncio
    @patch('core.handlers.admin_cabinet.db_v2')
    @patch('core.handlers.admin_cabinet._render_queue_page')
    async def test_admin_queue_command(self, mock_render, mock_db, mock_message, mock_bot, fsm_context):
        """Test /admin_queue command."""
        # Arrange
        from core.handlers import admin_cabinet
        
        # Mock database connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_db.get_connection.return_value.__enter__.return_value = mock_conn
        mock_conn.execute.return_value = mock_cursor
        mock_cursor.fetchone.return_value = (0,)  # No pending cards
        
        # Setup mock for _render_queue_page
        mock_render.return_value = None
        
        # First open admin cabinet
        mock_message.text = "/admin"
        await admin_cabinet.open_admin_cabinet(mock_message, mock_bot, fsm_context)
        mock_message.get_last_call()  # Clear the last call
        
        # Then test queue entry
        await admin_cabinet.admin_menu_queue_entry(mock_message, mock_bot, fsm_context)

        # Assert that _render_queue_page was called with correct arguments
        mock_render.assert_called_once()
        args, kwargs = mock_render.call_args
        assert args[0] == mock_message
        assert args[1] == 1  # admin_id from mock_message.from_user.id

    @pytest.mark.asyncio
    @patch('core.handlers.admin_cabinet.db_v2')
    async def test_admin_reports_command(self, mock_db, mock_message, mock_bot, fsm_context):
        """Test /admin_reports command."""
        # Arrange
        from core.handlers import admin_cabinet
        
        # Mock database connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_db.get_connection.return_value.__enter__.return_value = mock_conn
        mock_conn.execute.return_value = mock_cursor
        
        # Mock database responses for reports
        mock_cursor.fetchone.side_effect = [
            (0,),  # Total cards
            (0,),  # Pending cards
            (0,),  # Published cards
            (0,),  # Rejected cards
            (0,),  # Today's cards
            (0,),  # This week's cards
            (0,),  # This month's cards
            (0,),  # Total users
            (0,),  # Active users
        ]
        
        # First open admin cabinet
        mock_message.text = "/admin"
        await admin_cabinet.open_admin_cabinet(mock_message, mock_bot, fsm_context)
        mock_message.get_last_call()  # Clear the last call
        
        # Then test reports entry with a valid period
        mock_message.text = "📊 Отчёт за сегодня"
        await admin_cabinet.admin_menu_reports_entry(mock_message, mock_bot, fsm_context)
        
        # Assert that message.answer was called
        last_call = mock_message.get_last_call()
        assert last_call is not None, "message.answer was not called"
        
        # Check that database queries were made
        assert mock_conn.execute.call_count > 0, "Expected database queries to be executed"
