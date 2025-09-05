#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for QR Code Service
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
import uuid

from core.services.qr_code_service import QRCodeService
from core.models.qr_code import QRCode
from core.models.user import User
from core.exceptions import NotFoundError, BusinessLogicError


@pytest.fixture
def mock_db():
    """Mock database session"""
    db = AsyncMock()
    return db


@pytest.fixture
def qr_service(mock_db):
    """QR Code Service instance with mocked database"""
    return QRCodeService(mock_db)


@pytest.fixture
def mock_user():
    """Mock user object"""
    user = MagicMock()
    user.user_id = 12345
    user.first_name = "Test User"
    user.username = "testuser"
    return user


@pytest.fixture
def mock_qr_code():
    """Mock QR code object"""
    qr = MagicMock()
    qr.qr_id = str(uuid.uuid4())
    qr.user_id = 12345
    qr.discount_type = "loyalty_points"
    qr.discount_value = 100
    qr.description = "Test discount"
    qr.expires_at = datetime.utcnow() + timedelta(hours=24)
    qr.is_used = False
    qr.used_at = None
    qr.used_by_partner_id = None
    qr.created_at = datetime.utcnow()
    return qr


class TestQRCodeService:
    """Test cases for QR Code Service"""
    
    @pytest.mark.asyncio
    async def test_generate_qr_code_success(self, qr_service, mock_db, mock_user):
        """Test successful QR code generation"""
        # Mock database queries
        mock_db.execute.return_value.scalar_one_or_none.return_value = mock_user
        mock_db.commit = AsyncMock()
        mock_db.add = MagicMock()
        
        # Mock QR code generation
        with patch('core.services.qr_code_service.uuid.uuid4') as mock_uuid:
            mock_uuid.return_value = uuid.UUID('12345678-1234-5678-9012-123456789012')
            
            result = await qr_service.generate_qr_code(
                user_id=12345,
                discount_type="loyalty_points",
                discount_value=100,
                expires_in_hours=24,
                description="Test discount"
            )
        
        # Verify result
        assert result["qr_id"] == "12345678-1234-5678-9012-123456789012"
        assert result["discount_type"] == "loyalty_points"
        assert result["discount_value"] == 100
        assert result["description"] == "Test discount"
        assert "qr_image" in result
        assert "expires_at" in result
        
        # Verify database operations
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_qr_code_user_not_found(self, qr_service, mock_db):
        """Test QR code generation with non-existent user"""
        # Mock database query to return None (user not found)
        mock_db.execute.return_value.scalar_one_or_none.return_value = None
        
        with pytest.raises(NotFoundError, match="User not found"):
            await qr_service.generate_qr_code(
                user_id=99999,
                discount_type="loyalty_points",
                discount_value=100
            )
    
    @pytest.mark.asyncio
    async def test_validate_qr_code_success(self, qr_service, mock_db, mock_qr_code, mock_user):
        """Test successful QR code validation"""
        # Mock database queries
        mock_db.execute.return_value.scalar_one_or_none.side_effect = [mock_qr_code, mock_user]
        
        result = await qr_service.validate_qr_code(mock_qr_code.qr_id)
        
        # Verify result
        assert result["valid"] is True
        assert result["qr_id"] == mock_qr_code.qr_id
        assert result["user_id"] == mock_qr_code.user_id
        assert result["discount_type"] == mock_qr_code.discount_type
        assert result["discount_value"] == mock_qr_code.discount_value
    
    @pytest.mark.asyncio
    async def test_validate_qr_code_not_found(self, qr_service, mock_db):
        """Test QR code validation with non-existent code"""
        # Mock database query to return None (QR code not found)
        mock_db.execute.return_value.scalar_one_or_none.return_value = None
        
        result = await qr_service.validate_qr_code("non-existent-id")
        
        # Verify result
        assert result["valid"] is False
        assert result["error"] == "QR code not found"
    
    @pytest.mark.asyncio
    async def test_validate_qr_code_already_used(self, qr_service, mock_db, mock_qr_code):
        """Test QR code validation with already used code"""
        # Mock QR code as already used
        mock_qr_code.is_used = True
        mock_qr_code.used_at = datetime.utcnow()
        mock_db.execute.return_value.scalar_one_or_none.return_value = mock_qr_code
        
        result = await qr_service.validate_qr_code(mock_qr_code.qr_id)
        
        # Verify result
        assert result["valid"] is False
        assert result["error"] == "QR code already used"
        assert "used_at" in result
    
    @pytest.mark.asyncio
    async def test_validate_qr_code_expired(self, qr_service, mock_db, mock_qr_code):
        """Test QR code validation with expired code"""
        # Mock QR code as expired
        mock_qr_code.expires_at = datetime.utcnow() - timedelta(hours=1)
        mock_db.execute.return_value.scalar_one_or_none.return_value = mock_qr_code
        
        result = await qr_service.validate_qr_code(mock_qr_code.qr_id)
        
        # Verify result
        assert result["valid"] is False
        assert result["error"] == "QR code expired"
        assert "expires_at" in result
    
    @pytest.mark.asyncio
    async def test_redeem_qr_code_success(self, qr_service, mock_db, mock_qr_code, mock_user):
        """Test successful QR code redemption"""
        # Mock validation success
        with patch.object(qr_service, 'validate_qr_code', return_value={"valid": True}):
            # Mock database query
            mock_db.execute.return_value.scalar_one.return_value = mock_qr_code
            mock_db.commit = AsyncMock()
            
            result = await qr_service.redeem_qr_code(
                qr_id=mock_qr_code.qr_id,
                partner_id=67890,
                partner_name="Test Partner"
            )
        
        # Verify result
        assert result["success"] is True
        assert result["qr_id"] == mock_qr_code.qr_id
        assert result["partner_id"] == 67890
        assert result["partner_name"] == "Test Partner"
        
        # Verify QR code was marked as used
        assert mock_qr_code.is_used is True
        assert mock_qr_code.used_at is not None
        assert mock_qr_code.used_by_partner_id == 67890
        
        # Verify database commit
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_redeem_qr_code_validation_failed(self, qr_service, mock_db):
        """Test QR code redemption with validation failure"""
        # Mock validation failure
        with patch.object(qr_service, 'validate_qr_code', return_value={"valid": False, "error": "QR code not found"}):
            result = await qr_service.redeem_qr_code(
                qr_id="invalid-id",
                partner_id=67890,
                partner_name="Test Partner"
            )
        
        # Verify result
        assert result["success"] is False
        assert result["error"] == "QR code not found"
    
    @pytest.mark.asyncio
    async def test_get_user_qr_codes(self, qr_service, mock_db, mock_qr_code):
        """Test getting user's QR codes"""
        # Mock database query
        mock_db.execute.return_value.scalars.return_value.all.return_value = [mock_qr_code]
        
        result = await qr_service.get_user_qr_codes(
            user_id=12345,
            limit=10,
            include_used=False
        )
        
        # Verify result
        assert len(result) == 1
        assert result[0]["qr_id"] == mock_qr_code.qr_id
        assert result[0]["user_id"] == mock_qr_code.user_id
        assert result[0]["discount_type"] == mock_qr_code.discount_type
    
    @pytest.mark.asyncio
    async def test_get_qr_code_stats(self, qr_service, mock_db):
        """Test getting QR code statistics"""
        # Mock database queries for different counts
        mock_db.execute.return_value.scalars.return_value.all.side_effect = [
            [MagicMock()] * 10,  # total_codes
            [MagicMock()] * 7,   # used_codes
            [MagicMock()] * 2,   # active_codes
            [MagicMock()] * 1    # expired_codes
        ]
        
        result = await qr_service.get_qr_code_stats(user_id=12345)
        
        # Verify result
        assert result["total_codes"] == 10
        assert result["used_codes"] == 7
        assert result["active_codes"] == 2
        assert result["expired_codes"] == 1
        assert result["usage_rate"] == 70.0  # 7/10 * 100
    
    @pytest.mark.asyncio
    async def test_get_qr_code_stats_empty(self, qr_service, mock_db):
        """Test getting QR code statistics with no codes"""
        # Mock database queries to return empty lists
        mock_db.execute.return_value.scalars.return_value.all.return_value = []
        
        result = await qr_service.get_qr_code_stats(user_id=12345)
        
        # Verify result
        assert result["total_codes"] == 0
        assert result["used_codes"] == 0
        assert result["active_codes"] == 0
        assert result["expired_codes"] == 0
        assert result["usage_rate"] == 0


