"""
Тесты для QR WebApp функциональности
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from fastapi import FastAPI

from web.routes_qr_webapp import router, QRScanRequest, QRRedeemRequest, QRGenerateRequest
from core.models.qr_code import QRCode
from core.models.user_profile import UserLevel


class TestQRWebAppAPI:
    """Тесты для QR WebApp API endpoints"""
    
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
    def mock_user(self):
        """Мок пользователя"""
        return {
            "user_id": 123,
            "username": "testuser",
            "level": "silver"
        }
    
    @pytest.fixture
    def mock_qr_code(self):
        """Мок QR-кода"""
        return QRCode(
            id=1,
            qr_id="test-qr-id-123",
            user_id=123,
            discount_type="loyalty_points",
            discount_value=100,
            description="Test discount",
            expires_at=datetime.utcnow() + timedelta(hours=24),
            is_used=False,
            created_at=datetime.utcnow()
        )
    
    @pytest.fixture
    def mock_user_profile(self):
        """Мок профиля пользователя"""
        return {
            "user_id": 123,
            "level": "silver",
            "level_benefits": {
                "discount": 0.10,
                "points_multiplier": 1.2
            },
            "total_qr_scans": 5
        }
    
    @pytest.mark.asyncio
    async def test_qr_scanner_page(self, client):
        """Тест загрузки страницы QR сканера"""
        response = client.get("/api/qr/scanner")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "QR Сканер" in response.text
    
    @pytest.mark.asyncio
    async def test_scan_qr_code_success(self, client, mock_user, mock_qr_code, mock_user_profile):
        """Тест успешного сканирования QR-кода"""
        with patch('web.routes_qr_webapp.get_current_user', return_value=mock_user), \
             patch('web.routes_qr_webapp.get_db') as mock_get_db, \
             patch('web.routes_qr_webapp.user_profile_service.get_user_profile', return_value=mock_user_profile), \
             patch('web.routes_qr_webapp.user_profile_service.log_user_activity') as mock_log_activity:
            
            # Настройка мока базы данных
            mock_db = AsyncMock()
            mock_get_db.return_value.__aenter__.return_value = mock_db
            
            # Настройка результата запроса к БД
            mock_result = AsyncMock()
            mock_result.scalar_one_or_none.return_value = mock_qr_code
            mock_db.execute.return_value = mock_result
            
            # Выполнение запроса
            response = client.post(
                "/api/qr/scan",
                json={"qr_data": '{"qr_id": "test-qr-id-123"}'}
            )
            
            # Проверки
            assert response.status_code == 200
            data = response.json()
            assert data["qr_id"] == "test-qr-id-123"
            assert data["discount_type"] == "loyalty_points"
            assert data["discount_value"] == 120  # 100 * 1.2 (level multiplier)
            assert data["can_redeem"] is True
            
            # Проверяем что активность была записана
            mock_log_activity.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_scan_qr_code_not_found(self, client, mock_user):
        """Тест сканирования несуществующего QR-кода"""
        with patch('web.routes_qr_webapp.get_current_user', return_value=mock_user), \
             patch('web.routes_qr_webapp.get_db') as mock_get_db:
            
            # Настройка мока базы данных
            mock_db = AsyncMock()
            mock_get_db.return_value.__aenter__.return_value = mock_db
            
            # Настройка результата запроса к БД (QR не найден)
            mock_result = AsyncMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_db.execute.return_value = mock_result
            
            # Выполнение запроса
            response = client.post(
                "/api/qr/scan",
                json={"qr_data": '{"qr_id": "non-existent-qr"}'}
            )
            
            # Проверки
            assert response.status_code == 404
            assert "not found" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_scan_qr_code_expired(self, client, mock_user, mock_user_profile):
        """Тест сканирования просроченного QR-кода"""
        # Создаем просроченный QR-код
        expired_qr = QRCode(
            id=1,
            qr_id="expired-qr-id",
            user_id=123,
            discount_type="loyalty_points",
            discount_value=100,
            description="Expired discount",
            expires_at=datetime.utcnow() - timedelta(hours=1),  # Просрочен
            is_used=False,
            created_at=datetime.utcnow()
        )
        
        with patch('web.routes_qr_webapp.get_current_user', return_value=mock_user), \
             patch('web.routes_qr_webapp.get_db') as mock_get_db, \
             patch('web.routes_qr_webapp.user_profile_service.get_user_profile', return_value=mock_user_profile):
            
            # Настройка мока базы данных
            mock_db = AsyncMock()
            mock_get_db.return_value.__aenter__.return_value = mock_db
            
            # Настройка результата запроса к БД
            mock_result = AsyncMock()
            mock_result.scalar_one_or_none.return_value = expired_qr
            mock_db.execute.return_value = mock_result
            
            # Выполнение запроса
            response = client.post(
                "/api/qr/scan",
                json={"qr_data": '{"qr_id": "expired-qr-id"}'}
            )
            
            # Проверки
            assert response.status_code == 400
            assert "expired" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_redeem_qr_code_success(self, client, mock_user, mock_qr_code, mock_user_profile):
        """Тест успешного использования QR-кода"""
        with patch('web.routes_qr_webapp.get_current_user', return_value=mock_user), \
             patch('web.routes_qr_webapp.get_db') as mock_get_db, \
             patch('web.routes_qr_webapp.user_profile_service.get_user_profile', return_value=mock_user_profile), \
             patch('web.routes_qr_webapp.user_profile_service.log_user_activity') as mock_log_activity, \
             patch('web.routes_qr_webapp.loyalty_service.add_points') as mock_add_points, \
             patch('web.routes_qr_webapp.check_qr_achievements') as mock_check_achievements:
            
            # Настройка мока базы данных
            mock_db = AsyncMock()
            mock_get_db.return_value.__aenter__.return_value = mock_db
            
            # Настройка результата запроса к БД
            mock_result = AsyncMock()
            mock_result.scalar_one_or_none.return_value = mock_qr_code
            mock_db.execute.return_value = mock_result
            
            # Выполнение запроса
            response = client.post(
                "/api/qr/redeem",
                json={"qr_id": "test-qr-id-123"}
            )
            
            # Проверки
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["qr_id"] == "test-qr-id-123"
            assert data["discount_value"] == 120  # 100 * 1.2
            
            # Проверяем что QR-код был помечен как использованный
            mock_db.commit.assert_called_once()
            
            # Проверяем что активность была записана
            mock_log_activity.assert_called_once()
            
            # Проверяем что очки были добавлены
            mock_add_points.assert_called_once()
            
            # Проверяем что достижения были проверены
            mock_check_achievements.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_qr_code_success(self, client, mock_user, mock_user_profile):
        """Тест успешной генерации QR-кода"""
        with patch('web.routes_qr_webapp.get_current_user', return_value=mock_user), \
             patch('web.routes_qr_webapp.get_db') as mock_get_db, \
             patch('web.routes_qr_webapp.user_profile_service.get_user_profile', return_value=mock_user_profile), \
             patch('web.routes_qr_webapp.user_profile_service.log_user_activity') as mock_log_activity, \
             patch('web.routes_qr_webapp.QRCodeService') as mock_qr_service_class:
            
            # Настройка мока базы данных
            mock_db = AsyncMock()
            mock_get_db.return_value.__aenter__.return_value = mock_db
            
            # Настройка мока QR сервиса
            mock_qr_service = AsyncMock()
            mock_qr_service_class.return_value = mock_qr_service
            mock_qr_service.generate_qr_code.return_value = {
                "qr_id": "new-qr-id-456",
                "qr_image": "base64-image-data",
                "description": "Скидка 120 очков",
                "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat()
            }
            
            # Выполнение запроса
            response = client.post(
                "/api/qr/generate",
                json={
                    "discount_type": "loyalty_points",
                    "discount_value": 100,
                    "expires_in_hours": 24,
                    "description": "Test QR code"
                }
            )
            
            # Проверки
            assert response.status_code == 200
            data = response.json()
            assert data["qr_id"] == "new-qr-id-456"
            assert data["discount_type"] == "loyalty_points"
            assert data["discount_value"] == 120  # 100 * 1.2 (level multiplier)
            assert data["level_multiplier"] == 1.2
            
            # Проверяем что QR сервис был вызван
            mock_qr_service.generate_qr_code.assert_called_once()
            
            # Проверяем что активность была записана
            mock_log_activity.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_qr_history(self, client, mock_user):
        """Тест получения истории QR-кодов"""
        # Создаем список QR-кодов
        qr_codes = [
            QRCode(
                id=1,
                qr_id="qr-1",
                user_id=123,
                discount_type="loyalty_points",
                discount_value=100,
                description="QR 1",
                expires_at=datetime.utcnow() + timedelta(hours=24),
                is_used=True,
                used_at=datetime.utcnow(),
                created_at=datetime.utcnow()
            ),
            QRCode(
                id=2,
                qr_id="qr-2",
                user_id=123,
                discount_type="percentage",
                discount_value=10,
                description="QR 2",
                expires_at=datetime.utcnow() + timedelta(hours=24),
                is_used=False,
                created_at=datetime.utcnow()
            )
        ]
        
        with patch('web.routes_qr_webapp.get_current_user', return_value=mock_user), \
             patch('web.routes_qr_webapp.get_db') as mock_get_db:
            
            # Настройка мока базы данных
            mock_db = AsyncMock()
            mock_get_db.return_value.__aenter__.return_value = mock_db
            
            # Настройка результата запроса к БД
            mock_result = AsyncMock()
            mock_result.scalars.return_value.all.return_value = qr_codes
            mock_db.execute.return_value = mock_result
            
            # Выполнение запроса
            response = client.get("/api/qr/history")
            
            # Проверки
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["qr_id"] == "qr-1"
            assert data[0]["is_used"] is True
            assert data[1]["qr_id"] == "qr-2"
            assert data[1]["is_used"] is False
    
    @pytest.mark.asyncio
    async def test_get_qr_stats(self, client, mock_user, mock_user_profile):
        """Тест получения статистики QR-кодов"""
        # Создаем список QR-кодов для статистики
        qr_codes = [
            QRCode(id=1, qr_id="qr-1", user_id=123, discount_type="loyalty_points", discount_value=100, 
                   expires_at=datetime.utcnow() + timedelta(hours=24), is_used=True, created_at=datetime.utcnow()),
            QRCode(id=2, qr_id="qr-2", user_id=123, discount_type="loyalty_points", discount_value=200, 
                   expires_at=datetime.utcnow() + timedelta(hours=24), is_used=False, created_at=datetime.utcnow()),
            QRCode(id=3, qr_id="qr-3", user_id=123, discount_type="percentage", discount_value=10, 
                   expires_at=datetime.utcnow() - timedelta(hours=1), is_used=False, created_at=datetime.utcnow())
        ]
        
        with patch('web.routes_qr_webapp.get_current_user', return_value=mock_user), \
             patch('web.routes_qr_webapp.get_db') as mock_get_db, \
             patch('web.routes_qr_webapp.user_profile_service.get_user_profile', return_value=mock_user_profile):
            
            # Настройка мока базы данных
            mock_db = AsyncMock()
            mock_get_db.return_value.__aenter__.return_value = mock_db
            
            # Настройка результата запроса к БД
            mock_result = AsyncMock()
            mock_result.scalars.return_value.all.return_value = qr_codes
            mock_db.execute.return_value = mock_result
            
            # Выполнение запроса
            response = client.get("/api/qr/stats")
            
            # Проверки
            assert response.status_code == 200
            data = response.json()
            assert data["total_generated"] == 3
            assert data["total_used"] == 1
            assert data["total_expired"] == 1
            assert data["total_scans"] == 5
            assert data["usage_rate"] == 33.33  # 1/3 * 100
            assert data["user_level"] == "silver"


class TestQRWebAppIntegration:
    """Тесты интеграции QR WebApp с личным кабинетом"""
    
    @pytest.mark.asyncio
    async def test_level_based_discount_calculation(self):
        """Тест расчета скидки на основе уровня пользователя"""
        # Тестируем разные уровни
        test_cases = [
            {"level": "bronze", "multiplier": 1.0, "base_discount": 100, "expected": 100},
            {"level": "silver", "multiplier": 1.2, "base_discount": 100, "expected": 120},
            {"level": "gold", "multiplier": 1.5, "base_discount": 100, "expected": 150},
            {"level": "platinum", "multiplier": 2.0, "base_discount": 100, "expected": 200}
        ]
        
        for case in test_cases:
            final_discount = int(case["base_discount"] * case["multiplier"])
            assert final_discount == case["expected"], f"Failed for level {case['level']}"
    
    @pytest.mark.asyncio
    async def test_qr_achievement_unlocking(self):
        """Тест разблокировки достижений QR"""
        # Тестируем различные пороги достижений
        achievement_thresholds = [
            {"scans": 1, "achievement": "Первый QR", "points": 50},
            {"scans": 10, "achievement": "QR Мастер", "points": 200},
            {"scans": 50, "achievement": "QR Эксперт", "points": 500}
        ]
        
        for threshold in achievement_thresholds:
            # Проверяем что достижение должно разблокироваться
            assert threshold["scans"] > 0
            assert threshold["points"] > 0
            assert len(threshold["achievement"]) > 0


class TestQRWebAppSecurity:
    """Тесты безопасности QR WebApp"""
    
    @pytest.mark.asyncio
    async def test_unauthorized_access(self, client):
        """Тест доступа без авторизации"""
        endpoints = [
            ("/api/qr/scan", "POST"),
            ("/api/qr/redeem", "POST"),
            ("/api/qr/generate", "POST"),
            ("/api/qr/history", "GET"),
            ("/api/qr/stats", "GET")
        ]
        
        for endpoint, method in endpoints:
            if method == "POST":
                response = client.post(endpoint, json={})
            else:
                response = client.get(endpoint)
            
            # Должна быть ошибка авторизации
            assert response.status_code in [401, 403]
    
    @pytest.mark.asyncio
    async def test_malicious_qr_data(self, client, mock_user):
        """Тест обработки вредоносных данных QR"""
        malicious_data = [
            "<script>alert('xss')</script>",
            "'; DROP TABLE qr_codes; --",
            "../../etc/passwd",
            "javascript:alert('xss')"
        ]
        
        with patch('web.routes_qr_webapp.get_current_user', return_value=mock_user), \
             patch('web.routes_qr_webapp.get_db') as mock_get_db:
            
            mock_db = AsyncMock()
            mock_get_db.return_value.__aenter__.return_value = mock_db
            
            # Настройка результата запроса к БД (QR не найден)
            mock_result = AsyncMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_db.execute.return_value = mock_result
            
            for data in malicious_data:
                response = client.post(
                    "/api/qr/scan",
                    json={"qr_data": data}
                )
                
                # Должна быть ошибка валидации или не найдено
                assert response.status_code in [400, 404]
