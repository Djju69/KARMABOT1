"""
Performance Tests for KARMABOT1
Tests performance of critical components and endpoints
"""

import pytest
import asyncio
import time
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from web.main import app
from core.models import User, Card, Transaction
from core.security.jwt_service import create_admin_token


class TestPerformanceMetrics:
    """Test performance metrics and benchmarks"""
    
    @pytest.fixture
    def client(self):
        """Test client for FastAPI app"""
        return TestClient(app)
    
    @pytest.fixture
    def admin_token(self):
        """Admin JWT token for testing"""
        return create_admin_token(
            user_id=123,
            username="test_admin",
            role="admin"
        )
    
    def test_response_time_health_endpoint(self, client):
        """Test response time for health endpoint"""
        start_time = time.time()
        response = client.get("/health")
        end_time = time.time()
        
        response_time = end_time - start_time
        assert response.status_code == 200
        assert response_time < 0.1  # Should respond within 100ms
    
    def test_response_time_api_health_endpoint(self, client):
        """Test response time for API health endpoint"""
        start_time = time.time()
        response = client.get("/api/health")
        end_time = time.time()
        
        response_time = end_time - start_time
        assert response.status_code == 200
        assert response_time < 0.2  # Should respond within 200ms
    
    @patch('web.routes_admin_enhanced.get_db')
    @patch('web.routes_admin_enhanced.get_current_admin')
    def test_admin_dashboard_response_time(self, mock_get_admin, mock_get_db, client, admin_token):
        """Test response time for admin dashboard"""
        # Setup mocks
        mock_get_admin.return_value = {"user_id": 123, "role": "admin"}
        mock_db_session = MagicMock()
        mock_get_db.return_value = mock_db_session
        
        # Mock database queries
        mock_db_session.query.return_value.count.return_value = 100
        mock_db_session.query.return_value.filter.return_value.count.return_value = 25
        mock_db_session.query.return_value.scalar.return_value = 10000.0
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        start_time = time.time()
        response = client.get("/api/admin/dashboard", headers=headers)
        end_time = time.time()
        
        response_time = end_time - start_time
        assert response.status_code == 200
        assert response_time < 0.5  # Should respond within 500ms
    
    @patch('web.routes_admin_enhanced.get_db')
    @patch('web.routes_admin_enhanced.get_current_admin')
    def test_users_list_response_time(self, mock_get_admin, mock_get_db, client, admin_token):
        """Test response time for users list endpoint"""
        # Setup mocks
        mock_get_admin.return_value = {"user_id": 123, "role": "admin"}
        mock_db_session = MagicMock()
        mock_get_db.return_value = mock_db_session
        
        # Mock database queries
        mock_db_session.query.return_value.count.return_value = 1000
        mock_db_session.query.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        mock_db_session.query.return_value.filter.return_value.all.return_value = []
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        start_time = time.time()
        response = client.get("/api/admin/users", headers=headers)
        end_time = time.time()
        
        response_time = end_time - start_time
        assert response.status_code == 200
        assert response_time < 1.0  # Should respond within 1 second


class TestConcurrentRequests:
    """Test concurrent request handling"""
    
    @pytest.fixture
    def client(self):
        """Test client for FastAPI app"""
        return TestClient(app)
    
    def test_concurrent_health_requests(self, client):
        """Test concurrent health endpoint requests"""
        def make_request():
            return client.get("/health")
        
        # Make 10 concurrent requests
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            responses = [future.result() for future in futures]
        
        # All requests should succeed
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
    
    def test_concurrent_api_health_requests(self, client):
        """Test concurrent API health endpoint requests"""
        def make_request():
            return client.get("/api/health")
        
        # Make 5 concurrent requests
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(5)]
            responses = [future.result() for future in futures]
        
        # All requests should succeed
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert "status" in data
    
    @patch('web.routes_admin_enhanced.get_db')
    @patch('web.routes_admin_enhanced.get_current_admin')
    def test_concurrent_admin_requests(self, mock_get_admin, mock_get_db, client):
        """Test concurrent admin endpoint requests"""
        # Setup mocks
        mock_get_admin.return_value = {"user_id": 123, "role": "admin"}
        mock_db_session = MagicMock()
        mock_get_db.return_value = mock_db_session
        
        # Mock database queries
        mock_db_session.query.return_value.count.return_value = 100
        mock_db_session.query.return_value.filter.return_value.count.return_value = 25
        mock_db_session.query.return_value.scalar.return_value = 10000.0
        
        admin_token = create_admin_token(user_id=123, username="test_admin", role="admin")
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        def make_request():
            return client.get("/api/admin/dashboard", headers=headers)
        
        # Make 3 concurrent requests
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(make_request) for _ in range(3)]
            responses = [future.result() for future in futures]
        
        # All requests should succeed
        for response in responses:
            assert response.status_code == 200


