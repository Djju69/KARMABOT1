"""Test utilities for integration tests."""
import asyncio
import logging
import pytest
from typing import Any, Dict, Optional, List, Tuple
from unittest.mock import AsyncMock, MagicMock, patch

from aiogram import Bot, Dispatcher, types
from aiogram.types import Update, User, Chat, Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.context import FSMContext

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_mock_user(user_id: int = 1, is_admin: bool = True, is_superadmin: bool = False) -> User:
    """Create a mock user for testing."""
    return User(
        id=user_id,
        is_bot=False,
        first_name="Test",
        last_name="User",
        username=f"testuser{user_id}",
        language_code='ru',
        is_premium=False,
        _is_admin=is_admin,
        _is_superadmin=is_superadmin
    )

# For backward compatibility
MockUser = create_mock_user


class MockMessage:
    """Mock message class that tracks calls to answer()."""
    _calls: List[Dict[str, Any]] = []
    _answer_mock = AsyncMock()
    
    def __init__(self, **data):
        from datetime import datetime
        
        # Set default values
        defaults = {
            'message_id': 1,
            'date': datetime.now(),
            'chat': Chat(id=1, type='private'),
            'from_user': create_mock_user(),
            'text': "",
        }
        defaults.update(data)
        
        # Create the message instance
        self.message = Message.model_validate({
            'message_id': defaults['message_id'],
            'date': int(defaults['date'].timestamp()),
            'chat': defaults['chat'],
            'from_user': defaults['from_user'],
            'text': defaults['text'],
        })
        
        # Initialize instance-specific attributes
        self._calls = []
        self._answer_mock = AsyncMock()
        
        # Delegate attribute access to the message object
        self.__dict__.update(self.message.__dict__)
        
    @classmethod
    def reset(cls):
        """Reset mock state."""
        cls._calls = []
        cls._answer_mock = AsyncMock()
        
    def get_last_call(self) -> Optional[Dict[str, Any]]:
        """Get the last call to answer()."""
        return self._calls[-1] if self._calls else None
        
    async def answer(self, *args, **kwargs):
        """Mock answer method that tracks calls."""
        call_info = {'args': args, 'kwargs': kwargs}
        self._calls.append(call_info)
        logger.debug(f"MockMessage.answer called with args: {args}, kwargs: {kwargs}")
        return await self._answer_mock(*args, **kwargs)
        
    def __getattr__(self, name):
        """Delegate attribute access to the message object."""
        return getattr(self.message, name)


class BaseBotTest:
    """Base class for bot integration tests."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test environment."""
        # Reset mocks before each test
        MockMessage.reset()
        
        # Apply common patches
        self.patches = [
            patch('core.settings.settings.features.moderation', True),
            patch('core.settings.settings.bots.admin_id', '1'),
            patch('core.services.admins.admins_service.is_admin', AsyncMock(return_value=True)),
            patch('core.services.profile.profile_service.get_lang', AsyncMock(return_value='ru')),
        ]
        
        for p in self.patches:
            p.start()
            
        yield
        
        # Cleanup patches
        for p in self.patches:
            p.stop()
    
    @pytest.fixture
    def mock_user(self) -> User:
        """Create a mock user."""
        return create_mock_user()
        
    @pytest.fixture
    def mock_message(self, mock_user: User) -> Message:
        """Create a mock message."""
        return MockMessage(
            message_id=1,
            from_user=mock_user,
            chat=Chat(id=1, type='private'),
            text=""
        )
        
    @pytest.fixture
    def mock_bot(self) -> AsyncMock:
        """Create a mock bot."""
        bot = AsyncMock()
        return bot
        
    @pytest.fixture
    def fsm_context(self) -> FSMContext:
        """Create a mock FSM context."""
        storage = MemoryStorage()
        return FSMContext(
            storage=storage,
            key=StorageKey(bot_id=1, user_id=1, chat_id=1)
        )


def create_mock_update(
    text: str = "",
    user_id: int = 1,
    username: str = "test_user",
    chat_id: int = 1,
    message_id: int = 1,
    callback_data: Optional[str] = None,
) -> Update:
    """Create a mock Update object for testing."""
    user = User(
        id=user_id,
        is_bot=False,
        first_name="Test",
        last_name="User",
        username=username,
        language_code="en",
    )
    
    chat = Chat(id=chat_id, type="private")
    
    if callback_data:
        return Update(
            update_id=1,
            callback_query=types.CallbackQuery(
                id="123",
                from_user=user,
                chat_instance="test",
                data=callback_data,
                message=types.Message(
                    message_id=message_id,
                    date=0,
                    chat=chat,
                ),
            ),
        )
    
    return Update(
        update_id=1,
        message=types.Message(
            message_id=message_id,
            from_user=user,
            chat=chat,
            date=0,
            text=text,
        ),
    )


async def process_update(
    dp: Dispatcher, 
    update: Update, 
    bot: Optional[Bot] = None
) -> str:
    """Process an update and return the bot's response."""
    if bot is None:
        bot = AsyncMock(spec=Bot)
        bot.get_my_commands = AsyncMock(return_value=[])
    
    # Mock the send_message method to capture responses
    responses = []
    
    async def mock_send_message(chat_id: int, text: str, **kwargs) -> types.Message:
        responses.append(text)
        return types.Message(
            message_id=1,
            date=0,
            chat=types.Chat(id=chat_id, type="private"),
            text=text,
        )
    
    bot.send_message = mock_send_message
    
    # Process the update
    await dp.feed_update(bot=bot, update=update)
    
    # Return the last response or an empty string if no responses
    return responses[-1] if responses else ""


def create_mock_bot() -> AsyncMock:
    """Create a mock Bot instance for testing."""
    bot = AsyncMock(spec=Bot)
    bot.get_my_commands = AsyncMock(return_value=[])
    bot.send_message = AsyncMock()
    bot.answer_callback_query = AsyncMock()
    return bot
