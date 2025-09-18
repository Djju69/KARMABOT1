"""
Comprehensive Integration Tests for KARMABOT1 API
Tests all major API endpoints and workflows
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy.orm import Session

from web.main import app
from core.models import User, Card, Transaction, Partner, ModerationLog
from core.security.jwt_service import create_admin_token


class TestComprehensiveAPI:
    """Comprehensive API integration tests"""
    
    @pytest.fixture
    def client(self):
        """Test client for FastAPI app"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        return MagicMock(spec=Session)
    
    @pytest.fixture
    def admin_token(self):
        """Admin JWT token for testing"""
        return create_admin_token(
            user_id=123,
            username="test_admin",
            role="admin"
        )
    
    @pytest.fixture
    def superadmin_token(self):
        """Super admin JWT token for testing"""
        return create_admin_token(
            user_id=456,
            username="test_superadmin",
            role="superadmin"
        )
    
    @pytest.fixture
    def sample_user(self):
        """Sample user data"""
        return User(
            id=1,
            full_name="Test User",
            username="testuser",
            email="test@example.com",
            role="user",
            is_active=True,
            created_at=datetime.utcnow()
        )
    
    @pytest.fixture
    def sample_partner(self):
        """Sample partner data"""
        return Partner(
            id=1,
            name="Test Partner",
            description="Test partner description",
            category="restaurant",
            address="Test Address",
            phone="+1234567890",
            email="partner@example.com",
            is_active=True,
            created_at=datetime.utcnow()
        )
    
    @pytest.fixture
    def sample_card(self):
        """Sample card data"""
        return Card(
            id=1,
            partner_id=1,
            title="Test Card",
            description="Test card description",
            category="restaurant",
            status="pending",
            created_at=datetime.utcnow()
        )
    
    @pytest.fixture
    def sample_transaction(self):
        """Sample transaction data"""
        return Transaction(
            id=1,
            user_id=1,
            partner_id=1,
            amount=100.0,
            transaction_type="purchase",
            created_at=datetime.utcnow()
        )

class TestHealthEndpoints:
    """Test health and status endpoints"""
    
    def test_health_endpoint(self, client):
        """Test basic health endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
    
    def test_api_health_endpoint(self, client):
        """Test API health endpoint"""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data

class TestAuthenticationFlow:
    """Test authentication and authorization flows"""
    
    def test_unauthorized_access(self, client):
        """Test unauthorized access to protected endpoints"""
        response = client.get("/api/admin/dashboard")
        assert response.status_code == 401
    
    def test_admin_authentication(self, client, admin_token):
        """Test admin authentication"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/admin/dashboard", headers=headers)
        # Should not return 401 (might return 500 due to mock DB)
        assert response.status_code != 401
    
    def test_superadmin_authentication(self, client, superadmin_token):
        """Test super admin authentication"""
        headers = {"Authorization": f"Bearer {superadmin_token}"}
        response = client.get("/api/admin/dashboard", headers=headers)
        # Should not return 401 (might return 500 due to mock DB)
        assert response.status_code != 401

