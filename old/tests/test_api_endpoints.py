import pytest
import asyncio
import json
import os
import sys
from datetime import datetime
from fastapi.testclient import TestClient

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from api.platform_endpoints import *
from core.database.enhanced_unified_service import enhanced_unified_db

class TestAPIEndpoints:
    """Тесты для API endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup_api(self):
        """Настройка API перед тестами"""
        self.client = TestClient(app)
        # Инициализируем базы данных
        enhanced_unified_db.init_databases()
        yield
        # Очистка после тестов (если нужно)
    
    def test_root_endpoint(self):
        """Тест корневого endpoint"""
        print("🧪 Testing root endpoint...")
        
        response = self.client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["service"] == "🛡️ Fault-Tolerant Multi-Platform System"
        assert data["version"] == "1.0.0"
        assert "platforms" in data
        assert "features" in data
        
        print("✅ Root endpoint working correctly")
    
    def test_status_endpoint(self):
        """Тест endpoint статуса"""
        print("🧪 Testing status endpoint...")
        
        response = self.client.get("/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "mode" in data
        assert "databases" in data
        assert "uptime" in data
        
        print("✅ Status endpoint working correctly")
    
    def test_platforms_endpoint(self):
        """Тест endpoint платформ"""
        print("🧪 Testing platforms endpoint...")
        
        response = self.client.get("/v1/platforms")
        assert response.status_code == 200
        
        data = response.json()
        assert "platforms" in data
        assert "universal" in data
        assert "admin" in data
        
        # Проверяем наличие всех платформ
        platforms = data["platforms"]
        expected_platforms = ["telegram", "website", "mobile", "desktop", "api"]
        
        for platform in expected_platforms:
            assert platform in platforms
        
        print("✅ Platforms endpoint working correctly")
    
    def test_telegram_user_creation(self):
        """Тест создания пользователя Telegram через API"""
        print("🧪 Testing Telegram user creation via API...")
        
        user_data = {
            "telegram_id": 123456789,
            "username": "test_api_user",
            "first_name": "Test",
            "last_name": "API"
        }
        
        response = self.client.post("/v1/telegram/users/", json=user_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert "user_uuid" in data
        assert data["platform"] == "telegram"
        
        print("✅ Telegram user creation via API working correctly")
    
    def test_website_user_creation(self):
        """Тест создания пользователя Website через API"""
        print("🧪 Testing Website user creation via API...")
        
        user_data = {
            "email": "test_api@example.com",
            "username": "test_web_user",
            "first_name": "Test",
            "last_name": "Web"
        }
        
        response = self.client.post("/v1/website/users/", json=user_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert "user_uuid" in data
        assert data["platform"] == "website"
        
        print("✅ Website user creation via API working correctly")
    
    def test_mobile_user_creation(self):
        """Тест создания пользователя Mobile через API"""
        print("🧪 Testing Mobile user creation via API...")
        
        user_data = {
            "device_id": "test_device_123",
            "platform": "ios",
            "username": "test_mobile_user",
            "first_name": "Test",
            "app_version": "1.0.0"
        }
        
        response = self.client.post("/v1/mobile/users/", json=user_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert "user_uuid" in data
        assert data["platform"] == "mobile_ios"
        
        print("✅ Mobile user creation via API working correctly")
    
    def test_desktop_user_creation(self):
        """Тест создания пользователя Desktop через API"""
        print("🧪 Testing Desktop user creation via API...")
        
        user_data = {
            "user_id": "test_desktop_123",
            "platform": "windows",
            "username": "test_desktop_user",
            "first_name": "Test",
            "app_version": "1.0.0"
        }
        
        response = self.client.post("/v1/desktop/users/", json=user_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert "user_uuid" in data
        assert data["platform"] == "desktop_windows"
        
        print("✅ Desktop user creation via API working correctly")
    
    def test_order_creation_telegram(self):
        """Тест создания заказа через Telegram API"""
        print("🧪 Testing Telegram order creation via API...")
        
        # Сначала создаем пользователя
        user_data = {"telegram_id": 987654321, "first_name": "Order"}
        self.client.post("/v1/telegram/users/", json=user_data)
        
        # Создаем заказ
        order_data = {
            "items": [{"name": "Test Product", "price": 25.0}],
            "total_amount": 25.0,
            "currency": "USD"
        }
        
        response = self.client.post("/v1/telegram/users/987654321/orders", json=order_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert "order_id" in data
        assert data["platform"] == "telegram"
        
        print("✅ Telegram order creation via API working correctly")
    
    def test_cross_platform_order(self):
        """Тест кросс-платформенного заказа"""
        print("🧪 Testing cross-platform order via API...")
        
        # Создаем пользователей на разных платформах
        telegram_data = {"telegram_id": 111222333, "first_name": "Cross"}
        website_data = {"email": "cross@example.com", "first_name": "Cross"}
        
        self.client.post("/v1/telegram/users/", json=telegram_data)
        self.client.post("/v1/website/users/", json=website_data)
        
        # Создаем кросс-платформенный заказ
        order_data = {
            "user_identifiers": {
                "telegram_id": 111222333,
                "email": "cross@example.com"
            },
            "primary_platform": "telegram",
            "order_details": {
                "items": [{"name": "Cross Product", "price": 50.0}],
                "total_amount": 50.0,
                "currency": "USD"
            }
        }
        
        response = self.client.post("/v1/universal/orders/cross-platform", json=order_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert "order_id" in data
        assert data["primary_platform"] == "telegram"
        
        print("✅ Cross-platform order via API working correctly")
    
    def test_unified_loyalty(self):
        """Тест объединенной системы лояльности"""
        print("🧪 Testing unified loyalty via API...")
        
        # Создаем связанных пользователей
        telegram_data = {"telegram_id": 444555666, "first_name": "Loyalty"}
        website_data = {"email": "loyalty@example.com", "first_name": "Loyalty"}
        
        self.client.post("/v1/telegram/users/", json=telegram_data)
        self.client.post("/v1/website/users/", json=website_data)
        
        # Связываем аккаунты
        link_data = {"telegram_id": 444555666}
        self.client.post("/v1/website/users/loyalty@example.com/link-telegram", json=link_data)
        
        # Получаем объединенную лояльность
        identifiers = {
            "telegram_id": 444555666,
            "email": "loyalty@example.com"
        }
        
        response = self.client.post("/v1/universal/loyalty/unified", json=identifiers)
        assert response.status_code == 200
        
        data = response.json()
        assert "current_points" in data
        assert "partner_cards" in data
        
        print("✅ Unified loyalty via API working correctly")
    
    def test_admin_health_endpoint(self):
        """Тест админского endpoint здоровья"""
        print("🧪 Testing admin health endpoint...")
        
        response = self.client.get("/v1/admin/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "mode" in data
        assert "timestamp" in data
        assert "uptime" in data
        
        print("✅ Admin health endpoint working correctly")
    
    def test_admin_status_with_auth(self):
        """Тест админского статуса с авторизацией"""
        print("🧪 Testing admin status with authentication...")
        
        headers = {"Authorization": "Bearer admin_secret_token_2025"}
        response = self.client.get("/v1/admin/status", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "system_status" in data
        assert "alerts" in data
        assert "recommendations" in data
        
        print("✅ Admin status with auth working correctly")
    
    def test_api_key_validation(self):
        """Тест валидации API ключей"""
        print("🧪 Testing API key validation...")
        
        # Тест с валидным ключом
        headers = {"X-API-Key": "pk_live_test123"}
        order_data = {
            "external_user_id": "test_external_123",
            "order_details": {
                "items": [{"name": "API Product", "price": 30.0}],
                "total_amount": 30.0
            }
        }
        
        response = self.client.post("/v1/api/orders", json=order_data, headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert "order_id" in data
        
        print("✅ API key validation working correctly")
    
    def test_invalid_api_key(self):
        """Тест с невалидным API ключом"""
        print("🧪 Testing invalid API key...")
        
        headers = {"X-API-Key": "invalid_key"}
        order_data = {
            "external_user_id": "test_external_123",
            "order_details": {"total_amount": 30.0}
        }
        
        response = self.client.post("/v1/api/orders", json=order_data, headers=headers)
        assert response.status_code == 403
        
        data = response.json()
        assert "detail" in data
        assert "Invalid API key" in data["detail"]
        
        print("✅ Invalid API key rejection working correctly")
    
    def test_dashboard_endpoint(self):
        """Тест dashboard endpoint"""
        print("🧪 Testing dashboard endpoint...")
        
        response = self.client.get("/dashboard")
        assert response.status_code == 200
        
        # Проверяем, что возвращается HTML
        content = response.text
        assert "<!DOCTYPE html>" in content
        assert "Fault-Tolerant System Dashboard" in content
        
        print("✅ Dashboard endpoint working correctly")
    
    def test_error_handling(self):
        """Тест обработки ошибок"""
        print("🧪 Testing error handling...")
        
        # Тест 404 ошибки
        response = self.client.get("/nonexistent-endpoint")
        assert response.status_code == 404
        
        data = response.json()
        assert "error" in data
        assert "Not Found" in data["error"]
        
        # Тест валидации данных
        invalid_user_data = {
            "telegram_id": -1,  # Невалидный ID
            "username": "test"
        }
        
        response = self.client.post("/v1/telegram/users/", json=invalid_user_data)
        assert response.status_code == 422  # Validation error
        
        print("✅ Error handling working correctly")
    
    def test_cors_headers(self):
        """Тест CORS заголовков"""
        print("🧪 Testing CORS headers...")
        
        response = self.client.options("/v1/telegram/users/")
        assert response.status_code == 200
        
        # Проверяем CORS заголовки
        headers = response.headers
        assert "access-control-allow-origin" in headers
        assert "access-control-allow-methods" in headers
        
        print("✅ CORS headers working correctly")

def run_api_tests():
    """Запустить все API тесты"""
    print("🚀 Starting API Endpoints Tests")
    print("=" * 60)
    
    test_suite = TestAPIEndpoints()
    test_suite.setup_api()
    
    # Список всех тестов
    tests = [
        test_suite.test_root_endpoint,
        test_suite.test_status_endpoint,
        test_suite.test_platforms_endpoint,
        test_suite.test_telegram_user_creation,
        test_suite.test_website_user_creation,
        test_suite.test_mobile_user_creation,
        test_suite.test_desktop_user_creation,
        test_suite.test_order_creation_telegram,
        test_suite.test_cross_platform_order,
        test_suite.test_unified_loyalty,
        test_suite.test_admin_health_endpoint,
        test_suite.test_admin_status_with_auth,
        test_suite.test_api_key_validation,
        test_suite.test_invalid_api_key,
        test_suite.test_dashboard_endpoint,
        test_suite.test_error_handling,
        test_suite.test_cors_headers
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} FAILED: {e}")
            failed += 1
    
    print("=" * 60)
    print(f"🏁 API Tests completed: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("✅ ALL API TESTS PASSED! API is fully operational.")
    else:
        print("⚠️ Some API tests failed. Please check the implementation.")
    
    return failed == 0

if __name__ == "__main__":
    success = run_api_tests()
    exit(0 if success else 1)
