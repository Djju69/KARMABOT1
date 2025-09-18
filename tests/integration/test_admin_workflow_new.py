import pytest
from unittest.mock import AsyncMock, patch
from aiogram.types import Update, Message, Chat, User
from aiogram.fsm.context import FSMContext, StorageKey
from aiogram.fsm.storage.memory import MemoryStorage
from core.settings import settings

class TestAdminWorkflowNew:
    """Исправленные тесты workflow админ-панели"""
    
    @pytest.fixture
    def mock_bot(self):
        bot = AsyncMock()
        bot.send_message = AsyncMock()
        bot.id = 1
        return bot
    
    @pytest.fixture
    def test_user(self):
        return User(
            id=1,
            first_name='Test',
            is_bot=False,
            username='testuser'
        )
    
    @pytest.fixture
    def test_chat(self):
        return Chat(id=1, type='private')
    
    @pytest.mark.asyncio
    async def test_admin_command(self, setup_router, test_database, mock_bot, test_user, test_chat):
        """Тестирование команды /admin через диспетчер"""
        dp = setup_router
        
        # Мокаем зависимости
        with patch('core.services.admins.admins_service.is_admin', AsyncMock(return_value=True)), \
             patch('core.database.db_v2.db_v2.get_connection', return_value=test_database), \
             patch('core.services.profile.profile_service.get_lang', AsyncMock(return_value='ru')):
            
            # Создаем тестовое обновление
            update = Update(
                update_id=1,
                message=Message(
                    message_id=1,
                    date=None,
                    chat=test_chat,
                    from_user=test_user,
                    text="/admin"
                )
            )
            
            # Обрабатываем обновление
            await dp.feed_update(bot=mock_bot, update=update)
            
            # Проверяем что бот отправил сообщение
            assert mock_bot.send_message.called, "Bot's send_message was not called"
            
            # Проверяем аргументы вызова
            call_args = mock_bot.send_message.call_args.kwargs
            assert "text" in call_args, "No text in the bot's response"
            assert "Панель администратора" in call_args["text"], "Admin panel title not found"
            assert "reply_markup" in call_args, "No reply markup in response"
    
    @pytest.mark.asyncio
    async def test_moderation_queue(self, setup_router, test_database, mock_bot, test_user, test_chat):
        """Тест очереди модерации"""
        dp = setup_router
        
        # Добавляем тестовую карточку
        await test_database.execute(
            """
            INSERT INTO listings (id, name, status, category, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                'test-listing-1',
                'Test Restaurant',
                'pending',
                'restaurant',
                '2023-01-01T00:00:00',
                '2023-01-01T00:00:00'
            )
        )
        
        # Мокаем зависимости
        with patch('core.services.admins.admins_service.is_admin', AsyncMock(return_value=True)), \
             patch('core.database.db_v2.db_v2.get_connection', return_value=test_database), \
             patch('core.services.profile.profile_service.get_lang', AsyncMock(return_value='ru')):
            
            # Создаем тестовое обновление
            update = Update(
                update_id=2,
                message=Message(
                    message_id=2,
                    chat=test_chat,
                    from_user=test_user,
                    text="/admin_queue"
                )
            )
            
            # Обрабатываем обновление
            await dp.feed_update(bot=mock_bot, update=update)
            
            # Проверяем что бот отправил сообщение
            assert mock_bot.send_message.called, "Bot's send_message was not called"
            
            # Проверяем ответ
            call_args = mock_bot.send_message.call_args.kwargs
            response_text = call_args.get("text", "")
            assert "Очередь модерации" in response_text, "Queue title not found"
            assert "Test Restaurant" in response_text, "Test listing not found in response"