class TestQRCodeModel:
    """Test cases for QR Code model"""
    
    def test_qr_code_to_dict(self, mock_qr_code):
        """Test QR code to_dict method"""
        result = mock_qr_code.to_dict()
        
        assert result["qr_id"] == mock_qr_code.qr_id
        assert result["user_id"] == mock_qr_code.user_id
        assert result["discount_type"] == mock_qr_code.discount_type
        assert result["discount_value"] == mock_qr_code.discount_value
        assert result["is_used"] == mock_qr_code.is_used
    
    def test_qr_code_is_expired(self, mock_qr_code):
        """Test QR code expiration check"""
        # Test not expired
        mock_qr_code.expires_at = datetime.utcnow() + timedelta(hours=1)
        assert not mock_qr_code.is_expired()
        
        # Test expired
        mock_qr_code.expires_at = datetime.utcnow() - timedelta(hours=1)
        assert mock_qr_code.is_expired()
    
    def test_qr_code_can_be_used(self, mock_qr_code):
        """Test QR code usage eligibility"""
        # Test can be used
        mock_qr_code.is_used = False
        mock_qr_code.expires_at = datetime.utcnow() + timedelta(hours=1)
        assert mock_qr_code.can_be_used()
        
        # Test already used
        mock_qr_code.is_used = True
        assert not mock_qr_code.can_be_used()
        
        # Test expired
        mock_qr_code.is_used = False
        mock_qr_code.expires_at = datetime.utcnow() - timedelta(hours=1)
        assert not mock_qr_code.can_be_used()
