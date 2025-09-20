"""
Тесты для ИИ помощника
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from aiogram.types import Message, CallbackQuery, User
from aiogram.fsm.context import FSMContext
from core.services.ai_assistant import ClaudeAIService, ai_assistant
from core.handlers.ai_assistant_router import (
    ai_assistant_handler,
    analyze_logs_callback,
    analyze_analytics_callback,
    search_data_callback,
    get_recommendations_callback
)


class TestClaudeAIService:
    """Тесты сервиса Claude AI"""
    
    def setup_method(self):
        """Настройка для каждого теста"""
        self.service = ClaudeAIService()
    
    def test_is_available_without_api_key(self):
        """Тест доступности без API ключа"""
        with patch.dict('os.environ', {}, clear=True):
            service = ClaudeAIService()
            assert not service.is_available()
    
    def test_is_available_with_api_key(self):
        """Тест доступности с API ключом"""
        with patch.dict('os.environ', {'CLAUDE_API_KEY': 'test-key'}):
            service = ClaudeAIService()
            assert service.is_available()
    
    @pytest.mark.asyncio
    async def test_analyze_system_logs_not_available(self):
        """Тест анализа логов когда API недоступен"""
        with patch.dict('os.environ', {}, clear=True):
            service = ClaudeAIService()
            result = await service.analyze_system_logs(24)
            assert "error" in result
            assert "Claude API not available" in result["error"]
    
    @pytest.mark.asyncio
    async def test_analyze_user_analytics_not_available(self):
        """Тест анализа аналитики когда API недоступен"""
        with patch.dict('os.environ', {}, clear=True):
            service = ClaudeAIService()
            result = await service.analyze_user_analytics(7)
            assert "error" in result
            assert "Claude API not available" in result["error"]
    
    @pytest.mark.asyncio
    async def test_search_database_not_available(self):
        """Тест поиска когда API недоступен"""
        with patch.dict('os.environ', {}, clear=True):
            service = ClaudeAIService()
            result = await service.search_database("test query")
            assert "error" in result
            assert "Claude API not available" in result["error"]
    
    @pytest.mark.asyncio
    async def test_get_system_recommendations_not_available(self):
        """Тест получения рекомендаций когда API недоступен"""
        with patch.dict('os.environ', {}, clear=True):
            service = ClaudeAIService()
            result = await service.get_system_recommendations()
            assert "error" in result
            assert "Claude API not available" in result["error"]
    
    @pytest.mark.asyncio
    async def test_call_claude_api_success(self):
        """Тест успешного вызова Claude API"""
        with patch.dict('os.environ', {'CLAUDE_API_KEY': 'test-key'}):
            service = ClaudeAIService()
            
            # Мокаем aiohttp
            mock_response = Mock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={
                "content": [{"text": "Test analysis result"}]
            })
            
            with patch('aiohttp.ClientSession.post') as mock_post:
                mock_post.return_value.__aenter__.return_value = mock_response
                
                result = await service._call_claude_api("Test prompt")
                assert result == "Test analysis result"
    
    @pytest.mark.asyncio
    async def test_call_claude_api_error(self):
        """Тест ошибки Claude API"""
        with patch.dict('os.environ', {'CLAUDE_API_KEY': 'test-key'}):
            service = ClaudeAIService()
            
            # Мокаем aiohttp с ошибкой
            mock_response = Mock()
            mock_response.status = 400
            mock_response.text = AsyncMock(return_value="Bad Request")
            
            with patch('aiohttp.ClientSession.post') as mock_post:
                mock_post.return_value.__aenter__.return_value = mock_response
                
                result = await service._call_claude_api("Test prompt")
                assert "Ошибка API: 400" in result
    
    @pytest.mark.asyncio
    async def test_get_recent_logs(self):
        """Тест получения логов"""
        result = await self.service._get_recent_logs(24)
        assert "total_logs" in result
        assert "error_count" in result
        assert "warning_count" in result
        assert "info_count" in result
    
    @pytest.mark.asyncio
    async def test_get_user_analytics(self):
        """Тест получения аналитики"""
        result = await self.service._get_user_analytics(7)
        assert "total_users" in result
        assert "active_users" in result
        assert "new_users" in result
        assert "partner_count" in result
    
    @pytest.mark.asyncio
    async def test_search_db_data(self):
        """Тест поиска данных"""
        result = await self.service._search_db_data("test query", "general")
        assert "query" in result
        assert "context" in result
        assert "results_count" in result
        assert "matches" in result
    
    @pytest.mark.asyncio
    async def test_get_system_info(self):
        """Тест получения системной информации"""
        result = await self.service._get_system_info()
        assert "database_status" in result
        assert "redis_status" in result
        assert "odoo_connection" in result
        assert "active_connections" in result


class TestAIAssistantRouter:
    """Тесты роутера ИИ помощника"""
    
    def setup_method(self):
        """Настройка для каждого теста"""
        self.user_id = 123456789
        self.admin_user = User(
            id=self.user_id,
            is_bot=False,
            first_name="Admin",
            username="admin"
        )
        self.message = Mock(spec=Message)
        self.message.from_user = self.admin_user
        self.message.answer = AsyncMock()
        
        self.callback = Mock(spec=CallbackQuery)
        self.callback.from_user = self.admin_user
        self.callback.message = self.message
        self.callback.answer = AsyncMock()
        
        self.state = Mock(spec=FSMContext)
        self.state.set_state = AsyncMock()
        self.state.clear = AsyncMock()
    
    @pytest.mark.asyncio
    async def test_ai_assistant_handler_admin_access(self):
        """Тест доступа админа к ИИ помощнику"""
        with patch('core.handlers.ai_assistant_router.get_user_role', return_value='admin'):
            with patch('core.handlers.ai_assistant_router.ai_assistant') as mock_ai:
                mock_ai.is_available.return_value = True
                
                await ai_assistant_handler(self.message, self.state)
                
                # Проверить что сообщение отправлено
                self.message.answer.assert_called_once()
                call_args = self.message.answer.call_args
                assert "ИИ Помощник" in call_args[0][0]
                assert "Доступные функции" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_ai_assistant_handler_user_access_denied(self):
        """Тест запрета доступа обычного пользователя"""
        with patch('core.handlers.ai_assistant_router.get_user_role', return_value='user'):
            await ai_assistant_handler(self.message, self.state)
            
            # Проверить что сообщение отправлено
            self.message.answer.assert_called_once()
            call_args = self.message.answer.call_args
            assert "Доступ запрещен" in call_args[0][0]
            assert "только администраторам" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_ai_assistant_handler_api_not_available(self):
        """Тест когда Claude API недоступен"""
        with patch('core.handlers.ai_assistant_router.get_user_role', return_value='admin'):
            with patch('core.handlers.ai_assistant_router.ai_assistant') as mock_ai:
                mock_ai.is_available.return_value = False
                
                await ai_assistant_handler(self.message, self.state)
                
                # Проверить что сообщение отправлено
                self.message.answer.assert_called_once()
                call_args = self.message.answer.call_args
                assert "ИИ помощник недоступен" in call_args[0][0]
                assert "Claude API не настроен" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_analyze_logs_callback(self):
        """Тест callback'а анализа логов"""
        await analyze_logs_callback(self.callback, self.state)
        
        # Проверить что сообщение отредактировано
        self.message.edit_text.assert_called_once()
        call_args = self.message.edit_text.call_args
        assert "Анализ системных логов" in call_args[0][0]
        assert "Выберите период" in call_args[0][0]
        
        self.callback.answer.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_analyze_analytics_callback(self):
        """Тест callback'а анализа аналитики"""
        await analyze_analytics_callback(self.callback, self.state)
        
        # Проверить что сообщение отредактировано
        self.message.edit_text.assert_called_once()
        call_args = self.message.edit_text.call_args
        assert "Анализ аналитики пользователей" in call_args[0][0]
        assert "Выберите период" in call_args[0][0]
        
        self.callback.answer.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_data_callback(self):
        """Тест callback'а поиска данных"""
        await search_data_callback(self.callback, self.state)
        
        # Проверить что сообщение отредактировано
        self.message.edit_text.assert_called_once()
        call_args = self.message.edit_text.call_args
        assert "Интеллектуальный поиск" in call_args[0][0]
        assert "Введите ваш запрос" in call_args[0][0]
        
        # Проверить что состояние установлено
        self.state.set_state.assert_called_once()
        self.callback.answer.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_recommendations_callback(self):
        """Тест callback'а получения рекомендаций"""
        with patch('core.handlers.ai_assistant_router.ai_assistant') as mock_ai:
            mock_ai.get_system_recommendations = AsyncMock(return_value={
                "recommendations": "Test recommendations",
                "timestamp": "2024-01-15T10:00:00"
            })
            
            await get_recommendations_callback(self.callback, self.state)
            
            # Проверить что сообщение отредактировано
            assert self.message.edit_text.call_count == 2  # Загрузка + результат
            call_args = self.message.edit_text.call_args
            assert "Рекомендации по системе" in call_args[0][0]
            
            self.callback.answer.assert_called_once()


