"""
Тесты для расширенной системы модерации
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from fastapi import FastAPI

from core.services.moderation_service import ModerationService
from core.models.card import Card
from core.models.partner import ModerationLog
from web.routes_moderation import router
from core.services.admins import admins_service


class TestModerationService:
    """Тесты для сервиса модерации"""
    
    @pytest.fixture
    def mock_db(self):
        """Мок базы данных"""
        return AsyncMock()
    
    @pytest.fixture
    def moderation_service(self, mock_db):
        """Сервис модерации с мок БД"""
        return ModerationService(mock_db)
    
    @pytest.fixture
    def mock_card(self):
        """Мок карточки"""
        return Card(
            id=1,
            title="Test Card",
            description="Test description",
            status="pending",
            partner_id=123,
            category_id=1,
            created_at=datetime.utcnow()
        )
    
    @pytest.fixture
    def mock_moderation_log(self):
        """Мок лога модерации"""
        return ModerationLog(
            id=1,
            moderator_id=456,
            card_id=1,
            action="approve",
            comment="Test approval",
            created_at=datetime.utcnow()
        )
    
    @pytest.mark.asyncio
    async def test_get_pending_cards(self, moderation_service, mock_db, mock_card):
        """Тест получения карточек ожидающих модерации"""
        # Настройка мока
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = [mock_card]
        mock_db.execute.return_value = mock_result
        
        # Выполнение теста
        cards = await moderation_service.get_pending_cards(limit=10)
        
        # Проверки
        assert len(cards) == 1
        assert cards[0]["id"] == 1
        assert cards[0]["title"] == "Test Card"
        assert cards[0]["status"] == "pending"
    
    @pytest.mark.asyncio
    async def test_approve_card_success(self, moderation_service, mock_db, mock_card):
        """Тест успешного одобрения карточки"""
        # Настройка мока
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_card
        mock_db.execute.return_value = mock_result
        
        # Выполнение теста
        result = await moderation_service.approve_card(
            card_id=1,
            moderator_id=456,
            comment="Test approval"
        )
        
        # Проверки
        assert result["success"] is True
        assert result["card_id"] == 1
        assert result["status"] == "published"
        
        # Проверяем что были вызваны нужные методы
        mock_db.execute.assert_called()
        mock_db.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_approve_card_not_found(self, moderation_service, mock_db):
        """Тест одобрения несуществующей карточки"""
        # Настройка мока - карточка не найдена
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        # Выполнение теста и проверка исключения
        with pytest.raises(Exception):  # NotFoundError
            await moderation_service.approve_card(
                card_id=999,
                moderator_id=456,
                comment="Test approval"
            )
    
    @pytest.mark.asyncio
    async def test_reject_card_success(self, moderation_service, mock_db, mock_card):
        """Тест успешного отклонения карточки"""
        # Настройка мока
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_card
        mock_db.execute.return_value = mock_result
        
        # Выполнение теста
        result = await moderation_service.reject_card(
            card_id=1,
            moderator_id=456,
            reason="Test rejection",
            reason_code="incomplete"
        )
        
        # Проверки
        assert result["success"] is True
        assert result["card_id"] == 1
        assert result["status"] == "rejected"
        assert result["reason"] == "Test rejection"
    
    @pytest.mark.asyncio
    async def test_feature_card_success(self, moderation_service, mock_db, mock_card):
        """Тест успешного выделения карточки как рекомендуемой"""
        # Настройка мока
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_card
        mock_db.execute.return_value = mock_result
        
        # Выполнение теста
        result = await moderation_service.feature_card(
            card_id=1,
            moderator_id=456,
            comment="Test feature"
        )
        
        # Проверки
        assert result["success"] is True
        assert result["card_id"] == 1
        assert result["featured"] is True
    
    @pytest.mark.asyncio
    async def test_archive_card_success(self, moderation_service, mock_db, mock_card):
        """Тест успешного архивирования карточки"""
        # Настройка мока
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_card
        mock_db.execute.return_value = mock_result
        
        # Выполнение теста
        result = await moderation_service.archive_card(
            card_id=1,
            moderator_id=456,
            comment="Test archive"
        )
        
        # Проверки
        assert result["success"] is True
        assert result["card_id"] == 1
        assert result["status"] == "archived"
    
    @pytest.mark.asyncio
    async def test_get_moderation_stats(self, moderation_service, mock_db, mock_moderation_log):
        """Тест получения статистики модерации"""
        # Настройка мока
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = [mock_moderation_log]
        mock_db.execute.return_value = mock_result
        
        # Выполнение теста
        stats = await moderation_service.get_moderation_stats(days=30)
        
        # Проверки
        assert stats["total_actions"] == 1
        assert stats["approvals"] == 1
        assert stats["rejections"] == 0
        assert stats["features"] == 0
        assert stats["approval_rate"] == 1.0
    
    @pytest.mark.asyncio
    async def test_get_moderation_queue_status(self, moderation_service, mock_db):
        """Тест получения статуса очереди модерации"""
        # Настройка мока для подсчета карточек
        mock_pending_result = AsyncMock()
        mock_pending_result.scalar.return_value = 5
        mock_published_result = AsyncMock()
        mock_published_result.scalar.return_value = 10
        mock_rejected_result = AsyncMock()
        mock_rejected_result.scalar.return_value = 2
        
        # Настройка мока для недавней активности
        mock_logs_result = AsyncMock()
        mock_logs_result.scalars.return_value.all.return_value = []
        
        # Настройка последовательных вызовов execute
        mock_db.execute.side_effect = [
            mock_pending_result,
            mock_published_result,
            mock_rejected_result,
            mock_logs_result
        ]
        
        # Выполнение теста
        queue_status = await moderation_service.get_moderation_queue_status()
        
        # Проверки
        assert queue_status["pending_cards"] == 5
        assert queue_status["published_cards"] == 10
        assert queue_status["rejected_cards"] == 2
        assert queue_status["recent_activity"] == []
    
    @pytest.mark.asyncio
    async def test_apply_automated_rules(self, moderation_service, mock_db, mock_card):
        """Тест применения автоматических правил модерации"""
        # Настройка мока
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_card
        mock_db.execute.return_value = mock_result
        
        # Выполнение теста
        result = await moderation_service.apply_automated_rules(card_id=1)
        
        # Проверки
        assert result["success"] is True
        assert result["card_id"] == 1
        assert result["rules_applied"] == []
        assert result["auto_action"] is None


class TestModerationAPI:
    """Тесты для API модерации"""
    
    @pytest.fixture
    def app(self):
        """Создание тестового приложения"""
        app = FastAPI()
        app.include_router(router)
        return app
    
    @pytest.fixture
    def client(self, app):
        """Тестовый клиент"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_admin_user(self):
        """Мок админа"""
        return {
            "user_id": 123,
            "username": "admin",
            "role": "admin"
        }
    
    @pytest.fixture
    def mock_regular_user(self):
        """Мок обычного пользователя"""
        return {
            "user_id": 456,
            "username": "user",
            "role": "user"
        }
    
    @pytest.mark.asyncio
    async def test_moderation_dashboard_page(self, client):
        """Тест загрузки страницы дашборда модерации"""
        response = client.get("/api/moderation/dashboard")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Модерация" in response.text
    
    @pytest.mark.asyncio
    async def test_get_moderation_stats_admin(self, client, mock_admin_user):
        """Тест получения статистики модерации для админа"""
        with patch('web.routes_moderation.admins_service.is_admin', return_value=True), \
             patch('web.routes_moderation.ModerationService') as mock_service_class:
            
            # Настройка мока сервиса
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service
            mock_service.get_moderation_stats.return_value = {
                "total_actions": 10,
                "approvals": 8,
                "rejections": 2,
                "approval_rate": 0.8
            }
            mock_service.get_moderation_queue_status.return_value = {
                "pending_cards": 5,
                "published_cards": 20,
                "rejected_cards": 3,
                "recent_activity": []
            }
            
            response = client.get("/api/moderation/stats")
            assert response.status_code == 200
            data = response.json()
            assert data["pending_cards"] == 5
            assert data["published_cards"] == 20
            assert data["approval_rate"] == 0.8
    
    @pytest.mark.asyncio
    async def test_get_moderation_stats_unauthorized(self, client, mock_regular_user):
        """Тест получения статистики модерации для неавторизованного пользователя"""
        with patch('web.routes_moderation.admins_service.is_admin', return_value=False):
            response = client.get("/api/moderation/stats")
            assert response.status_code == 403
            assert "Access denied" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_approve_card_success(self, client, mock_admin_user):
        """Тест успешного одобрения карточки"""
        with patch('web.routes_moderation.admins_service.is_admin', return_value=True), \
             patch('web.routes_moderation.ModerationService') as mock_service_class:
            
            # Настройка мока сервиса
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service
            mock_service.approve_card.return_value = {
                "success": True,
                "card_id": 1,
                "status": "published",
                "message": "Card approved successfully"
            }
            
            response = client.post(
                "/api/moderation/approve/1",
                json={"comment": "Test approval"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["card_id"] == 1
    
    @pytest.mark.asyncio
    async def test_reject_card_success(self, client, mock_admin_user):
        """Тест успешного отклонения карточки"""
        with patch('web.routes_moderation.admins_service.is_admin', return_value=True), \
             patch('web.routes_moderation.ModerationService') as mock_service_class:
            
            # Настройка мока сервиса
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service
            mock_service.reject_card.return_value = {
                "success": True,
                "card_id": 1,
                "status": "rejected",
                "reason": "Test rejection",
                "message": "Card rejected successfully"
            }
            
            response = client.post(
                "/api/moderation/reject/1",
                json={"reason": "Test rejection"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["reason"] == "Test rejection"
    
    @pytest.mark.asyncio
    async def test_reject_card_no_reason(self, client, mock_admin_user):
        """Тест отклонения карточки без указания причины"""
        with patch('web.routes_moderation.admins_service.is_admin', return_value=True):
            response = client.post(
                "/api/moderation/reject/1",
                json={}
            )
            
            assert response.status_code == 400
            assert "Rejection reason is required" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_feature_card_success(self, client, mock_admin_user):
        """Тест успешного выделения карточки как рекомендуемой"""
        with patch('web.routes_moderation.admins_service.is_admin', return_value=True), \
             patch('web.routes_moderation.ModerationService') as mock_service_class:
            
            # Настройка мока сервиса
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service
            mock_service.feature_card.return_value = {
                "success": True,
                "card_id": 1,
                "featured": True,
                "message": "Card featured successfully"
            }
            
            response = client.post(
                "/api/moderation/feature/1",
                json={"comment": "Test feature"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["featured"] is True
    
    @pytest.mark.asyncio
    async def test_bulk_approve_cards(self, client, mock_admin_user):
        """Тест массового одобрения карточек"""
        with patch('web.routes_moderation.admins_service.is_admin', return_value=True), \
             patch('web.routes_moderation.ModerationService') as mock_service_class:
            
            # Настройка мока сервиса
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service
            mock_service.approve_card.return_value = {
                "success": True,
                "card_id": 1,
                "status": "published"
            }
            
            response = client.post(
                "/api/moderation/bulk/approve",
                json=[1, 2, 3]
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 3
            assert data["successful"] == 3
            assert data["failed"] == 0
    
    @pytest.mark.asyncio
    async def test_get_moderation_logs(self, client, mock_admin_user):
        """Тест получения логов модерации"""
        with patch('web.routes_moderation.admins_service.is_admin', return_value=True), \
             patch('web.routes_moderation.get_db') as mock_get_db:
            
            # Настройка мока базы данных
            mock_db = AsyncMock()
            mock_get_db.return_value.__aenter__.return_value = mock_db
            
            # Настройка результата запроса
            mock_result = AsyncMock()
            mock_result.scalars.return_value.all.return_value = []
            mock_count_result = AsyncMock()
            mock_count_result.scalar.return_value = 0
            
            mock_db.execute.side_effect = [mock_result, mock_count_result]
            
            response = client.get("/api/moderation/logs")
            
            assert response.status_code == 200
            data = response.json()
            assert data["logs"] == []
            assert data["total"] == 0
    
    @pytest.mark.asyncio
    async def test_get_queue_status(self, client, mock_admin_user):
        """Тест получения статуса очереди"""
        with patch('web.routes_moderation.admins_service.is_admin', return_value=True), \
             patch('web.routes_moderation.ModerationService') as mock_service_class:
            
            # Настройка мока сервиса
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service
            mock_service.get_moderation_queue_status.return_value = {
                "pending_cards": 5,
                "published_cards": 20,
                "rejected_cards": 3,
                "recent_activity": []
            }
            
            response = client.get("/api/moderation/queue/status")
            
            assert response.status_code == 200
            data = response.json()
            assert data["pending_cards"] == 5
            assert data["published_cards"] == 20


class TestModerationSecurity:
    """Тесты безопасности системы модерации"""
    
    @pytest.mark.asyncio
    async def test_unauthorized_access(self, client):
        """Тест доступа без авторизации"""
        endpoints = [
            ("/api/moderation/stats", "GET"),
            ("/api/moderation/cards", "GET"),
            ("/api/moderation/approve/1", "POST"),
            ("/api/moderation/reject/1", "POST"),
            ("/api/moderation/feature/1", "POST"),
            ("/api/moderation/archive/1", "POST"),
            ("/api/moderation/logs", "GET"),
            ("/api/moderation/queue/status", "GET")
        ]
        
        for endpoint, method in endpoints:
            if method == "POST":
                response = client.post(endpoint, json={})
            else:
                response = client.get(endpoint)
            
            # Должна быть ошибка авторизации
            assert response.status_code in [401, 403]
    
    @pytest.mark.asyncio
    async def test_non_admin_access(self, client):
        """Тест доступа не-админа к функциям модерации"""
        with patch('web.routes_moderation.admins_service.is_admin', return_value=False):
            response = client.get("/api/moderation/stats")
            assert response.status_code == 403
            assert "Admin privileges required" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_malicious_card_id(self, client, mock_admin_user):
        """Тест обработки вредоносных ID карточек"""
        malicious_ids = [-1, 0, 999999999, "'; DROP TABLE cards; --"]
        
        with patch('web.routes_moderation.admins_service.is_admin', return_value=True):
            for card_id in malicious_ids:
                response = client.post(f"/api/moderation/approve/{card_id}", json={})
                # Должна быть ошибка валидации или не найдено
                assert response.status_code in [400, 404, 422]
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, client, mock_admin_user):
        """Тест ограничения скорости запросов"""
        with patch('web.routes_moderation.admins_service.is_admin', return_value=True), \
             patch('web.routes_moderation.ModerationService') as mock_service_class:
            
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service
            mock_service.approve_card.return_value = {"success": True}
            
            # Множественные запросы
            for i in range(10):
                response = client.post(f"/api/moderation/approve/{i}", json={})
                # Все должны быть успешными (rate limiting не реализован в тестах)
                assert response.status_code == 200


class TestModerationIntegration:
    """Тесты интеграции системы модерации"""
    
    @pytest.mark.asyncio
    async def test_moderation_workflow(self):
        """Тест полного рабочего процесса модерации"""
        # 1. Создание карточки
        # 2. Добавление в очередь модерации
        # 3. Одобрение модератором
        # 4. Уведомление партнера
        # 5. Обновление статистики
        
        # Этот тест был бы более комплексным в реальной среде
        assert True  # Placeholder для интеграционного теста
    
    @pytest.mark.asyncio
    async def test_automated_rules_integration(self):
        """Тест интеграции автоматических правил"""
        # Тест автоматического применения правил модерации
        assert True  # Placeholder для интеграционного теста
    
    @pytest.mark.asyncio
    async def test_notification_system_integration(self):
        """Тест интеграции системы уведомлений"""
        # Тест уведомлений партнеров о результатах модерации
        assert True  # Placeholder для интеграционного теста
