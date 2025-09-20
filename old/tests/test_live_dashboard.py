"""
Тесты для живых дашбордов
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from aiogram.types import Message, CallbackQuery, User
from aiogram.fsm.context import FSMContext
from datetime import datetime, timedelta
from core.services.live_dashboard import LiveDashboardService, DashboardMetric, DashboardData
from core.handlers.live_dashboard_router import (
    moderation_dashboard_handler,
    notifications_dashboard_handler,
    system_dashboard_handler,
    refresh_dashboard_callback,
    dashboard_menu_callback
)


class TestLiveDashboardService:
    """Тесты сервиса живых дашбордов"""
    
    def setup_method(self):
        """Настройка для каждого теста"""
        self.service = LiveDashboardService()
    
    @pytest.mark.asyncio
    async def test_get_moderation_dashboard(self):
        """Тест получения дашборда модерации"""
        with patch('core.services.live_dashboard.db_v2') as mock_db:
            # Настроить моки
            mock_db.get_cards_count.side_effect = [100, 15, 50, 10, 25]  # total, pending, approved, rejected, published
            mock_db.get_cards_count.return_value = 5  # для since параметра
            
            dashboard = await self.service.get_moderation_dashboard()
            
            assert isinstance(dashboard, DashboardData)
            assert dashboard.title == "📊 Дашборд модерации"
            assert len(dashboard.metrics) == 5
            assert dashboard.auto_refresh_seconds == 60
            
            # Проверить метрики
            metric_names = [metric.name for metric in dashboard.metrics]
            assert "📝 На модерации" in metric_names
            assert "✅ Одобрено" in metric_names
            assert "❌ Отклонено" in metric_names
            assert "🎉 Опубликовано" in metric_names
            assert "📊 Всего карточек" in metric_names
    
    @pytest.mark.asyncio
    async def test_get_notifications_dashboard(self):
        """Тест получения дашборда уведомлений"""
        with patch('core.services.live_dashboard.db_v2') as mock_db:
            # Настроить моки
            mock_db.get_notifications_count.side_effect = [500, 25]  # total, unread
            mock_db.get_sms_queue_count.return_value = 10
            mock_db.get_sms_failed_count.return_value = 2
            mock_db.get_sms_sent_count.return_value = 100
            
            dashboard = await self.service.get_notifications_dashboard()
            
            assert isinstance(dashboard, DashboardData)
            assert dashboard.title == "🔔 Дашборд уведомлений"
            assert len(dashboard.metrics) == 5
            assert dashboard.auto_refresh_seconds == 30
            
            # Проверить метрики
            metric_names = [metric.name for metric in dashboard.metrics]
            assert "🔔 Всего уведомлений" in metric_names
            assert "📬 Непрочитанные" in metric_names
            assert "📱 SMS в очереди" in metric_names
            assert "❌ Неудачные SMS" in metric_names
            assert "📤 Отправлено SMS" in metric_names
    
    @pytest.mark.asyncio
    async def test_get_system_dashboard(self):
        """Тест получения дашборда системы"""
        with patch('core.services.live_dashboard.psutil') as mock_psutil:
            # Настроить моки
            mock_psutil.virtual_memory.return_value.percent = 65.5
            mock_psutil.disk_usage.return_value.percent = 45.2
            
            with patch.object(self.service, '_check_database_status', return_value=True):
                with patch.object(self.service, '_check_redis_status', return_value=True):
                    with patch.object(self.service, '_check_odoo_status', return_value=False):
                        with patch.object(self.service, '_get_active_connections', return_value=45):
                            dashboard = await self.service.get_system_dashboard()
            
            assert isinstance(dashboard, DashboardData)
            assert dashboard.title == "⚙️ Дашборд системы"
            assert len(dashboard.metrics) == 6
            assert dashboard.auto_refresh_seconds == 120
            
            # Проверить метрики
            metric_names = [metric.name for metric in dashboard.metrics]
            assert "🗄️ База данных" in metric_names
            assert "🔴 Redis" in metric_names
            assert "🌐 Odoo" in metric_names
            assert "🔗 Активные соединения" in metric_names
            assert "💾 Использование памяти" in metric_names
            assert "💿 Использование диска" in metric_names
    
    @pytest.mark.asyncio
    async def test_check_database_status_success(self):
        """Тест успешной проверки статуса БД"""
        with patch('core.services.live_dashboard.db_v2') as mock_db:
            mock_db.get_cards_count.return_value = 100
            
            result = await self.service._check_database_status()
            assert result is True
    
    @pytest.mark.asyncio
    async def test_check_database_status_failure(self):
        """Тест неудачной проверки статуса БД"""
        with patch('core.services.live_dashboard.db_v2') as mock_db:
            mock_db.get_cards_count.side_effect = Exception("DB Error")
            
            result = await self.service._check_database_status()
            assert result is False
    
    @pytest.mark.asyncio
    async def test_check_redis_status_success(self):
        """Тест успешной проверки статуса Redis"""
        with patch('os.getenv', return_value='redis://localhost:6379'):
            with patch('aioredis.from_url') as mock_redis:
                mock_client = AsyncMock()
                mock_client.ping = AsyncMock()
                mock_client.close = AsyncMock()
                mock_redis.return_value = mock_client
                
                result = await self.service._check_redis_status()
                assert result is True
    
    @pytest.mark.asyncio
    async def test_check_redis_status_failure(self):
        """Тест неудачной проверки статуса Redis"""
        with patch('os.getenv', return_value=None):
            result = await self.service._check_redis_status()
            assert result is False
    
    @pytest.mark.asyncio
    async def test_check_odoo_status_success(self):
        """Тест успешной проверки статуса Odoo"""
        with patch('core.services.live_dashboard.odoo_api') as mock_odoo:
            mock_odoo.is_configured = True
            mock_odoo.get_partner_count = AsyncMock(return_value=50)
            
            result = await self.service._check_odoo_status()
            assert result is True
    
    @pytest.mark.asyncio
    async def test_check_odoo_status_failure(self):
        """Тест неудачной проверки статуса Odoo"""
        with patch('core.services.live_dashboard.odoo_api') as mock_odoo:
            mock_odoo.is_configured = False
            
            result = await self.service._check_odoo_status()
            assert result is False
    
    def test_format_dashboard_message(self):
        """Тест форматирования сообщения дашборда"""
        # Создать тестовый дашборд
        metrics = [
            DashboardMetric(
                name="📝 На модерации",
                value=15,
                change=5,
                status="warning",
                last_updated=datetime.now(),
                description="Карточки ожидающие модерации"
            ),
            DashboardMetric(
                name="✅ Одобрено",
                value=50,
                change=0,
                status="good",
                last_updated=datetime.now(),
                description="Карточки одобренные модераторами"
            )
        ]
        
        dashboard = DashboardData(
            title="📊 Дашборд модерации",
            metrics=metrics,
            last_updated=datetime.now(),
            auto_refresh_seconds=60
        )
        
        message = self.service.format_dashboard_message(dashboard)
        
        assert "📊 Дашборд модерации" in message
        assert "📝 На модерации: 15 (+5)" in message
        assert "✅ Одобрено: 50" in message
        assert "Карточки ожидающие модерации" in message
        assert "Автообновление: каждые 60 сек" in message
    
    @pytest.mark.asyncio
    async def test_start_auto_refresh(self):
        """Тест запуска автообновления"""
        callback_func = AsyncMock()
        
        with patch.object(self.service, 'get_moderation_dashboard') as mock_get:
            mock_get.return_value = DashboardData(
                title="Test",
                metrics=[],
                last_updated=datetime.now(),
                auto_refresh_seconds=1
            )
            
            # Запустить автообновление
            await self.service.start_auto_refresh("moderation", callback_func, 123456)
            
            # Проверить что задача создана
            assert "moderation" in self.service.refresh_tasks
            
            # Остановить автообновление
            await self.service.stop_auto_refresh("moderation")
            assert "moderation" not in self.service.refresh_tasks
    
    @pytest.mark.asyncio
    async def test_stop_auto_refresh(self):
        """Тест остановки автообновления"""
        # Создать фиктивную задачу
        task = asyncio.create_task(asyncio.sleep(3600))
        self.service.refresh_tasks["test"] = task
        
        # Остановить автообновление
        await self.service.stop_auto_refresh("test")
        
        # Проверить что задача удалена
        assert "test" not in self.service.refresh_tasks
        assert task.cancelled()


class TestLiveDashboardRouter:
    """Тесты роутера живых дашбордов"""
    
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
    async def test_moderation_dashboard_handler_admin_access(self):
        """Тест доступа админа к дашборду модерации"""
        with patch('core.handlers.live_dashboard_router.get_user_role', return_value='admin'):
            with patch('core.handlers.live_dashboard_router.live_dashboard') as mock_dashboard:
                mock_dashboard.get_moderation_dashboard = AsyncMock(return_value=DashboardData(
                    title="Test",
                    metrics=[],
                    last_updated=datetime.now(),
                    auto_refresh_seconds=60
                ))
                mock_dashboard.format_dashboard_message.return_value = "Test dashboard message"
                
                await moderation_dashboard_handler(self.message, self.state)
                
                # Проверить что сообщение отправлено
                self.message.answer.assert_called_once()
                call_args = self.message.answer.call_args
                assert "Test dashboard message" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_moderation_dashboard_handler_user_access_denied(self):
        """Тест запрета доступа обычного пользователя"""
        with patch('core.handlers.live_dashboard_router.get_user_role', return_value='user'):
            await moderation_dashboard_handler(self.message, self.state)
            
            # Проверить что сообщение отправлено
            self.message.answer.assert_called_once()
            call_args = self.message.answer.call_args
            assert "Доступ запрещен" in call_args[0][0]
            assert "только администраторам" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_notifications_dashboard_handler_admin_access(self):
        """Тест доступа админа к дашборду уведомлений"""
        with patch('core.handlers.live_dashboard_router.get_user_role', return_value='admin'):
            with patch('core.handlers.live_dashboard_router.live_dashboard') as mock_dashboard:
                mock_dashboard.get_notifications_dashboard = AsyncMock(return_value=DashboardData(
                    title="Test",
                    metrics=[],
                    last_updated=datetime.now(),
                    auto_refresh_seconds=30
                ))
                mock_dashboard.format_dashboard_message.return_value = "Test notifications message"
                
                await notifications_dashboard_handler(self.message, self.state)
                
                # Проверить что сообщение отправлено
                self.message.answer.assert_called_once()
                call_args = self.message.answer.call_args
                assert "Test notifications message" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_system_dashboard_handler_admin_access(self):
        """Тест доступа админа к дашборду системы"""
        with patch('core.handlers.live_dashboard_router.get_user_role', return_value='admin'):
            with patch('core.handlers.live_dashboard_router.live_dashboard') as mock_dashboard:
                mock_dashboard.get_system_dashboard = AsyncMock(return_value=DashboardData(
                    title="Test",
                    metrics=[],
                    last_updated=datetime.now(),
                    auto_refresh_seconds=120
                ))
                mock_dashboard.format_dashboard_message.return_value = "Test system message"
                
                await system_dashboard_handler(self.message, self.state)
                
                # Проверить что сообщение отправлено
                self.message.answer.assert_called_once()
                call_args = self.message.answer.call_args
                assert "Test system message" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_refresh_dashboard_callback(self):
        """Тест callback'а обновления дашборда"""
        self.callback.data = "dashboard_refresh_moderation"
        
        with patch('core.handlers.live_dashboard_router.live_dashboard') as mock_dashboard:
            mock_dashboard.get_moderation_dashboard = AsyncMock(return_value=DashboardData(
                title="Test",
                metrics=[],
                last_updated=datetime.now(),
                auto_refresh_seconds=60
            ))
            mock_dashboard.format_dashboard_message.return_value = "Updated dashboard message"
            
            await refresh_dashboard_callback(self.callback, self.state)
            
            # Проверить что сообщение отредактировано
            assert self.message.edit_text.call_count == 2  # Загрузка + результат
            call_args = self.message.edit_text.call_args
            assert "Updated dashboard message" in call_args[0][0]
            
            self.callback.answer.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_dashboard_menu_callback(self):
        """Тест callback'а меню дашбордов"""
        await dashboard_menu_callback(self.callback, self.state)
        
        # Проверить что сообщение отредактировано
        self.message.edit_text.assert_called_once()
        call_args = self.message.edit_text.call_args
        assert "Живые дашборды" in call_args[0][0]
        assert "Модерация" in call_args[0][0]
        assert "Уведомления" in call_args[0][0]
        assert "Система" in call_args[0][0]
        
        self.callback.answer.assert_called_once()