class TestAIAssistantUtilityFunctions:
    """Тесты утилитарных функций ИИ помощника"""
    
    @pytest.mark.asyncio
    async def test_analyze_logs_utility(self):
        """Тест утилитарной функции анализа логов"""
        from core.services.ai_assistant import analyze_logs
        
        with patch('core.services.ai_assistant.ai_assistant') as mock_ai:
            mock_ai.analyze_system_logs = AsyncMock(return_value={"test": "result"})
            
            result = await analyze_logs(24)
            assert result == {"test": "result"}
            mock_ai.analyze_system_logs.assert_called_once_with(24)
    
    @pytest.mark.asyncio
    async def test_analyze_analytics_utility(self):
        """Тест утилитарной функции анализа аналитики"""
        from core.services.ai_assistant import analyze_analytics
        
        with patch('core.services.ai_assistant.ai_assistant') as mock_ai:
            mock_ai.analyze_user_analytics = AsyncMock(return_value={"test": "result"})
            
            result = await analyze_analytics(7)
            assert result == {"test": "result"}
            mock_ai.analyze_user_analytics.assert_called_once_with(7)
    
    @pytest.mark.asyncio
    async def test_search_data_utility(self):
        """Тест утилитарной функции поиска данных"""
        from core.services.ai_assistant import search_data
        
        with patch('core.services.ai_assistant.ai_assistant') as mock_ai:
            mock_ai.search_database = AsyncMock(return_value={"test": "result"})
            
            result = await search_data("test query", "general")
            assert result == {"test": "result"}
            mock_ai.search_database.assert_called_once_with("test query", "general")
    
    @pytest.mark.asyncio
    async def test_get_recommendations_utility(self):
        """Тест утилитарной функции получения рекомендаций"""
        from core.services.ai_assistant import get_recommendations
        
        with patch('core.services.ai_assistant.ai_assistant') as mock_ai:
            mock_ai.get_system_recommendations = AsyncMock(return_value={"test": "result"})
            
            result = await get_recommendations()
            assert result == {"test": "result"}
            mock_ai.get_system_recommendations.assert_called_once_with()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
