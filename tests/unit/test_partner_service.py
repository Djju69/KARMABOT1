#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for Partner Service
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from core.services.partner_service import PartnerService, partner_service
from core.models import User, Card, QRScan, QRCode


class TestPartnerService:
    """Test cases for PartnerService"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def partner_service_instance(self):
        """Partner service instance for testing"""
        return PartnerService()
    
    @pytest.fixture
    def sample_partner(self):
        """Sample partner user"""
        partner = Mock(spec=User)
        partner.telegram_id = 12345
        partner.display_name = "Test Partner"
        partner.full_name = "Test Partner Full"
        partner.phone = "+1234567890"
        partner.email = "test@partner.com"
        partner.is_verified = True
        partner.created_at = datetime.utcnow()
        partner.updated_at = datetime.utcnow()
        return partner
    
    @pytest.fixture
    def sample_cards(self):
        """Sample cards"""
        cards = []
        for i in range(3):
            card = Mock(spec=Card)
            card.id = i + 1
            card.category_id = 1
            card.subcategory_id = 101
            card.city_id = 1
            card.area_id = 1001
            card.title = f"Test Card {i + 1}"
            card.description = f"Description {i + 1}"
            card.contact = f"+123456789{i}"
            card.address = f"Address {i + 1}"
            card.google_maps_url = f"https://maps.google.com/{i + 1}"
            card.discount_text = f"Discount {i + 1}"
            card.status = "approved" if i < 2 else "pending"
            card.priority_level = 0
            card.views = 10 + i * 5
            card.scans = 2 + i
            card.created_at = datetime.utcnow()
            card.updated_at = datetime.utcnow()
            cards.append(card)
        return cards
    
    @pytest.fixture
    def sample_qr_codes(self):
        """Sample QR codes"""
        qr_codes = []
        for i in range(2):
            qr = Mock(spec=QRCode)
            qr.id = i + 1
            qr.code = f"QR{i + 1:03d}"
            qr.value = 100 + i * 50
            qr.expires_at = datetime.utcnow() + timedelta(days=30)
            qr.is_active = True
            qr.redeemed_by = None
            qr.redeemed_at = None
            qr.created_at = datetime.utcnow()
            qr.card = Mock()
            qr.card.title = f"Card {i + 1}"
            qr_codes.append(qr)
        return qr_codes
    
    @pytest.mark.asyncio
    async def test_get_partner_profile_success(self, partner_service_instance, mock_db, sample_partner):
        """Test successful partner profile retrieval"""
        # Mock database query results
        mock_card_stats = Mock()
        mock_card_stats.total_cards = 3
        mock_card_stats.active_cards = 2
        mock_card_stats.total_views = 25
        mock_card_stats.total_scans = 5
        
        with patch.object(partner_service_instance, 'db') as mock_db_context:
            mock_db_context.return_value.__enter__.return_value = mock_db
            
            # Mock queries
            mock_db.query.return_value.filter.return_value.first.return_value = sample_partner
            mock_db.query.return_value.filter.return_value.first.side_effect = [
                sample_partner,  # First call for partner
                mock_card_stats,  # Second call for card stats
            ]
            mock_db.query.return_value.filter.return_value.count.return_value = 3  # Recent scans
            mock_db.query.return_value.join.return_value.filter.return_value.count.return_value = 2  # QR codes
            
            result = await partner_service_instance.get_partner_profile(12345)
            
            assert result["partner_id"] == 12345
            assert result["display_name"] == "Test Partner"
            assert result["total_cards"] == 3
            assert result["active_cards"] == 2
            assert result["total_views"] == 25
            assert result["total_scans"] == 5
            assert result["conversion_rate"] == 20.0  # 5/25 * 100
    
    @pytest.mark.asyncio
    async def test_get_partner_profile_not_found(self, partner_service_instance, mock_db):
        """Test partner profile when partner not found"""
        with patch.object(partner_service_instance, 'db') as mock_db_context:
            mock_db_context.return_value.__enter__.return_value = mock_db
            mock_db.query.return_value.filter.return_value.first.return_value = None
            
            result = await partner_service_instance.get_partner_profile(99999)
            
            assert result == {}
    
    @pytest.mark.asyncio
    async def test_get_partner_cards_detailed_success(self, partner_service_instance, mock_db, sample_cards):
        """Test successful detailed cards retrieval"""
        with patch.object(partner_service_instance, 'db') as mock_db_context:
            mock_db_context.return_value.__enter__.return_value = mock_db
            
            # Mock query chain
            mock_query = Mock()
            mock_query.filter.return_value = mock_query
            mock_query.count.return_value = 3
            mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = sample_cards
            
            mock_db.query.return_value = mock_query
            
            result = await partner_service_instance.get_partner_cards_detailed(
                partner_id=12345,
                status="approved",
                page=1,
                per_page=10
            )
            
            assert len(result["cards"]) == 3
            assert result["total"] == 3
            assert result["current_page"] == 1
            assert result["has_next"] is False
            assert result["has_previous"] is False
            
            # Check first card
            first_card = result["cards"][0]
            assert first_card["id"] == 1
            assert first_card["title"] == "Test Card 1"
            assert first_card["status"] == "approved"
    
    @pytest.mark.asyncio
    async def test_get_partner_qr_codes_success(self, partner_service_instance, mock_db, sample_qr_codes):
        """Test successful QR codes retrieval"""
        with patch.object(partner_service_instance, 'db') as mock_db_context:
            mock_db_context.return_value.__enter__.return_value = mock_db
            
            # Mock query chain
            mock_query = Mock()
            mock_query.join.return_value.filter.return_value.order_by.return_value.all.return_value = sample_qr_codes
            
            mock_db.query.return_value = mock_query
            
            result = await partner_service_instance.get_partner_qr_codes(12345)
            
            assert len(result) == 2
            assert result[0]["id"] == 1
            assert result[0]["code"] == "QR001"
            assert result[0]["value"] == 100
            assert result[0]["is_active"] is True
    
    @pytest.mark.asyncio
    async def test_get_partner_analytics_success(self, partner_service_instance, mock_db):
        """Test successful analytics retrieval"""
        # Mock analytics data
        mock_daily_stats = [
            Mock(date=datetime.utcnow().date(), scans=5),
            Mock(date=(datetime.utcnow() - timedelta(days=1)).date(), scans=3)
        ]
        
        mock_top_cards = [
            Mock(id=1, title="Top Card 1", views=20, scans=5),
            Mock(id=2, title="Top Card 2", views=15, scans=3)
        ]
        
        mock_category_stats = [
            Mock(category_id=1, cards_count=2, total_views=35, total_scans=8)
        ]
        
        with patch.object(partner_service_instance, 'db') as mock_db_context:
            mock_db_context.return_value.__enter__.return_value = mock_db
            
            # Mock different query results
            mock_db.query.return_value.join.return_value.filter.return_value.group_by.return_value.all.return_value = mock_daily_stats
            mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_top_cards
            mock_db.query.return_value.filter.return_value.group_by.return_value.all.return_value = mock_category_stats
            
            result = await partner_service_instance.get_partner_analytics(12345, days=30)
            
            assert len(result["daily_activity"]) == 2
            assert len(result["top_cards"]) == 2
            assert len(result["category_performance"]) == 1
            
            assert result["top_cards"][0]["title"] == "Top Card 1"
            assert result["top_cards"][0]["views"] == 20
    
    @pytest.mark.asyncio
    async def test_update_partner_settings_success(self, partner_service_instance, mock_db, sample_partner):
        """Test successful settings update"""
        with patch.object(partner_service_instance, 'db') as mock_db_context:
            mock_db_context.return_value.__enter__.return_value = mock_db
            mock_db.query.return_value.filter.return_value.first.return_value = sample_partner
            
            settings_data = {
                "display_name": "Updated Partner",
                "phone": "+9876543210",
                "email": "updated@partner.com"
            }
            
            result = await partner_service_instance.update_partner_settings(12345, settings_data)
            
            assert result is True
            assert sample_partner.display_name == "Updated Partner"
            assert sample_partner.phone == "+9876543210"
            assert sample_partner.email == "updated@partner.com"
            mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_partner_settings_not_found(self, partner_service_instance, mock_db):
        """Test settings update when partner not found"""
        with patch.object(partner_service_instance, 'db') as mock_db_context:
            mock_db_context.return_value.__enter__.return_value = mock_db
            mock_db.query.return_value.filter.return_value.first.return_value = None
            
            settings_data = {"display_name": "Updated Partner"}
            
            result = await partner_service_instance.update_partner_settings(99999, settings_data)
            
            assert result is False
    
    def test_calculate_conversion_rate(self, partner_service_instance):
        """Test conversion rate calculation"""
        # Normal case
        assert partner_service_instance._calculate_conversion_rate(100, 25) == 25.0
        
        # Zero views
        assert partner_service_instance._calculate_conversion_rate(0, 10) == 0.0
        
        # Zero scans
        assert partner_service_instance._calculate_conversion_rate(100, 0) == 0.0
        
        # Rounding
        assert partner_service_instance._calculate_conversion_rate(33, 10) == 30.3
    
    @pytest.mark.asyncio
    async def test_get_partner_profile_error_handling(self, partner_service_instance, mock_db):
        """Test error handling in get_partner_profile"""
        with patch.object(partner_service_instance, 'db') as mock_db_context:
            mock_db_context.return_value.__enter__.return_value = mock_db
            mock_db.query.side_effect = Exception("Database error")
            
            result = await partner_service_instance.get_partner_profile(12345)
            
            assert result == {}
    
    @pytest.mark.asyncio
    async def test_get_partner_cards_detailed_with_filters(self, partner_service_instance, mock_db, sample_cards):
        """Test cards retrieval with various filters"""
        with patch.object(partner_service_instance, 'db') as mock_db_context:
            mock_db_context.return_value.__enter__.return_value = mock_db
            
            mock_query = Mock()
            mock_query.filter.return_value = mock_query
            mock_query.count.return_value = 1
            mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [sample_cards[0]]
            
            mock_db.query.return_value = mock_query
            
            result = await partner_service_instance.get_partner_cards_detailed(
                partner_id=12345,
                status="approved",
                category_id=1,
                search="Test",
                page=1,
                per_page=5
            )
            
            assert len(result["cards"]) == 1
            assert result["total"] == 1
            # Verify filters were applied
            mock_query.filter.assert_called()


class TestPartnerServiceIntegration:
    """Integration tests for PartnerService"""
    
    @pytest.mark.asyncio
    async def test_service_instance_creation(self):
        """Test that service instance is created correctly"""
        assert partner_service is not None
        assert isinstance(partner_service, PartnerService)
    
    @pytest.mark.asyncio
    async def test_service_methods_exist(self):
        """Test that all required methods exist"""
        assert hasattr(partner_service, 'get_partner_profile')
        assert hasattr(partner_service, 'get_partner_cards_detailed')
        assert hasattr(partner_service, 'get_partner_qr_codes')
        assert hasattr(partner_service, 'get_partner_analytics')
        assert hasattr(partner_service, 'update_partner_settings')
        assert hasattr(partner_service, '_calculate_conversion_rate')
    
    @pytest.mark.asyncio
    async def test_method_signatures(self):
        """Test method signatures are correct"""
        import inspect
        
        # Check get_partner_profile signature
        sig = inspect.signature(partner_service.get_partner_profile)
        assert 'partner_id' in sig.parameters
        assert sig.parameters['partner_id'].annotation == int
        
        # Check get_partner_cards_detailed signature
        sig = inspect.signature(partner_service.get_partner_cards_detailed)
        assert 'partner_id' in sig.parameters
        assert 'status' in sig.parameters
        assert 'category_id' in sig.parameters
        assert 'search' in sig.parameters
        assert 'page' in sig.parameters
        assert 'per_page' in sig.parameters
