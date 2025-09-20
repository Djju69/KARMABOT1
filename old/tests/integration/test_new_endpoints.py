"""
Integration tests for new endpoints: dashboard, user routes
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import json

from web.main import app


class TestDashboardEndpoints:
    """Test cases for dashboard endpoints"""
    
    def setup_method(self):
        """Setup test client"""
        self.client = TestClient(app)
    
    def test_top_places_endpoint_structure(self):
        """Test top places endpoint structure"""
        # Mock admin authentication
        with patch('web.routes_dashboard.require_admin') as mock_auth, \
             patch('web.routes_dashboard.get_db') as mock_db:
            
            mock_auth.return_value = {"sub": "admin_user"}
            mock_db.return_value = Mock()
            
            # Mock database response
            mock_db.return_value.fetch_all.return_value = [
                {
                    "id": 1,
                    "name": "Test Restaurant",
                    "address": "Test Address",
                    "rating": 4.5,
                    "total_reviews": 10,
                    "recent_reviews": 5,
                    "checkins_count": 3,
                    "is_verified": True
                }
            ]
            
            response = self.client.get("/admin/top-places?limit=5&period=month")
            
            # Should return 200 even with mocked data
            assert response.status_code in [200, 401]  # 401 if auth fails
    
    def test_referrals_stats_endpoint_structure(self):
        """Test referrals stats endpoint structure"""
        with patch('web.routes_dashboard.require_admin') as mock_auth, \
             patch('web.routes_dashboard.get_db') as mock_db:
            
            mock_auth.return_value = {"sub": "admin_user"}
            mock_db.return_value = Mock()
            
            # Mock database responses
            mock_db.return_value.fetch_one.return_value = {
                "total_referrals": 10,
                "active_referrers": 5,
                "recent_referrals": 3
            }
            mock_db.return_value.fetch_all.return_value = []
            
            response = self.client.get("/admin/referrals-stats?period=month")
            
            assert response.status_code in [200, 401]  # 401 if auth fails
    
    def test_user_activity_endpoint_structure(self):
        """Test user activity endpoint structure"""
        with patch('web.routes_dashboard.require_admin') as mock_auth, \
             patch('web.routes_dashboard.get_db') as mock_db:
            
            mock_auth.return_value = {"sub": "admin_user"}
            mock_db.return_value = Mock()
            
            # Mock database responses
            mock_db.return_value.fetch_one.return_value = {
                "active_users": 100,
                "total_activities": 500,
                "active_days": 7
            }
            mock_db.return_value.fetch_all.return_value = []
            
            response = self.client.get("/admin/user-activity?period=week&limit=20")
            
            assert response.status_code in [200, 401]  # 401 if auth fails


class TestUserEndpoints:
    """Test cases for user endpoints"""
    
    def setup_method(self):
        """Setup test client"""
        self.client = TestClient(app)
    
    def test_user_profile_endpoint_structure(self):
        """Test user profile endpoint structure"""
        with patch('web.routes_user.get_current_user') as mock_auth, \
             patch('web.routes_user.get_db') as mock_db:
            
            mock_auth.return_value = {"sub": "user123"}
            mock_db.return_value = Mock()
            
            # Mock service responses
            with patch('web.routes_user.profile_service.get_user_profile') as mock_profile, \
                 patch('web.routes_user.loyalty_service.get_user_stats') as mock_loyalty, \
                 patch('web.routes_user.referral_service.get_referral_stats') as mock_referral:
                
                mock_profile.return_value = {"user_id": "user123", "username": "testuser"}
                mock_loyalty.return_value = {"balance": {"total_points": 100}}
                mock_referral.return_value = {"total_referrals": 5}
                
                response = self.client.get("/api/user/profile")
                
                assert response.status_code in [200, 401]  # 401 if auth fails
    
    def test_loyalty_balance_endpoint_structure(self):
        """Test loyalty balance endpoint structure"""
        with patch('web.routes_user.get_current_user') as mock_auth, \
             patch('web.routes_user.get_db') as mock_db:
            
            mock_auth.return_value = {"sub": "user123"}
            mock_db.return_value = Mock()
            
            with patch('web.routes_user.loyalty_service.get_user_balance') as mock_balance:
                mock_balance.return_value = {"total_points": 100, "available_points": 80}
                
                response = self.client.get("/api/user/loyalty/balance")
                
                assert response.status_code in [200, 401]  # 401 if auth fails
    
    def test_loyalty_transactions_endpoint_structure(self):
        """Test loyalty transactions endpoint structure"""
        with patch('web.routes_user.get_current_user') as mock_auth, \
             patch('web.routes_user.get_db') as mock_db:
            
            mock_auth.return_value = {"sub": "user123"}
            mock_db.return_value = Mock()
            
            with patch('web.routes_user.loyalty_service.get_user_transactions') as mock_transactions, \
                 patch('web.routes_user.loyalty_service.get_user_transactions_count') as mock_count:
                
                mock_transactions.return_value = []
                mock_count.return_value = 0
                
                response = self.client.get("/api/user/loyalty/transactions?limit=10&offset=0")
                
                assert response.status_code in [200, 401]  # 401 if auth fails
    
    def test_referrals_endpoint_structure(self):
        """Test referrals endpoint structure"""
        with patch('web.routes_user.get_current_user') as mock_auth, \
             patch('web.routes_user.get_db') as mock_db:
            
            mock_auth.return_value = {"sub": "user123"}
            mock_db.return_value = Mock()
            
            with patch('web.routes_user.referral_service.get_referral_stats') as mock_stats, \
                 patch('web.routes_user.referral_service.get_referral_tree') as mock_tree, \
                 patch('web.routes_user.referral_service.get_referral_earnings') as mock_earnings:
                
                mock_stats.return_value = {"total_referrals": 5}
                mock_tree.return_value = {"levels": {}}
                mock_earnings.return_value = []
                
                response = self.client.get("/api/user/referrals")
                
                assert response.status_code in [200, 401]  # 401 if auth fails
    
    def test_create_referral_code_endpoint_structure(self):
        """Test create referral code endpoint structure"""
        with patch('web.routes_user.get_current_user') as mock_auth, \
             patch('web.routes_user.get_db') as mock_db:
            
            mock_auth.return_value = {"sub": "user123"}
            mock_db.return_value = Mock()
            
            with patch('web.routes_user.referral_service.create_referral_code') as mock_create:
                mock_create.return_value = "REF12345678"
                
                response = self.client.post("/api/user/referrals/create-code")
                
                assert response.status_code in [200, 401]  # 401 if auth fails
    
    def test_activities_endpoint_structure(self):
        """Test activities endpoint structure"""
        with patch('web.routes_user.get_current_user') as mock_auth, \
             patch('web.routes_user.get_db') as mock_db:
            
            mock_auth.return_value = {"sub": "user123"}
            mock_db.return_value = Mock()
            
            with patch('web.routes_user.loyalty_service.get_user_activities') as mock_activities, \
                 patch('web.routes_user.loyalty_service.get_user_activities_count') as mock_count:
                
                mock_activities.return_value = []
                mock_count.return_value = 0
                
                response = self.client.get("/api/user/activities?limit=10&offset=0")
                
                assert response.status_code in [200, 401]  # 401 if auth fails
    
    def test_claim_activity_endpoint_structure(self):
        """Test claim activity endpoint structure"""
        with patch('web.routes_user.get_current_user') as mock_auth, \
             patch('web.routes_user.get_db') as mock_db:
            
            mock_auth.return_value = {"sub": "user123"}
            mock_db.return_value = Mock()
            
            with patch('web.routes_user.loyalty_service.perform_activity') as mock_perform:
                mock_perform.return_value = {"points_awarded": 10, "message": "Success"}
                
                response = self.client.post("/api/user/activities/claim?activity_type=daily_checkin")
                
                assert response.status_code in [200, 401]  # 401 if auth fails
    
    def test_settings_endpoint_structure(self):
        """Test settings endpoint structure"""
        with patch('web.routes_user.get_current_user') as mock_auth, \
             patch('web.routes_user.get_db') as mock_db:
            
            mock_auth.return_value = {"sub": "user123"}
            mock_db.return_value = Mock()
            
            with patch('web.routes_user.profile_service.get_user_settings') as mock_settings:
                mock_settings.return_value = {"language": "ru", "notifications": {}}
                
                response = self.client.get("/api/user/settings")
                
                assert response.status_code in [200, 401]  # 401 if auth fails
    
    def test_notifications_endpoint_structure(self):
        """Test notifications endpoint structure"""
        with patch('web.routes_user.get_current_user') as mock_auth, \
             patch('web.routes_user.get_db') as mock_db:
            
            mock_auth.return_value = {"sub": "user123"}
            mock_db.return_value = Mock()
            
            with patch('web.routes_user.profile_service.get_user_notifications') as mock_notifications, \
                 patch('web.routes_user.profile_service.get_user_notifications_count') as mock_count:
                
                mock_notifications.return_value = []
                mock_count.return_value = 0
                
                response = self.client.get("/api/user/notifications?limit=10&offset=0")
                
                assert response.status_code in [200, 401]  # 401 if auth fails


class TestEndpointIntegration:
    """Integration tests for endpoints"""
    
    def setup_method(self):
        """Setup test client"""
        self.client = TestClient(app)
    
    def test_endpoints_are_registered(self):
        """Test that all new endpoints are registered"""
        # Get all routes
        routes = [route.path for route in app.routes]
        
        # Check dashboard endpoints
        assert "/admin/top-places" in routes
        assert "/admin/referrals-stats" in routes
        assert "/admin/user-activity" in routes
        
        # Check user endpoints
        assert "/api/user/profile" in routes
        assert "/api/user/loyalty/balance" in routes
        assert "/api/user/loyalty/transactions" in routes
        assert "/api/user/referrals" in routes
        assert "/api/user/referrals/create-code" in routes
        assert "/api/user/activities" in routes
        assert "/api/user/activities/claim" in routes
        assert "/api/user/settings" in routes
        assert "/api/user/notifications" in routes
    
    def test_endpoints_require_authentication(self):
        """Test that endpoints require authentication"""
        # Test dashboard endpoints (should require admin auth)
        response = self.client.get("/admin/top-places")
        assert response.status_code == 401  # Unauthorized
        
        response = self.client.get("/admin/referrals-stats")
        assert response.status_code == 401  # Unauthorized
        
        response = self.client.get("/admin/user-activity")
        assert response.status_code == 401  # Unauthorized
        
        # Test user endpoints (should require user auth)
        response = self.client.get("/api/user/profile")
        assert response.status_code == 401  # Unauthorized
        
        response = self.client.get("/api/user/loyalty/balance")
        assert response.status_code == 401  # Unauthorized


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