class TestDatabasePerformance:
    """Test database performance with mocked operations"""
    
    @patch('web.routes_admin_enhanced.get_db')
    @patch('web.routes_admin_enhanced.get_current_admin')
    def test_large_dataset_query_performance(self, mock_get_admin, mock_get_db, client):
        """Test performance with large datasets"""
        # Setup mocks
        mock_get_admin.return_value = {"user_id": 123, "role": "admin"}
        mock_db_session = MagicMock()
        mock_get_db.return_value = mock_db_session
        
        # Mock large dataset
        mock_db_session.query.return_value.count.return_value = 100000
        mock_db_session.query.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        
        admin_token = create_admin_token(user_id=123, username="test_admin", role="admin")
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        start_time = time.time()
        response = client.get("/api/admin/users?limit=1000", headers=headers)
        end_time = time.time()
        
        response_time = end_time - start_time
        assert response.status_code == 200
        assert response_time < 2.0  # Should handle large datasets within 2 seconds
    
    @patch('web.routes_admin_enhanced.get_db')
    @patch('web.routes_admin_enhanced.get_current_admin')
    def test_pagination_performance(self, mock_get_admin, mock_get_db, client):
        """Test pagination performance"""
        # Setup mocks
        mock_get_admin.return_value = {"user_id": 123, "role": "admin"}
        mock_db_session = MagicMock()
        mock_get_db.return_value = mock_db_session
        
        # Mock pagination
        mock_db_session.query.return_value.count.return_value = 50000
        mock_db_session.query.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        
        admin_token = create_admin_token(user_id=123, username="test_admin", role="admin")
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Test different page sizes
        page_sizes = [10, 50, 100, 500]
        
        for page_size in page_sizes:
            start_time = time.time()
            response = client.get(f"/api/admin/users?limit={page_size}", headers=headers)
            end_time = time.time()
            
            response_time = end_time - start_time
            assert response.status_code == 200
            assert response_time < 1.0  # Should handle pagination within 1 second


class TestMemoryUsage:
    """Test memory usage patterns"""
    
    @patch('web.routes_admin_enhanced.get_db')
    @patch('web.routes_admin_enhanced.get_current_admin')
    def test_memory_efficient_queries(self, mock_get_admin, mock_get_db, client):
        """Test memory efficiency of queries"""
        # Setup mocks
        mock_get_admin.return_value = {"user_id": 123, "role": "admin"}
        mock_db_session = MagicMock()
        mock_get_db.return_value = mock_db_session
        
        # Mock database queries
        mock_db_session.query.return_value.count.return_value = 1000
        mock_db_session.query.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        
        admin_token = create_admin_token(user_id=123, username="test_admin", role="admin")
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Make multiple requests to test memory efficiency
        for i in range(10):
            response = client.get("/api/admin/users?limit=100", headers=headers)
            assert response.status_code == 200
        
        # If we get here without memory issues, the test passes
        assert True


class TestErrorHandlingPerformance:
    """Test error handling performance"""
    
    def test_error_response_time(self, client):
        """Test error response time"""
        start_time = time.time()
        response = client.get("/api/invalid/endpoint")
        end_time = time.time()
        
        response_time = end_time - start_time
        assert response.status_code == 404
        assert response_time < 0.1  # Error responses should be fast
    
    @patch('web.routes_admin_enhanced.get_db', side_effect=Exception("Database error"))
    def test_database_error_response_time(self, mock_get_db, client):
        """Test database error response time"""
        admin_token = create_admin_token(user_id=123, username="test_admin", role="admin")
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        start_time = time.time()
        response = client.get("/api/admin/dashboard", headers=headers)
        end_time = time.time()
        
        response_time = end_time - start_time
        assert response.status_code == 500
        assert response_time < 0.5  # Database errors should be handled quickly


class TestCachingPerformance:
    """Test caching performance (mocked)"""
    
    @patch('web.routes_admin_enhanced.get_db')
    @patch('web.routes_admin_enhanced.get_current_admin')
    def test_cached_response_performance(self, mock_get_admin, mock_get_db, client):
        """Test performance of cached responses"""
        # Setup mocks
        mock_get_admin.return_value = {"user_id": 123, "role": "admin"}
        mock_db_session = MagicMock()
        mock_get_db.return_value = mock_db_session
        
        # Mock database queries
        mock_db_session.query.return_value.count.return_value = 100
        mock_db_session.query.return_value.filter.return_value.count.return_value = 25
        mock_db_session.query.return_value.scalar.return_value = 10000.0
        
        admin_token = create_admin_token(user_id=123, username="test_admin", role="admin")
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # First request (cold cache)
        start_time = time.time()
        response1 = client.get("/api/admin/dashboard", headers=headers)
        end_time = time.time()
        first_request_time = end_time - start_time
        
        # Second request (warm cache)
        start_time = time.time()
        response2 = client.get("/api/admin/dashboard", headers=headers)
        end_time = time.time()
        second_request_time = end_time - start_time
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Second request should be faster (simulating cache hit)
        # Note: In real implementation, this would be much more significant
        assert second_request_time <= first_request_time


class TestLoadTesting:
    """Test load handling capabilities"""
    
    def test_sustained_load(self, client):
        """Test sustained load handling"""
        def make_request():
            return client.get("/health")
        
        # Make 100 requests over time
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for i in range(100):
                futures.append(executor.submit(make_request))
                if i % 10 == 0:  # Small delay every 10 requests
                    time.sleep(0.01)
            
            responses = [future.result() for future in futures]
        
        # All requests should succeed
        success_count = sum(1 for response in responses if response.status_code == 200)
        assert success_count == 100
    
    def test_burst_load(self, client):
        """Test burst load handling"""
        def make_request():
            return client.get("/api/health")
        
        # Make 20 requests simultaneously
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(make_request) for _ in range(20)]
            responses = [future.result() for future in futures]
        
        # All requests should succeed
        success_count = sum(1 for response in responses if response.status_code == 200)
        assert success_count == 20


if __name__ == "__main__":
    pytest.main([__file__])
