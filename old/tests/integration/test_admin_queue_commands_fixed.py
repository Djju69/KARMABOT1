"""Тесты для команд админ-панели, связанных с очередью модерации."""
import logging
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, ANY
from aiogram.types import CallbackQuery, Message, User, Chat
from aiogram.fsm.context import FSMContext

from tests.test_utils import create_mock_user, BaseBotTest, MockMessage

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestAdminQueueCommands:
    """Тесты для команд админ-панели, связанных с очередью модерации."""

    @pytest.fixture(autouse=True)
    def setup(self):
        # Импортируем здесь, чтобы избежать циклического импорта
        from core.handlers import admin_cabinet
        self.admin_cabinet = admin_cabinet
        
        # Мок для settings
        self.mock_settings = MagicMock()
        self.mock_settings.features.moderation = True
        
        # Мок для admins_service
        self.mock_admins_service = AsyncMock()
        self.mock_admins_service.is_admin.return_value = True
        
        # Мок для базы данных
        self.mock_db = MagicMock()
        self.mock_conn = MagicMock()
        self.mock_cursor = MagicMock()
        self.mock_db.get_connection.return_value.__enter__.return_value = self.mock_conn
        self.mock_conn.execute.return_value = self.mock_cursor
        
        # Применяем патчи
        self.patchers = [
            patch('core.handlers.admin_cabinet.settings', self.mock_settings),
            patch('core.handlers.admin_cabinet.admins_service', self.mock_admins_service),
            patch('core.handlers.admin_cabinet.db_v2', self.mock_db)
        ]
        
        for patcher in self.patchers:
            patcher.start()
            
        yield
        
        # Останавливаем все патчи
        for patcher in self.patchers:
            patcher.stop()

    @pytest.mark.asyncio
    async def test_admin_queue_view(self):
        """Тест просмотра карточки в очереди модерации."""
        # Импортируем здесь, чтобы использовать замоканные зависимости
        from core.handlers import admin_cabinet
        
        # Мок данных карточки
        self.mock_cursor.fetchone.return_value = {
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
        
        # Создаем мок для сообщения с асинхронным edit_text
        message = MockMessage()
        message.edit_text = AsyncMock()
        message.answer = AsyncMock()
        
        # Создаем асинхронный мок для callback
        callback = AsyncMock(spec=CallbackQuery)
        callback.from_user = user
        callback.message = message
        callback.data = 'adm:q:view:1:0'  # card_id=1, page=0
        
        # Настраиваем мок для асинхронного вызова
        callback.answer = AsyncMock()
        
        # Мокаем _build_card_view_text, чтобы не зависеть от его реализации
        with patch('core.handlers.admin_cabinet._build_card_view_text') as mock_build_text:
            mock_build_text.return_value = 'Test card view text'
            
            # Мокаем _build_card_view_kb, чтобы не зависеть от его реализации
            with patch('core.handlers.admin_cabinet._build_card_view_kb') as mock_build_kb:
                mock_build_kb.return_value = 'test_keyboard'
                
                # Вызываем обработчик
                await admin_cabinet.admin_queue_view(callback)
        
        # Проверяем, что был вызван edit_text с правильными параметрами
        callback.message.edit_text.assert_called_once()
        args, kwargs = callback.message.edit_text.call_args
        assert args[0] == 'Test card view text', "Неверный текст сообщения"
        assert kwargs.get('reply_markup') == 'test_keyboard', "Неверная клавиатура"

    @pytest.mark.asyncio
    async def test_admin_queue_delete(self):
        """Тест удаления карточки из очереди модерации."""
        # Импортируем здесь, чтобы использовать замоканные зависимости
        from core.handlers import admin_cabinet
        
        # Мок данных карточки
        self.mock_cursor.fetchone.return_value = {
            'id': 1,
            'title': 'Тестовая карточка',
            'status': 'pending',
            'partner_id': 123
        }
        
        # Создаем мок для callback_query
        user = MagicMock()
        user.id = 12345
        
        message = MockMessage()
        
        # Создаем асинхронный мок для callback
        callback = AsyncMock(spec=CallbackQuery)
        callback.from_user = user
        callback.message = message
        # Исправляем формат данных для удаления (должен быть adm:q:del:confirm:)
        callback.data = 'adm:q:del:confirm:1:0'  # card_id=1, page=0
        
        # Настраиваем мок для асинхронного вызова
        callback.answer = AsyncMock()
        
        # Мок для функции _render_queue_page
        with patch('core.handlers.admin_cabinet._render_queue_page') as mock_render:
            # Вызываем обработчик
            await admin_cabinet.admin_queue_delete(callback)
            
            # Проверяем, что функция удаления была вызвана с правильными аргументами
            self.mock_db.delete_card.assert_called_once_with(1)
            
            # Проверяем, что была вызвана отрисовка страницы с правильными параметрами
            mock_render.assert_called_once_with(callback.message, 12345, page=0, edit=True)
            
            # Проверяем, что был вызван answer с правильными параметрами
            callback.answer.assert_called_once_with(ANY, show_alert=False)
