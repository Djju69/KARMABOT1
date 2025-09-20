"""
Unit tests for new services: referral_service, profile_service, geo utils
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4

from core.services.referral_service import ReferralService
from core.services.profile_service import ProfileService
from core.utils.geo import haversine_distance, nearest_places, format_distance


class TestReferralService:
    """Test cases for ReferralService"""
    
    def setup_method(self):
        """Setup test instance"""
        self.service = ReferralService()
    
    def test_referral_service_init(self):
        """Test ReferralService initialization"""
        assert self.service.referrer_bonus == 100
        assert self.service.referee_bonus == 50
        assert len(self.service.levels) == 3
        assert self.service.levels[1] == 0.10
        assert self.service.levels[2] == 0.05
        assert self.service.levels[3] == 0.02
    
    @pytest.mark.asyncio
    async def test_create_referral_code(self):
        """Test referral code creation"""
        user_id = str(uuid4())
        
        with patch('core.services.referral_service.get_db') as mock_get_db:
            mock_db = AsyncMock()
            mock_get_db.return_value.__aenter__.return_value = mock_db
            
            # Mock database query
            mock_db.execute.return_value.scalar_one_or_none.return_value = None
            mock_db.commit = AsyncMock()
            
            result = await self.service.create_referral_code(user_id)
            
            assert result.startswith("REF")
            assert len(result) == 11  # REF + 8 chars
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_referral_stats(self):
        """Test getting referral statistics"""
        user_id = str(uuid4())
        
        with patch('core.services.referral_service.get_db') as mock_get_db:
            mock_db = AsyncMock()
            mock_get_db.return_value.__aenter__.return_value = mock_db
            
            # Mock database queries
            mock_db.execute.return_value.scalar.return_value = 5  # direct_refs
            mock_db.execute.return_value.scalar.return_value = 1000  # total_earned
            mock_db.execute.return_value.scalar_one_or_none.return_value = "REF12345678"  # referral_code
            
            result = await self.service.get_referral_stats(user_id)
            
            assert 'total_referrals' in result
            assert 'total_earned' in result
            assert 'referral_link' in result
            assert 'referral_code' in result
            assert result['referrer_bonus'] == 100
            assert result['referee_bonus'] == 50


class TestProfileService:
    """Test cases for ProfileService"""
    
    def setup_method(self):
        """Setup test instance"""
        self.service = ProfileService()
    
    @pytest.mark.asyncio
    async def test_get_user_profile(self):
        """Test getting user profile"""
        user_id = "12345"
        
        with patch('core.services.profile_service.get_db') as mock_get_db:
            mock_db = AsyncMock()
            mock_get_db.return_value.__aenter__.return_value = mock_db
            
            # Mock database queries
            mock_db.execute.return_value.scalar_one_or_none.return_value = None  # balance
            mock_db.execute.return_value.scalar.return_value = 0  # transactions_count
            mock_db.execute.return_value.scalar.return_value = 0  # activities_count
            
            result = await self.service.get_user_profile(user_id)
            
            assert result['user_id'] == user_id
            assert 'username' in result
            assert 'loyalty_balance' in result
            assert 'stats' in result
            assert result['is_active'] is True
    
    @pytest.mark.asyncio
    async def test_get_user_settings(self):
        """Test getting user settings"""
        user_id = "12345"
        
        result = await self.service.get_user_settings(user_id)
        
        assert 'language' in result
        assert 'notifications' in result
        assert 'privacy' in result
        assert 'preferences' in result
        assert result['language'] == 'ru'
        assert result['notifications']['email'] is True
    
    @pytest.mark.asyncio
    async def test_update_user_settings(self):
        """Test updating user settings"""
        user_id = "12345"
        new_settings = {
            'language': 'en',
            'notifications': {
                'email': False
            }
        }
        
        result = await self.service.update_user_settings(user_id, new_settings)
        
        assert result['language'] == 'en'
        assert result['notifications']['email'] is False
        assert result['notifications']['push'] is True  # Should remain unchanged
    
    @pytest.mark.asyncio
    async def test_get_user_notifications(self):
        """Test getting user notifications"""
        user_id = "12345"
        
        result = await self.service.get_user_notifications(user_id, limit=5)
        
        assert isinstance(result, list)
        assert len(result) <= 5
        if result:
            assert 'id' in result[0]
            assert 'title' in result[0]
            assert 'message' in result[0]
            assert 'is_read' in result[0]


class TestGeoUtils:
    """Test cases for geo utilities"""
    
    def test_haversine_distance(self):
        """Test haversine distance calculation"""
        # Distance between Moscow and St. Petersburg (approximately 635 km)
        moscow_lat, moscow_lon = 55.7558, 37.6176
        spb_lat, spb_lon = 59.9311, 30.3609
        
        distance = haversine_distance(moscow_lat, moscow_lon, spb_lat, spb_lon)
        
        # Should be approximately 635 km (allowing 10% error)
        assert 570 <= distance <= 700
    
    def test_haversine_distance_same_point(self):
        """Test haversine distance for same point"""
        lat, lon = 55.7558, 37.6176
        distance = haversine_distance(lat, lon, lat, lon)
        assert distance == 0.0
    
    def test_nearest_places(self):
        """Test finding nearest places"""
        user_lat, user_lon = 55.7558, 37.6176
        
        places = [
            {
                'id': 1,
                'name': 'Near Place',
                'latitude': 55.7568,  # ~100m away
                'longitude': 37.6186
            },
            {
                'id': 2,
                'name': 'Far Place',
                'latitude': 55.7658,  # ~1km away
                'longitude': 37.6276
            },
            {
                'id': 3,
                'name': 'No Coords',
                'name': 'No Coords'
                # No latitude/longitude
            }
        ]
        
        result = nearest_places(user_lat, user_lon, places, radius_km=1.0)
        
        assert len(result) == 2  # Only 2 places with coordinates
        assert result[0]['distance_km'] < result[1]['distance_km']  # Sorted by distance
        assert 'distance_km' in result[0]
        assert 'distance_km' in result[1]
    
    def test_format_distance(self):
        """Test distance formatting"""
        assert format_distance(0.5) == "500 м"
        assert format_distance(1.0) == "1.0 км"
        assert format_distance(1.5) == "1.5 км"
        assert format_distance(10.0) == "10.0 км"
    
    def test_format_distance_edge_cases(self):
        """Test distance formatting edge cases"""
        assert format_distance(0.0) == "0 м"
        assert format_distance(0.001) == "1 м"
        assert format_distance(0.999) == "999 м"


class TestIntegration:
    """Integration tests for new services"""
    
    @pytest.mark.asyncio
    async def test_referral_and_profile_integration(self):
        """Test integration between referral and profile services"""
        user_id = str(uuid4())
        
        # Mock database for both services
        with patch('core.services.referral_service.get_db') as mock_ref_db, \
             patch('core.services.profile_service.get_db') as mock_prof_db:
            
            # Setup mock databases
            mock_ref_db.return_value.__aenter__.return_value = AsyncMock()
            mock_prof_db.return_value.__aenter__.return_value = AsyncMock()
            
            # Test that both services can be instantiated and used
            ref_service = ReferralService()
            prof_service = ProfileService()
            
            # These should not raise exceptions
            assert ref_service.referrer_bonus == 100
            assert prof_service is not None
    
    def test_geo_utils_integration(self):
        """Test integration of geo utilities"""
        # Test with real-world coordinates
        user_lat, user_lon = 55.7558, 37.6176  # Moscow
        
        places = [
            {
                'id': 1,
                'name': 'Red Square',
                'latitude': 55.7539,
                'longitude': 37.6208
            },
            {
                'id': 2,
                'name': 'Bolshoi Theatre',
                'latitude': 55.7596,
                'longitude': 37.6194
            }
        ]
        
        # Test the full pipeline
        nearby = nearest_places(user_lat, user_lon, places, radius_km=2.0)
        
        assert len(nearby) == 2
        assert all('distance_km' in place for place in nearby)
        assert all(place['distance_km'] <= 2.0 for place in nearby)
        
        # Test formatting
        for place in nearby:
            formatted = format_distance(place['distance_km'])
            assert isinstance(formatted, str)
            assert 'м' in formatted or 'км' in formatted


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