class TestLiveDashboardUtilityFunctions:
    """Тесты утилитарных функций живых дашбордов"""
    
    @pytest.mark.asyncio
    async def test_get_moderation_dashboard_utility(self):
        """Тест утилитарной функции получения дашборда модерации"""
        from core.services.live_dashboard import get_moderation_dashboard
        
        with patch('core.services.live_dashboard.live_dashboard') as mock_dashboard:
            mock_dashboard.get_moderation_dashboard = AsyncMock(return_value={"test": "result"})
            
            result = await get_moderation_dashboard()
            assert result == {"test": "result"}
            mock_dashboard.get_moderation_dashboard.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_notifications_dashboard_utility(self):
        """Тест утилитарной функции получения дашборда уведомлений"""
        from core.services.live_dashboard import get_notifications_dashboard
        
        with patch('core.services.live_dashboard.live_dashboard') as mock_dashboard:
            mock_dashboard.get_notifications_dashboard = AsyncMock(return_value={"test": "result"})
            
            result = await get_notifications_dashboard()
            assert result == {"test": "result"}
            mock_dashboard.get_notifications_dashboard.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_system_dashboard_utility(self):
        """Тест утилитарной функции получения дашборда системы"""
        from core.services.live_dashboard import get_system_dashboard
        
        with patch('core.services.live_dashboard.live_dashboard') as mock_dashboard:
            mock_dashboard.get_system_dashboard = AsyncMock(return_value={"test": "result"})
            
            result = await get_system_dashboard()
            assert result == {"test": "result"}
            mock_dashboard.get_system_dashboard.assert_called_once()
    
    def test_format_dashboard_utility(self):
        """Тест утилитарной функции форматирования дашборда"""
        from core.services.live_dashboard import format_dashboard
        
        dashboard = DashboardData(
            title="Test Dashboard",
            metrics=[],
            last_updated=datetime.now(),
            auto_refresh_seconds=60
        )
        
        with patch('core.services.live_dashboard.live_dashboard') as mock_dashboard:
            mock_dashboard.format_dashboard_message.return_value = "Formatted message"
            
            result = format_dashboard(dashboard)
            assert result == "Formatted message"
            mock_dashboard.format_dashboard_message.assert_called_once_with(dashboard)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
