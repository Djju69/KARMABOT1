#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integration tests for Partner API endpoints
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

from web.app import app
from core.models import User, Card, QRCode


class TestPartnerAPI:
    """Integration tests for partner API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Test client"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_partner_token(self):
        """Mock partner JWT token"""
        return "mock_partner_token_12345"
    
    @pytest.fixture
    def mock_partner_claims(self):
        """Mock partner JWT claims"""
        return {
            "sub": "12345",
            "role": "partner",
            "exp": int((datetime.utcnow() + timedelta(hours=1)).timestamp())
        }
    
    @pytest.fixture
    def sample_partner_stats(self):
        """Sample partner statistics"""
        return {
            "total_cards": 5,
            "active_cards": 3,
            "total_views": 150,
            "total_scans": 25,
            "recent_scans": 8,
            "conversion_rate": 16.67,
            "popular_cards": [
                {"title": "Card 1", "views": 50, "scans": 10},
                {"title": "Card 2", "views": 40, "scans": 8},
                {"title": "Card 3", "views": 30, "scans": 5}
            ]
        }
    
    @pytest.fixture
    def sample_cards_data(self):
        """Sample cards data"""
        return {
            "items": [
                {
                    "id": 1,
                    "category_id": 1,
                    "subcategory_id": 101,
                    "city_id": 1,
                    "area_id": 1001,
                    "title": "Test Restaurant",
                    "description": "Great food",
                    "contact": "+1234567890",
                    "address": "123 Main St",
                    "google_maps_url": "https://maps.google.com/1",
                    "discount_text": "10% off",
                    "status": "approved",
                    "priority_level": 0,
                    "views": 25,
                    "scans": 5,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            ],
            "total": 1,
            "total_pages": 1,
            "current_page": 1,
            "has_next": False,
            "has_previous": False
        }
    
    @pytest.fixture
    def sample_qr_codes_data(self):
        """Sample QR codes data"""
        return [
            {
                "id": 1,
                "code": "QR001",
                "value": 100,
                "expires_at": datetime.utcnow() + timedelta(days=30),
                "is_active": True,
                "redeemed_by": None,
                "redeemed_at": None,
                "qr_code_url": "/api/qr-codes/1/image",
                "created_at": datetime.utcnow()
            }
        ]
    
    @patch('web.routes_partner.verify_partner_token')
    def test_get_partner_statistics_success(self, mock_verify_token, client, mock_partner_claims, sample_partner_stats):
        """Test successful partner statistics retrieval"""
        mock_verify_token.return_value = mock_partner_claims
        
        with patch('web.routes_partner.get_partner_statistics') as mock_get_stats:
            mock_get_stats.return_value = sample_partner_stats
            
            response = client.get(
                "/api/partner/statistics",
                headers={"Authorization": f"Bearer {mock_partner_claims['sub']}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["total_cards"] == 5
            assert data["active_cards"] == 3
            assert data["total_views"] == 150
            assert data["total_scans"] == 25
            assert data["conversion_rate"] == 16.67
            assert len(data["popular_cards"]) == 3
    
    def test_get_partner_statistics_unauthorized(self, client):
        """Test partner statistics without authentication"""
        response = client.get("/api/partner/statistics")
        
        assert response.status_code == 401
        assert "Missing authentication token" in response.json()["detail"]
    
    @patch('web.routes_partner.verify_partner_token')
    def test_get_partner_cards_success(self, mock_verify_token, client, mock_partner_claims, sample_cards_data):
        """Test successful partner cards retrieval"""
        mock_verify_token.return_value = mock_partner_claims
        
        with patch('web.routes_partner.get_partner_cards_with_filter') as mock_get_cards:
            mock_get_cards.return_value = sample_cards_data
            
            response = client.get(
                "/api/partner/cards",
                headers={"Authorization": f"Bearer {mock_partner_claims['sub']}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["items"]) == 1
            assert data["total"] == 1
            assert data["current_page"] == 1
            assert data["items"][0]["title"] == "Test Restaurant"
            assert data["items"][0]["status"] == "approved"
    
    @patch('web.routes_partner.verify_partner_token')
    def test_get_partner_cards_with_filters(self, mock_verify_token, client, mock_partner_claims, sample_cards_data):
        """Test partner cards retrieval with filters"""
        mock_verify_token.return_value = mock_partner_claims
        
        with patch('web.routes_partner.get_partner_cards_with_filter') as mock_get_cards:
            mock_get_cards.return_value = sample_cards_data
            
            response = client.get(
                "/api/partner/cards?status=approved&category_id=1&q=restaurant&page=1&limit=10",
                headers={"Authorization": f"Bearer {mock_partner_claims['sub']}"}
            )
            
            assert response.status_code == 200
            # Verify filters were passed to service
            mock_get_cards.assert_called_once()
    
    @patch('web.routes_partner.verify_partner_token')
    def test_create_partner_card_success(self, mock_verify_token, client, mock_partner_claims):
        """Test successful partner card creation"""
        mock_verify_token.return_value = mock_partner_claims
        
        card_data = {
            "category_id": 1,
            "subcategory_id": 101,
            "city_id": 1,
            "area_id": 1001,
            "title": "New Restaurant",
            "description": "Amazing food",
            "contact": "+1234567890",
            "address": "456 Oak St",
            "google_maps_url": "https://maps.google.com/2",
            "discount_text": "15% off"
        }
        
        with patch('web.routes_partner.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value.__enter__.return_value = mock_db
            
            # Mock card creation
            mock_card = Mock()
            mock_card.id = 2
            mock_card.category_id = 1
            mock_card.title = "New Restaurant"
            mock_card.status = "pending"
            mock_card.created_at = datetime.utcnow()
            mock_card.updated_at = datetime.utcnow()
            mock_card.views = 0
            mock_card.scans = 0
            
            mock_db.add.return_value = None
            mock_db.commit.return_value = None
            mock_db.refresh.return_value = None
            mock_db.refresh.side_effect = lambda obj: setattr(obj, 'id', 2)
            
            response = client.post(
                "/api/partner/cards",
                json=card_data,
                headers={"Authorization": f"Bearer {mock_partner_claims['sub']}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["title"] == "New Restaurant"
            assert data["status"] == "pending"
            assert data["category_id"] == 1
    
    @patch('web.routes_partner.verify_partner_token')
    def test_update_partner_card_success(self, mock_verify_token, client, mock_partner_claims):
        """Test successful partner card update"""
        mock_verify_token.return_value = mock_partner_claims
        
        update_data = {
            "title": "Updated Restaurant",
            "description": "Updated description",
            "discount_text": "20% off"
        }
        
        with patch('web.routes_partner.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value.__enter__.return_value = mock_db
            
            # Mock existing card
            mock_card = Mock()
            mock_card.id = 1
            mock_card.partner_id = 12345
            mock_card.category_id = 1
            mock_card.title = "Updated Restaurant"
            mock_card.description = "Updated description"
            mock_card.discount_text = "20% off"
            mock_card.status = "pending"
            mock_card.created_at = datetime.utcnow()
            mock_card.updated_at = datetime.utcnow()
            mock_card.views = 0
            mock_card.scans = 0
            
            mock_db.query.return_value.filter.return_value.first.return_value = mock_card
            mock_db.commit.return_value = None
            mock_db.refresh.return_value = None
            
            response = client.patch(
                "/api/partner/cards/1",
                json=update_data,
                headers={"Authorization": f"Bearer {mock_partner_claims['sub']}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["title"] == "Updated Restaurant"
            assert data["description"] == "Updated description"
            assert data["discount_text"] == "20% off"
    
    @patch('web.routes_partner.verify_partner_token')
    def test_hide_partner_card_success(self, mock_verify_token, client, mock_partner_claims):
        """Test successful partner card hiding"""
        mock_verify_token.return_value = mock_partner_claims
        
        with patch('web.routes_partner.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value.__enter__.return_value = mock_db
            
            # Mock existing card
            mock_card = Mock()
            mock_card.id = 1
            mock_card.partner_id = 12345
            mock_card.category_id = 1
            mock_card.title = "Test Card"
            mock_card.status = "archived"
            mock_card.created_at = datetime.utcnow()
            mock_card.updated_at = datetime.utcnow()
            mock_card.views = 0
            mock_card.scans = 0
            
            mock_db.query.return_value.filter.return_value.first.return_value = mock_card
            mock_db.commit.return_value = None
            mock_db.refresh.return_value = None
            
            response = client.post(
                "/api/partner/cards/1/hide",
                headers={"Authorization": f"Bearer {mock_partner_claims['sub']}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "archived"
    
    @patch('web.routes_partner.verify_partner_token')
    def test_get_partner_qr_codes_success(self, mock_verify_token, client, mock_partner_claims, sample_qr_codes_data):
        """Test successful partner QR codes retrieval"""
        mock_verify_token.return_value = mock_partner_claims
        
        with patch('web.routes_partner.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value.__enter__.return_value = mock_db
            
            # Mock QR codes query
            mock_qr_code = Mock()
            mock_qr_code.id = 1
            mock_qr_code.code = "QR001"
            mock_qr_code.value = 100
            mock_qr_code.expires_at = datetime.utcnow() + timedelta(days=30)
            mock_qr_code.is_active = True
            mock_qr_code.redeemed_by = None
            mock_qr_code.redeemed_at = None
            mock_qr_code.created_at = datetime.utcnow()
            
            mock_db.query.return_value.join.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_qr_code]
            
            response = client.get(
                "/api/partner/qr-codes",
                headers={"Authorization": f"Bearer {mock_partner_claims['sub']}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["code"] == "QR001"
            assert data[0]["value"] == 100
            assert data[0]["is_active"] is True
    
    @patch('web.routes_partner.verify_partner_token')
    def test_create_partner_qr_code_success(self, mock_verify_token, client, mock_partner_claims):
        """Test successful partner QR code creation"""
        mock_verify_token.return_value = mock_partner_claims
        
        qr_data = {
            "card_id": 1,
            "value": 150,
            "expires_days": 30
        }
        
        with patch('web.routes_partner.get_db') as mock_get_db, \
             patch('web.routes_partner.qr_code_service') as mock_qr_service:
            
            mock_db = Mock()
            mock_get_db.return_value.__enter__.return_value = mock_db
            
            # Mock card ownership verification
            mock_card = Mock()
            mock_card.id = 1
            mock_card.partner_id = 12345
            
            mock_db.query.return_value.filter.return_value.first.return_value = mock_card
            
            # Mock QR code creation
            mock_qr_code = Mock()
            mock_qr_code.id = 2
            mock_qr_code.code = "QR002"
            mock_qr_code.value = 150
            mock_qr_code.expires_at = datetime.utcnow() + timedelta(days=30)
            mock_qr_code.is_active = True
            mock_qr_code.redeemed_by = None
            mock_qr_code.redeemed_at = None
            mock_qr_code.created_at = datetime.utcnow()
            
            mock_qr_service.create_qr_code.return_value = mock_qr_code
            
            response = client.post(
                "/api/partner/qr-codes",
                json=qr_data,
                headers={"Authorization": f"Bearer {mock_partner_claims['sub']}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == "QR002"
            assert data["value"] == 150
            assert data["is_active"] is True
    
    @patch('web.routes_partner.verify_partner_token')
    def test_update_partner_settings_success(self, mock_verify_token, client, mock_partner_claims):
        """Test successful partner settings update"""
        mock_verify_token.return_value = mock_partner_claims
        
        settings_data = {
            "display_name": "Updated Partner Name",
            "phone": "+9876543210",
            "email": "updated@partner.com"
        }
        
        with patch('web.routes_partner.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value.__enter__.return_value = mock_db
            
            # Mock partner user
            mock_partner = Mock()
            mock_partner.telegram_id = 12345
            mock_partner.display_name = "Updated Partner Name"
            mock_partner.phone = "+9876543210"
            mock_partner.email = "updated@partner.com"
            
            mock_db.query.return_value.filter.return_value.first.return_value = mock_partner
            mock_db.commit.return_value = None
            
            response = client.put(
                "/api/partner/settings",
                json=settings_data,
                headers={"Authorization": f"Bearer {mock_partner_claims['sub']}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Settings updated successfully"
    
    @patch('web.routes_partner.verify_partner_token')
    def test_card_not_found_error(self, mock_verify_token, client, mock_partner_claims):
        """Test error when card not found"""
        mock_verify_token.return_value = mock_partner_claims
        
        with patch('web.routes_partner.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value.__enter__.return_value = mock_db
            mock_db.query.return_value.filter.return_value.first.return_value = None
            
            response = client.patch(
                "/api/partner/cards/999",
                json={"title": "Updated Title"},
                headers={"Authorization": f"Bearer {mock_partner_claims['sub']}"}
            )
            
            assert response.status_code == 404
            assert "Card not found" in response.json()["detail"]
    
    @patch('web.routes_partner.verify_partner_token')
    def test_unauthorized_card_access(self, mock_verify_token, client, mock_partner_claims):
        """Test unauthorized access to another partner's card"""
        mock_verify_token.return_value = mock_partner_claims
        
        with patch('web.routes_partner.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value.__enter__.return_value = mock_db
            
            # Mock card owned by different partner
            mock_card = Mock()
            mock_card.id = 1
            mock_card.partner_id = 99999  # Different partner
            
            mock_db.query.return_value.filter.return_value.first.return_value = mock_card
            
            response = client.patch(
                "/api/partner/cards/1",
                json={"title": "Updated Title"},
                headers={"Authorization": f"Bearer {mock_partner_claims['sub']}"}
            )
            
            assert response.status_code == 404  # Card not found for this partner
            assert "Card not found" in response.json()["detail"]
    
    def test_invalid_token(self, client):
        """Test with invalid token"""
        response = client.get(
            "/api/partner/statistics",
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        assert response.status_code == 401
        assert "Invalid token" in response.json()["detail"]
    
    def test_missing_authorization_header(self, client):
        """Test without authorization header"""
        response = client.get("/api/partner/statistics")
        
        assert response.status_code == 401
        assert "Missing authentication token" in response.json()["detail"]
    
    @patch('web.routes_partner.verify_partner_token')
    def test_invalid_card_data(self, mock_verify_token, client, mock_partner_claims):
        """Test with invalid card data"""
        mock_verify_token.return_value = mock_partner_claims
        
        invalid_data = {
            "title": "",  # Empty title should fail validation
            "category_id": "invalid"  # Invalid category ID type
        }
        
        response = client.post(
            "/api/partner/cards",
            json=invalid_data,
            headers={"Authorization": f"Bearer {mock_partner_claims['sub']}"}
        )
        
        assert response.status_code == 422  # Validation error
    
    @patch('web.routes_partner.verify_partner_token')
    def test_invalid_qr_data(self, mock_verify_token, client, mock_partner_claims):
        """Test with invalid QR code data"""
        mock_verify_token.return_value = mock_partner_claims
        
        invalid_data = {
            "card_id": "invalid",  # Invalid card ID type
            "value": -10,  # Negative value should fail validation
            "expires_days": 0  # Zero days should fail validation
        }
        
        response = client.post(
            "/api/partner/qr-codes",
            json=invalid_data,
            headers={"Authorization": f"Bearer {mock_partner_claims['sub']}"}
        )
        
        assert response.status_code == 422  # Validation error
