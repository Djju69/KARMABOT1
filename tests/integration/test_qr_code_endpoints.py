#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integration tests for QR Code endpoints
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import json

from web.app import app
from core.database import get_db


@pytest.fixture
def client():
    """Test client for FastAPI app"""
    return TestClient(app)


@pytest.fixture
def mock_user():
    """Mock user for authentication"""
    return {
        "user_id": 12345,
        "username": "testuser",
        "first_name": "Test",
        "last_name": "User"
    }


@pytest.fixture
def mock_qr_code():
    """Mock QR code data"""
    return {
        "qr_id": "12345678-1234-5678-9012-123456789012",
        "user_id": 12345,
        "discount_type": "loyalty_points",
        "discount_value": 100,
        "description": "Test discount",
        "expires_at": "2025-01-28T15:30:00",
        "is_used": False,
        "used_at": None,
        "used_by_partner_id": None,
        "created_at": "2025-01-27T15:30:00"
    }


class TestQREndpoints:
    """Test cases for QR Code endpoints"""
    
    def test_get_user_qr_codes_success(self, client, mock_user, mock_qr_code):
        """Test successful retrieval of user QR codes"""
        with patch("core.security.get_current_user", return_value=mock_user):
            with patch("core.database.get_db") as mock_get_db:
                mock_db = AsyncMock()
                mock_get_db.return_value = mock_db
                
                # Mock QR code service
                with patch("core.services.qr_code_service.QRCodeService.get_user_qr_codes", 
                          return_value=[mock_qr_code]):
                    
                    response = client.get("/qr/codes?limit=10&include_used=false")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["qr_id"] == mock_qr_code["qr_id"]
        assert data[0]["user_id"] == mock_qr_code["user_id"]
    
    def test_get_user_qr_codes_unauthorized(self, client):
        """Test QR codes endpoint without authentication"""
        with patch("core.security.get_current_user", side_effect=Exception("Unauthorized")):
            response = client.get("/qr/codes")
        
        assert response.status_code == 401
    
    def test_generate_qr_code_success(self, client, mock_user):
        """Test successful QR code generation"""
        request_data = {
            "discount_type": "loyalty_points",
            "discount_value": 100,
            "expires_in_hours": 24,
            "description": "Test discount"
        }
        
        with patch("core.security.get_current_user", return_value=mock_user):
            with patch("core.database.get_db") as mock_get_db:
                mock_db = AsyncMock()
                mock_get_db.return_value = mock_db
                
                # Mock QR code service
                with patch("core.services.qr_code_service.QRCodeService.generate_qr_code", 
                          return_value={
                              "qr_id": "12345678-1234-5678-9012-123456789012",
                              "qr_image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
                              "discount_type": "loyalty_points",
                              "discount_value": 100,
                              "description": "Test discount",
                              "expires_at": "2025-01-28T15:30:00",
                              "expires_in_hours": 24
                          }):
                    
                    response = client.post("/qr/codes/generate", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["qr_id"] == "12345678-1234-5678-9012-123456789012"
        assert data["discount_type"] == "loyalty_points"
        assert data["discount_value"] == 100
        assert "qr_image" in data
    
    def test_generate_qr_code_invalid_value(self, client, mock_user):
        """Test QR code generation with invalid discount value"""
        request_data = {
            "discount_type": "loyalty_points",
            "discount_value": -100,  # Invalid negative value
            "expires_in_hours": 24,
            "description": "Test discount"
        }
        
        with patch("core.security.get_current_user", return_value=mock_user):
            with patch("core.database.get_db") as mock_get_db:
                mock_db = AsyncMock()
                mock_get_db.return_value = mock_db
                
                response = client.post("/qr/codes/generate", json=request_data)
        
        assert response.status_code == 400
        assert "Discount value must be positive" in response.json()["detail"]
    
    def test_generate_qr_code_invalid_expiration(self, client, mock_user):
        """Test QR code generation with invalid expiration time"""
        request_data = {
            "discount_type": "loyalty_points",
            "discount_value": 100,
            "expires_in_hours": 200,  # Invalid: more than 168 hours
            "description": "Test discount"
        }
        
        with patch("core.security.get_current_user", return_value=mock_user):
            with patch("core.database.get_db") as mock_get_db:
                mock_db = AsyncMock()
                mock_get_db.return_value = mock_db
                
                response = client.post("/qr/codes/generate", json=request_data)
        
        assert response.status_code == 400
        assert "Expiration must be between 1 and 168 hours" in response.json()["detail"]
    
    def test_validate_qr_code_success(self, client, mock_qr_code):
        """Test successful QR code validation"""
        qr_id = mock_qr_code["qr_id"]
        
        with patch("core.database.get_db") as mock_get_db:
            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            
            # Mock QR code service
            with patch("core.services.qr_code_service.QRCodeService.validate_qr_code", 
                      return_value={
                          "valid": True,
                          "qr_id": qr_id,
                          "user_id": mock_qr_code["user_id"],
                          "user_name": "Test User",
                          "discount_type": mock_qr_code["discount_type"],
                          "discount_value": mock_qr_code["discount_value"],
                          "description": mock_qr_code["description"],
                          "expires_at": mock_qr_code["expires_at"]
                      }):
                
                response = client.get(f"/qr/codes/{qr_id}/validate")
        
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["qr_id"] == qr_id
        assert data["user_id"] == mock_qr_code["user_id"]
    
    def test_validate_qr_code_not_found(self, client):
        """Test QR code validation with non-existent code"""
        qr_id = "non-existent-id"
        
        with patch("core.database.get_db") as mock_get_db:
            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            
            # Mock QR code service
            with patch("core.services.qr_code_service.QRCodeService.validate_qr_code", 
                      return_value={
                          "valid": False,
                          "error": "QR code not found"
                      }):
                
                response = client.get(f"/qr/codes/{qr_id}/validate")
        
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert data["error"] == "QR code not found"
    
    def test_redeem_qr_code_success(self, client, mock_user, mock_qr_code):
        """Test successful QR code redemption"""
        qr_id = mock_qr_code["qr_id"]
        request_data = {
            "partner_id": 67890,
            "partner_name": "Test Partner"
        }
        
        with patch("core.security.get_current_user", return_value=mock_user):
            with patch("core.database.get_db") as mock_get_db:
                mock_db = AsyncMock()
                mock_get_db.return_value = mock_db
                
                # Mock QR code service
                with patch("core.services.qr_code_service.QRCodeService.redeem_qr_code", 
                          return_value={
                              "success": True,
                              "qr_id": qr_id,
                              "user_id": mock_qr_code["user_id"],
                              "discount_type": mock_qr_code["discount_type"],
                              "discount_value": mock_qr_code["discount_value"],
                              "description": mock_qr_code["description"],
                              "redeemed_at": "2025-01-27T16:00:00",
                              "partner_id": 67890,
                              "partner_name": "Test Partner"
                          }):
                    
                    response = client.post(f"/qr/codes/{qr_id}/redeem", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["qr_id"] == qr_id
        assert data["partner_id"] == 67890
        assert data["partner_name"] == "Test Partner"
    
    def test_redeem_qr_code_validation_failed(self, client, mock_user):
        """Test QR code redemption with validation failure"""
        qr_id = "invalid-id"
        request_data = {
            "partner_id": 67890,
            "partner_name": "Test Partner"
        }
        
        with patch("core.security.get_current_user", return_value=mock_user):
            with patch("core.database.get_db") as mock_get_db:
                mock_db = AsyncMock()
                mock_get_db.return_value = mock_db
                
                # Mock QR code service
                with patch("core.services.qr_code_service.QRCodeService.redeem_qr_code", 
                          return_value={
                              "success": False,
                              "error": "QR code not found"
                          }):
                    
                    response = client.post(f"/qr/codes/{qr_id}/redeem", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["error"] == "QR code not found"
    
    def test_redeem_qr_code_missing_partner_id(self, client, mock_user):
        """Test QR code redemption without partner ID"""
        qr_id = "12345678-1234-5678-9012-123456789012"
        request_data = {
            "partner_name": "Test Partner"
            # Missing partner_id
        }
        
        with patch("core.security.get_current_user", return_value=mock_user):
            with patch("core.database.get_db") as mock_get_db:
                mock_db = AsyncMock()
                mock_get_db.return_value = mock_db
                
                response = client.post(f"/qr/codes/{qr_id}/redeem", json=request_data)
        
        assert response.status_code == 400
        assert "Partner ID is required" in response.json()["detail"]
    
    def test_get_qr_code_stats_success(self, client, mock_user):
        """Test successful QR code statistics retrieval"""
        with patch("core.security.get_current_user", return_value=mock_user):
            with patch("core.database.get_db") as mock_get_db:
                mock_db = AsyncMock()
                mock_get_db.return_value = mock_db
                
                # Mock QR code service
                with patch("core.services.qr_code_service.QRCodeService.get_qr_code_stats", 
                          return_value={
                              "total_codes": 10,
                              "used_codes": 7,
                              "active_codes": 2,
                              "expired_codes": 1,
                              "usage_rate": 70.0
                          }):
                    
                    response = client.get("/qr/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_codes"] == 10
        assert data["used_codes"] == 7
        assert data["active_codes"] == 2
        assert data["expired_codes"] == 1
        assert data["usage_rate"] == 70.0
    
    def test_scan_qr_code_success(self, client, mock_user):
        """Test successful QR code scanning"""
        qr_data = json.dumps({
            "qr_id": "12345678-1234-5678-9012-123456789012",
            "user_id": 12345,
            "discount_type": "loyalty_points",
            "discount_value": 100,
            "expires_at": "2025-01-28T15:30:00",
            "created_at": "2025-01-27T15:30:00"
        })
        
        with patch("core.security.get_current_user", return_value=mock_user):
            with patch("core.database.get_db") as mock_get_db:
                mock_db = AsyncMock()
                mock_get_db.return_value = mock_db
                
                # Mock QR code service
                with patch("core.services.qr_code_service.QRCodeService.validate_qr_code", 
                          return_value={
                              "valid": True,
                              "qr_id": "12345678-1234-5678-9012-123456789012",
                              "user_id": 12345,
                              "user_name": "Test User",
                              "discount_type": "loyalty_points",
                              "discount_value": 100,
                              "description": "Test discount",
                              "expires_at": "2025-01-28T15:30:00"
                          }):
                    
                    response = client.get(f"/qr/scan?qr_data={qr_data}")
        
        assert response.status_code == 200
        data = response.json()
        assert "qr_data" in data
        assert "validation" in data
        assert data["validation"]["valid"] is True
        assert data["qr_data"]["qr_id"] == "12345678-1234-5678-9012-123456789012"
    
    def test_scan_qr_code_invalid_format(self, client, mock_user):
        """Test QR code scanning with invalid format"""
        qr_data = "invalid-json-format"
        
        with patch("core.security.get_current_user", return_value=mock_user):
            with patch("core.database.get_db") as mock_get_db:
                mock_db = AsyncMock()
                mock_get_db.return_value = mock_db
                
                response = client.get(f"/qr/scan?qr_data={qr_data}")
        
        assert response.status_code == 400
        assert "Invalid QR code format" in response.json()["detail"]
    
    def test_scan_qr_code_missing_qr_id(self, client, mock_user):
        """Test QR code scanning with missing QR ID"""
        qr_data = json.dumps({
            "user_id": 12345,
            "discount_type": "loyalty_points",
            "discount_value": 100
            # Missing qr_id
        })
        
        with patch("core.security.get_current_user", return_value=mock_user):
            with patch("core.database.get_db") as mock_get_db:
                mock_db = AsyncMock()
                mock_get_db.return_value = mock_db
                
                response = client.get(f"/qr/scan?qr_data={qr_data}")
        
        assert response.status_code == 400
        assert "QR code ID not found" in response.json()["detail"]
