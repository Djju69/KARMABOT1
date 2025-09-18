#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for Admin Panel API
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from web.app import app
from core.models import User, Card, Transaction


class TestAdminPanelAPI:
    """Test cases for Admin Panel API"""
    
    @pytest.fixture
    def client(self):
        """Test client"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_admin_token(self):
        """Mock admin JWT token"""
        return "mock_admin_token_12345"
    
    @pytest.fixture
    def mock_admin_claims(self):
        """Mock admin JWT claims"""
        return {
            "sub": "12345",
            "role": "admin",
            "exp": int((datetime.utcnow() + timedelta(hours=1)).timestamp())
        }
    
    @pytest.fixture
    def sample_users(self):
        """Sample users data"""
        return [
            User(
                id=1,
                full_name="Test User 1",
                email="user1@test.com",
                role="user",
                is_active=True,
                created_at=datetime.utcnow()
            ),
            User(
                id=2,
                full_name="Test Partner",
                email="partner@test.com",
                role="partner",
                is_active=True,
                created_at=datetime.utcnow()
            )
        ]
    
    @pytest.fixture
    def sample_cards(self):
        """Sample cards data"""
        return [
            Card(
                id=1,
                title="Test Card 1",
                status="pending",
                partner_id=2,
                created_at=datetime.utcnow()
            ),
            Card(
                id=2,
                title="Test Card 2",
                status="approved",
                partner_id=2,
                created_at=datetime.utcnow()
            )
        ]
    
    @pytest.fixture
    def sample_transactions(self):
        """Sample transactions data"""
        return [
            Transaction(
                id=1,
                user_id=1,
                type="earn",
                amount=100,
                status="completed",
                created_at=datetime.utcnow()
            ),
            Transaction(
                id=2,
                user_id=2,
                type="spend",
                amount=50,
                status="completed",
                created_at=datetime.utcnow()
            )
        ]
    
    @patch('web.routes_admin_panel.verify_admin_token')
    def test_get_admin_dashboard_success(self, mock_verify_token, client, mock_admin_claims):
        """Test successful admin dashboard retrieval"""
        mock_verify_token.return_value = mock_admin_claims
        
        with patch('web.routes_admin_panel.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value.__enter__.return_value = mock_db
            
            # Mock database queries
            mock_db.query.return_value.count.return_value = 10  # total_users
            mock_db.query.return_value.filter.return_value.count.return_value = 5  # active_partners
            mock_db.query.return_value.filter.return_value.count.return_value = 3  # pending_moderation
            mock_db.query.return_value.filter.return_value.count.return_value = 7  # today_transactions
            
            response = client.get(
                "/api/admin/dashboard",
                headers={"Authorization": f"Bearer {mock_admin_claims['sub']}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["total_users"] == 10
            assert data["active_partners"] == 5
            assert data["pending_moderation"] == 3
            assert data["today_transactions"] == 7
    
    def test_get_admin_dashboard_unauthorized(self, client):
        """Test admin dashboard without authentication"""
        response = client.get("/api/admin/dashboard")
        
        assert response.status_code == 401
        assert "Missing authentication token" in response.json()["detail"]
    
    @patch('web.routes_admin_panel.verify_admin_token')
    def test_get_admin_users_success(self, mock_verify_token, client, mock_admin_claims, sample_users):
        """Test successful admin users retrieval"""
        mock_verify_token.return_value = mock_admin_claims
        
        with patch('web.routes_admin_panel.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value.__enter__.return_value = mock_db
            
            # Mock database queries
            mock_query = Mock()
            mock_query.count.return_value = 2
            mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = sample_users
            
            mock_db.query.return_value = mock_query
            
            response = client.get(
                "/api/admin/users",
                headers={"Authorization": f"Bearer {mock_admin_claims['sub']}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["users"]) == 2
            assert data["total"] == 2
            assert data["current_page"] == 1
            assert data["users"][0]["full_name"] == "Test User 1"
            assert data["users"][1]["role"] == "partner"
    
    @patch('web.routes_admin_panel.verify_admin_token')
    def test_get_admin_users_with_pagination(self, mock_verify_token, client, mock_admin_claims):
        """Test admin users retrieval with pagination"""
        mock_verify_token.return_value = mock_admin_claims
        
        with patch('web.routes_admin_panel.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value.__enter__.return_value = mock_db
            
            # Mock database queries
            mock_query = Mock()
            mock_query.count.return_value = 25
            mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
            
            mock_db.query.return_value = mock_query
            
            response = client.get(
                "/api/admin/users?page=2&limit=10",
                headers={"Authorization": f"Bearer {mock_admin_claims['sub']}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 25
            assert data["current_page"] == 2
            assert data["total_pages"] == 3
            assert data["has_next"] is True
            assert data["has_previous"] is True
    
    def test_get_admin_users_unauthorized(self, client):
        """Test admin users without authentication"""
        response = client.get("/api/admin/users")
        
        assert response.status_code == 401
        assert "Missing authentication token" in response.json()["detail"]
    
    @patch('web.routes_admin_panel.verify_admin_token')
    def test_get_admin_users_invalid_token(self, mock_verify_token, client):
        """Test admin users with invalid token"""
        mock_verify_token.return_value = None
        
        response = client.get(
            "/api/admin/users",
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        assert response.status_code == 401
        assert "Invalid token" in response.json()["detail"]
    
    @patch('web.routes_admin_panel.verify_admin_token')
    def test_get_admin_users_insufficient_permissions(self, mock_verify_token, client):
        """Test admin users with insufficient permissions"""
        mock_verify_token.return_value = {"sub": "12345", "role": "user"}
        
        response = client.get(
            "/api/admin/users",
            headers={"Authorization": "Bearer user_token"}
        )
        
        assert response.status_code == 403
        assert "Admin access required" in response.json()["detail"]
    
    @patch('web.routes_admin_panel.verify_admin_token')
    def test_get_admin_dashboard_database_error(self, mock_verify_token, client, mock_admin_claims):
        """Test admin dashboard with database error"""
        mock_verify_token.return_value = mock_admin_claims
        
        with patch('web.routes_admin_panel.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value.__enter__.return_value = mock_db
            mock_db.query.side_effect = Exception("Database error")
            
            response = client.get(
                "/api/admin/dashboard",
                headers={"Authorization": f"Bearer {mock_admin_claims['sub']}"}
            )
            
            assert response.status_code == 500
            assert "Internal server error" in response.json()["detail"]
    
    @patch('web.routes_admin_panel.verify_admin_token')
    def test_get_admin_users_database_error(self, mock_verify_token, client, mock_admin_claims):
        """Test admin users with database error"""
        mock_verify_token.return_value = mock_admin_claims
        
        with patch('web.routes_admin_panel.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value.__enter__.return_value = mock_db
            mock_db.query.side_effect = Exception("Database error")
            
            response = client.get(
                "/api/admin/users",
                headers={"Authorization": f"Bearer {mock_admin_claims['sub']}"}
            )
            
            assert response.status_code == 500
            assert "Internal server error" in response.json()["detail"]
    
    def test_admin_dashboard_endpoint_exists(self, client):
        """Test that admin dashboard endpoint exists"""
        # This should return 401 (unauthorized) rather than 404 (not found)
        response = client.get("/api/admin/dashboard")
        assert response.status_code == 401
    
    def test_admin_users_endpoint_exists(self, client):
        """Test that admin users endpoint exists"""
        # This should return 401 (unauthorized) rather than 404 (not found)
        response = client.get("/api/admin/users")
        assert response.status_code == 401
    
    def test_admin_endpoints_require_auth(self, client):
        """Test that all admin endpoints require authentication"""
        endpoints = [
            "/api/admin/dashboard",
            "/api/admin/users"
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401
            assert "Missing authentication token" in response.json()["detail"]
    
    @patch('web.routes_admin_panel.verify_admin_token')
    def test_admin_endpoints_accept_valid_auth(self, mock_verify_token, client, mock_admin_claims):
        """Test that admin endpoints accept valid authentication"""
        mock_verify_token.return_value = mock_admin_claims
        
        with patch('web.routes_admin_panel.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value.__enter__.return_value = mock_db
            
            # Mock successful database queries
            mock_db.query.return_value.count.return_value = 0
            mock_db.query.return_value.filter.return_value.count.return_value = 0
            
            endpoints = [
                "/api/admin/dashboard",
                "/api/admin/users"
            ]
            
            for endpoint in endpoints:
                response = client.get(
                    endpoint,
                    headers={"Authorization": f"Bearer {mock_admin_claims['sub']}"}
                )
                assert response.status_code == 200