class TestAdminPanelAPI:
    """Test admin panel API endpoints"""
    
    @patch('web.routes_admin_enhanced.get_db')
    @patch('web.routes_admin_enhanced.get_current_admin')
    def test_admin_dashboard(self, mock_get_admin, mock_get_db, client, admin_token, mock_db_session):
        """Test admin dashboard endpoint"""
        # Setup mocks
        mock_get_admin.return_value = {"user_id": 123, "role": "admin"}
        mock_get_db.return_value = mock_db_session
        
        # Mock database queries
        mock_db_session.query.return_value.count.return_value = 100
        mock_db_session.query.return_value.filter.return_value.count.return_value = 25
        mock_db_session.query.return_value.scalar.return_value = 10000.0
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/admin/dashboard", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "total_users" in data
        assert "active_partners" in data
        assert "pending_moderation" in data
        assert "today_transactions" in data
    
    @patch('web.routes_admin_enhanced.get_db')
    @patch('web.routes_admin_enhanced.get_current_admin')
    def test_admin_users_list(self, mock_get_admin, mock_get_db, client, admin_token, mock_db_session, sample_user):
        """Test admin users list endpoint"""
        # Setup mocks
        mock_get_admin.return_value = {"user_id": 123, "role": "admin"}
        mock_get_db.return_value = mock_db_session
        
        # Mock database queries
        mock_db_session.query.return_value.count.return_value = 1
        mock_db_session.query.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [sample_user]
        mock_db_session.query.return_value.filter.return_value.all.return_value = []
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/admin/users", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "total" in data
        assert "current_page" in data
    
    @patch('web.routes_admin_enhanced.get_db')
    @patch('web.routes_admin_enhanced.get_current_admin')
    def test_admin_users_search(self, mock_get_admin, mock_get_db, client, admin_token, mock_db_session, sample_user):
        """Test admin users search functionality"""
        # Setup mocks
        mock_get_admin.return_value = {"user_id": 123, "role": "admin"}
        mock_get_db.return_value = mock_db_session
        
        # Mock database queries
        mock_db_session.query.return_value.count.return_value = 1
        mock_db_session.query.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [sample_user]
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/admin/users?search=test", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "filters" in data
        assert data["filters"]["search"] == "test"
    
    @patch('web.routes_admin_enhanced.get_db')
    @patch('web.routes_admin_enhanced.get_current_admin')
    def test_recent_activity(self, mock_get_admin, mock_get_db, client, admin_token, mock_db_session, sample_user):
        """Test recent activity endpoint"""
        # Setup mocks
        mock_get_admin.return_value = {"user_id": 123, "role": "admin"}
        mock_get_db.return_value = mock_db_session
        
        # Mock database queries
        mock_db_session.query.return_value.order_by.return_value.limit.return_value.all.return_value = [sample_user]
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/admin/activity", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    @patch('web.routes_admin_enhanced.get_db')
    @patch('web.routes_admin_enhanced.get_current_admin')
    def test_analytics_data(self, mock_get_admin, mock_get_db, client, admin_token, mock_db_session):
        """Test analytics data endpoint"""
        # Setup mocks
        mock_get_admin.return_value = {"user_id": 123, "role": "admin"}
        mock_get_db.return_value = mock_db_session
        
        # Mock database queries
        mock_db_session.query.return_value.filter.return_value.count.return_value = 5
        mock_db_session.query.return_value.scalar.return_value = 1000.0
        mock_db_session.query.return_value.join.return_value.filter.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = []
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/admin/analytics", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "period" in data
        assert "users_growth" in data
        assert "transactions_trend" in data
        assert "revenue_breakdown" in data
    
    @patch('web.routes_admin_enhanced.get_db')
    @patch('web.routes_admin_enhanced.get_current_admin')
    def test_system_health(self, mock_get_admin, mock_get_db, client, admin_token, mock_db_session, sample_user):
        """Test system health endpoint"""
        # Setup mocks
        mock_get_admin.return_value = {"user_id": 123, "role": "admin"}
        mock_get_db.return_value = mock_db_session
        
        # Mock database query
        mock_db_session.query.return_value.limit.return_value.first.return_value = sample_user
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/admin/health", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "uptime" in data
        assert "memory_usage" in data
        assert "cpu_usage" in data
        assert "disk_usage" in data

