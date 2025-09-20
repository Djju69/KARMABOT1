"""
Test helpers and utilities for KarmaBot tests.
"""
from unittest.mock import AsyncMock, MagicMock, patch

class MockTelegramUpdate:
    """Mock Telegram update object."""
    
    def __init__(self, message_text=None, callback_data=None, user_id=12345):
        self.callback_query = AsyncMock()
        self.callback_query.data = callback_data
        self.callback_query.from_user.id = user_id
        self.callback_query.answer = AsyncMock()
        self.callback_query.message = AsyncMock()
        
        self.message = AsyncMock()
        self.message.text = message_text
        self.message.from_user.id = user_id
        self.message.answer = AsyncMock()
        self.message.reply = AsyncMock()

class MockTelegramContext:
    """Mock Telegram context object."""
    
    def __init__(self):
        self.bot = AsyncMock()
        self.args = []
        self.user_data = {}

class MockDatabase:
    """Mock database operations."""
    
    def __init__(self):
        self.delete_card = AsyncMock(return_value=True)
        self.get_card = AsyncMock(return_value={"id": 123, "title": "Test Card"})

class MockAdminService:
    """Mock admin service."""
    
    def __init__(self, is_admin=True):
        self.is_admin = MagicMock(return_value=is_admin)

class MockProfileService:
    """Mock profile service."""
    
    def __init__(self, lang='ru'):
        self.get_lang = MagicMock(return_value=lang)
