"""Тесты для команд админ-панели, связанных с очередью модерации."""
import logging
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram.types import CallbackQuery, Message, User, Chat
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command

from tests.test_utils import create_mock_user, BaseBotTest, MockMessage

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestAdminQueueCommands(BaseBotTest):
    """Тесты для команд админ-панели, связанных с очередью модерации."""

    @pytest.fixture
    def mock_handlers(self):
        # Импортируем здесь, чтобы избежать циклического импорта
        from core.handlers import admin_cabinet
        return admin_cabinet

    @pytest.fixture
    def mock_router(self, mock_handlers):
        return mock_handlers.router

    @pytest.mark.asyncio
    @patch('core.handlers.admin_cabinet.db_v2')
    @patch('core.handlers.admin_cabinet.admins_service')
    @patch('core.handlers.admin_cabinet.settings')
    async def test_admin_queue_view(self, mock_settings, mock_admins_service, mock_db, mock_bot):
        """Тест просмотра карточки в очереди модерации."""
        from core.handlers import admin_cabinet
        
        # Настройка моков
        mock_settings.features.moderation = True
        mock_admins_service.is_admin.return_value = True
        
        # Мок для базы данных
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_db.get_connection.return_value.__enter__.return_value = mock_conn
        mock_conn.execute.return_value = mock_cursor
        
        # Мок данных карточки
        mock_cursor.fetchone.return_value = {
            'id': 1,
            'title': 'Тестовая карточка',
            'description': 'Описание тестовой карточки',
            'status': 'pending',
            'created_at': '2023-01-01 12:00:00',
            'updated_at': '2023-01-01 12:00:00',
            'partner_id': 123
        }
        
        # Создаем мок для callback_query
        user = MagicMock()
        user.id = 12345
        
        message = MockMessage()
        
        callback = AsyncMock(spec=CallbackQuery)
        callback.from_user = user
        callback.message = message
        callback.data = 'adm:q:view:1:0'  # card_id=1, page=0
        
        # Получаем обработчик из модуля
        handler = getattr(admin_cabinet, 'admin_queue_view', None)
        if not handler:
            pytest.fail("Handler for admin_queue_view not found")
        
        # Вызываем обработчик
        await handler(callback)
        
        # Проверяем, что был вызван edit_text с правильными параметрами
        callback.message.edit_text.assert_called_once()
        args, kwargs = callback.message.edit_text.call_args
        assert 'text' in kwargs, "В вызове отсутствует параметр text"
        assert 'Тестовая карточка' in kwargs['text'], "Неверное содержимое карточки"

    @pytest.mark.asyncio
    @patch('core.handlers.admin_cabinet.db_v2')
    @patch('core.handlers.admin_cabinet.admins_service')
    @patch('core.handlers.admin_cabinet.settings')
    async def test_admin_queue_approve(self, mock_settings, mock_admins_service, mock_db):
        """Тест одобрения карточки в очереди модерации."""
        from core.handlers import admin_cabinet
        
        # Настройка моков
        mock_settings.features.moderation = True
        mock_admins_service.is_admin.return_value = True
        
        # Мок для базы данных
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_db.get_connection.return_value.__enter__.return_value = mock_conn
        mock_conn.execute.return_value = mock_cursor
        
        # Мок данных карточки
        mock_cursor.fetchone.return_value = {
            'id': 1,
            'title': 'Тестовая карточка',
            'status': 'pending',
            'partner_id': 123
        }
        
        # Создаем мок для callback_query
        user = MagicMock()
        user.id = 12345
        
        message = MockMessage()
        
        callback = AsyncMock(spec=CallbackQuery)
        callback.from_user = user
        callback.message = message
        callback.data = 'adm:q:approve:1:0'  # card_id=1, page=0
        
        # Получаем обработчик из модуля
        handler = getattr(admin_cabinet, 'admin_queue_approve', None)
        if not handler:
            pytest.fail("Handler for admin_queue_approve not found")
        
        # Вызываем обработчик
        await handler(callback)
        
        # Проверяем, что был вызван edit_text с сообщением об успешном одобрении
        callback.message.edit_text.assert_called_once()
        args, kwargs = callback.message.edit_text.call_args
        assert 'одобрена' in kwargs['text'].lower(), \
            "Должно быть сообщение об успешном одобрении"

    @pytest.mark.asyncio
    @patch('core.handlers.admin_cabinet.db_v2')
    @patch('core.handlers.admin_cabinet.admins_service')
    @patch('core.handlers.admin_cabinet.settings')
    async def test_admin_queue_reject(self, mock_settings, mock_admins_service, mock_db):
        """Тест отклонения карточки в очереди модерации."""
        from core.handlers import admin_cabinet
        
        # Настройка моков
        mock_settings.features.moderation = True
        mock_admins_service.is_admin.return_value = True
        
        # Мок для базы данных
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_db.get_connection.return_value.__enter__.return_value = mock_conn
        mock_conn.execute.return_value = mock_cursor
        
        # Мок данных карточки
        mock_cursor.fetchone.return_value = {
            'id': 1,
            'title': 'Тестовая карточка',
            'status': 'pending',
            'partner_id': 123
        }
        
        # Создаем мок для callback_query
        user = MagicMock()
        user.id = 12345
        
        message = MockMessage()
        
        callback = AsyncMock(spec=CallbackQuery)
        callback.from_user = user
        callback.message = message
        callback.data = 'adm:q:reject:1:0'  # card_id=1, page=0
        
        # Получаем обработчик из модуля
        handler = getattr(admin_cabinet, 'admin_queue_reject', None)
        if not handler:
            pytest.fail("Handler for admin_queue_reject not found")
        
        # Вызываем обработчик
        await handler(callback)
        
        # Проверяем, что был вызван edit_text с сообщением об отклонении
        callback.message.edit_text.assert_called_once()
        args, kwargs = callback.message.edit_text.call_args
        assert 'отклонена' in kwargs['text'].lower(), \
            "Должно быть сообщение об отклонении"