class TestUserManagementAPI:
    """Test user management API endpoints"""
    
    @patch('web.routes_admin_enhanced.get_db')
    @patch('web.routes_admin_enhanced.get_current_admin')
    def test_toggle_user_status(self, mock_get_admin, mock_get_db, client, admin_token, mock_db_session, sample_user):
        """Test toggle user status endpoint"""
        # Setup mocks
        mock_get_admin.return_value = {"user_id": 123, "role": "admin"}
        mock_get_db.return_value = mock_db_session
        
        # Mock database query
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_user
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.post("/api/admin/users/1/toggle-status", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "message" in data
        assert data["user_id"] == 1
    
    @patch('web.routes_admin_enhanced.get_db')
    @patch('web.routes_admin_enhanced.get_current_admin')
    def test_change_user_role(self, mock_get_admin, mock_get_db, client, admin_token, mock_db_session, sample_user):
        """Test change user role endpoint"""
        # Setup mocks
        mock_get_admin.return_value = {"user_id": 123, "role": "admin"}
        mock_get_db.return_value = mock_db_session
        
        # Mock database query
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_user
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.post("/api/admin/users/1/change-role?new_role=partner", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["old_role"] == "user"
        assert data["new_role"] == "partner"
    
    @patch('web.routes_admin_enhanced.get_db')
    @patch('web.routes_admin_enhanced.get_current_admin')
    def test_change_user_role_invalid(self, mock_get_admin, mock_get_db, client, admin_token, mock_db_session):
        """Test change user role with invalid role"""
        # Setup mocks
        mock_get_admin.return_value = {"user_id": 123, "role": "admin"}
        mock_get_db.return_value = mock_db_session
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.post("/api/admin/users/1/change-role?new_role=invalid_role", headers=headers)
        
        assert response.status_code == 400
    
    @patch('web.routes_admin_enhanced.get_db')
    @patch('web.routes_admin_enhanced.get_current_admin')
    def test_export_users(self, mock_get_admin, mock_get_db, client, admin_token, mock_db_session, sample_user):
        """Test export users endpoint"""
        # Setup mocks
        mock_get_admin.return_value = {"user_id": 123, "role": "admin"}
        mock_get_db.return_value = mock_db_session
        
        # Mock database query
        mock_db_session.query.return_value.all.return_value = [sample_user]
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/admin/export/users", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "total" in data

class TestSystemLogsAPI:
    """Test system logs API endpoints"""
    
    @patch('web.routes_admin_enhanced.get_current_admin')
    def test_system_logs(self, mock_get_admin, client, admin_token):
        """Test system logs endpoint"""
        # Setup mocks
        mock_get_admin.return_value = {"user_id": 123, "role": "admin"}
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/admin/logs", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "logs" in data
        assert "total" in data
        assert isinstance(data["logs"], list)
    
    @patch('web.routes_admin_enhanced.get_current_admin')
    def test_system_logs_with_level(self, mock_get_admin, client, admin_token):
        """Test system logs with level filter"""
        # Setup mocks
        mock_get_admin.return_value = {"user_id": 123, "role": "admin"}
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/admin/logs?level=ERROR", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "logs" in data
        assert "total" in data

class TestWebAppIntegration:
    """Test WebApp integration endpoints"""
    
    def test_admin_dashboard_enhanced_template(self, client):
        """Test admin dashboard enhanced template serving"""
        response = client.get("/api/admin/dashboard-enhanced")
        
        # Should return HTML content
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert b"Админ-панель" in response.content
        assert b"KARMABOT1" in response.content

class TestErrorHandling:
    """Test error handling across API endpoints"""
    
    def test_invalid_endpoint(self, client):
        """Test invalid endpoint returns 404"""
        response = client.get("/api/invalid/endpoint")
        assert response.status_code == 404
    
    def test_method_not_allowed(self, client):
        """Test method not allowed returns 405"""
        response = client.post("/health")
        assert response.status_code == 405
    
    def test_internal_server_error_handling(self, client, admin_token):
        """Test internal server error handling"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # This should trigger an error due to missing DB setup
        with patch('web.routes_admin_enhanced.get_db', side_effect=Exception("Database error")):
            response = client.get("/api/admin/dashboard", headers=headers)
            assert response.status_code == 500

class TestPerformanceEndpoints:
    """Test performance-related endpoints"""
    
    @patch('web.routes_admin_enhanced.get_db')
    @patch('web.routes_admin_enhanced.get_current_admin')
    def test_large_dataset_handling(self, mock_get_admin, mock_get_db, client, admin_token, mock_db_session):
        """Test handling of large datasets"""
        # Setup mocks
        mock_get_admin.return_value = {"user_id": 123, "role": "admin"}
        mock_get_db.return_value = mock_db_session
        
        # Mock large dataset
        mock_db_session.query.return_value.count.return_value = 10000
        mock_db_session.query.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/admin/users?limit=100", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 10000
        assert data["current_page"] == 1
    
    @patch('web.routes_admin_enhanced.get_db')
    @patch('web.routes_admin_enhanced.get_current_admin')
    def test_pagination_performance(self, mock_get_admin, mock_get_db, client, admin_token, mock_db_session):
        """Test pagination performance"""
        # Setup mocks
        mock_get_admin.return_value = {"user_id": 123, "role": "admin"}
        mock_get_db.return_value = mock_db_session
        
        # Mock pagination
        mock_db_session.query.return_value.count.return_value = 1000
        mock_db_session.query.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/admin/users?page=50&limit=20", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["current_page"] == 50
        assert data["total_pages"] == 50
        assert data["has_next"] is False
        assert data["has_previous"] is True

if __name__ == "__main__":
    pytest.main([__file__])
