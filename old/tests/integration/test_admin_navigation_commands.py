"""Тесты для команд админ-панели, связанных с поиском и навигацией."""
import logging
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram.types import CallbackQuery, Message, User, Chat, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext

from tests.test_utils import create_mock_user, BaseBotTest, MockMessage

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestAdminNavigationCommands(BaseBotTest):
    """Тесты для команд админ-панели, связанных с поиском и навигацией."""

    @pytest.mark.asyncio
    @patch('core.handlers.admin_cabinet.db_v2')
    async def test_admin_search(self, mock_db, mock_bot):
        """Тест функции поиска в админ-панели."""
        from core.handlers import admin_cabinet
        
        # Настройка моков
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_db.get_connection.return_value.__enter__.return_value = mock_conn
        mock_conn.execute.return_value = mock_cursor
        
        # Create a mock user
        user = MagicMock()
        user.id = 12345
        
        # Create a mock message
        message = MockMessage()
        
        # Create a mock callback with from_user
        callback = AsyncMock(spec=CallbackQuery)
        callback.from_user = user
        callback.message = message
        callback.data = 'adm:search'
        
        # Вызываем обработчик
 # Mock the router handler
        with patch('core.handlers.admin_cabinet.router') as mock_router:
            # Call the handler directly
            await admin_cabinet.admin_search(callback)
        
        # Проверяем, что был вызван edit_text с клавиатурой поиска
        callback.message.edit_text.assert_called_once()
        args, kwargs = callback.message.edit_text.call_args
        assert 'поиска' in kwargs['text'].lower(), \
            "Должно быть сообщение о выборе типа поиска"
        assert 'reply_markup' in kwargs, "Должна быть клавиатура с опциями поиска"

    @pytest.mark.asyncio
    @patch('core.handlers.admin_cabinet.db_v2')
    async def test_admin_search_by_status(self, mock_db, mock_bot):
        """Тест поиска карточек по статусу."""
        from core.handlers import admin_cabinet
        
        # Настройка моков
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_db.get_connection.return_value.__enter__.return_value = mock_conn
        mock_conn.execute.return_value = mock_cursor
        
        # Мок данных карточек
        mock_cursor.fetchall.return_value = [
            {'id': 1, 'title': 'Карточка 1', 'status': 'pending'},
            {'id': 2, 'title': 'Карточка 2', 'status': 'pending'}
        ]
        
        # Create a mock user
        user = MagicMock()
        user.id = 12345
        
        # Create a mock message
        message = MockMessage()
        
        # Create a mock callback with from_user
        callback = AsyncMock(spec=CallbackQuery)
        callback.from_user = user
        callback.message = message
        callback.data = 'adm:search:status:pending'  # Поиск по статусу 'pending'
        
        # Вызываем обработчик
 # Mock the router handler
        with patch('core.handlers.admin_cabinet.router') as mock_router:
            # Call the handler directly
            await admin_cabinet.admin_search_by_status(callback)
        
        # Проверяем, что был вызван edit_text с результатами поиска
        callback.message.edit_text.assert_called_once()
        args, kwargs = callback.message.edit_text.call_args
        assert 'найдено' in kwargs['text'].lower(), \
            "Должно быть сообщение с количеством найденных карточек"

    @pytest.mark.asyncio
    @patch('core.handlers.admin_cabinet.db_v2')
    async def test_admin_back(self, mock_db, mock_bot):
        """Тест возврата в главное меню админ-панели."""
        from core.handlers import admin_cabinet
        
        # Create a mock user
        user = MagicMock()
        user.id = 12345
        
        # Create a mock message
        message = MockMessage()
        
        # Create a mock callback with from_user
        callback = AsyncMock(spec=CallbackQuery)
        callback.from_user = user
        callback.message = message
        callback.data = 'adm:back'
        
        # Create a mock FSMContext
        fsm_context = MagicMock(spec=FSMContext)
        
        # Вызываем обработчик
 # Mock the router handler
        with patch('core.handlers.admin_cabinet.router') as mock_router:
            # Call the handler directly with the fsm_context
            await admin_cabinet.admin_back(callback, fsm_context=fsm_context)
        
        # Проверяем, что состояние сброшено
        fsm_context.clear.assert_called_once()
        
        # Проверяем, что было отправлено сообщение с главным меню
        callback.message.answer.assert_called_once()
        args, kwargs = callback.message.answer.call_args
        assert 'выберите раздел' in kwargs['text'].lower(), \
            "Должно быть сообщение с главным меню"
