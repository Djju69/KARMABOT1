"""
Unit tests for Enhanced Admin Panel
Tests comprehensive admin functionality
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from web.routes_admin_enhanced import router, DashboardStats, UserResponse, ActivityResponse
from core.models import User, Card, Transaction, ModerationLog
from core.security.jwt_service import verify_admin_token

class TestEnhancedAdminPanel:
    """Test enhanced admin panel functionality"""
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def mock_admin_claims(self):
        """Mock admin claims"""
        return {
            "user_id": 123,
            "role": "admin",
            "username": "test_admin"
        }
    
    @pytest.fixture
    def sample_users(self):
        """Sample user data"""
        return [
            User(
                id=1,
                full_name="Test User 1",
                username="testuser1",
                email="test1@example.com",
                role="user",
                is_active=True,
                created_at=datetime.utcnow()
            ),
            User(
                id=2,
                full_name="Test Partner",
                username="testpartner",
                email="partner@example.com",
                role="partner",
                is_active=True,
                created_at=datetime.utcnow()
            )
        ]
    
    @pytest.fixture
    def sample_transactions(self):
        """Sample transaction data"""
        return [
            Transaction(
                id=1,
                user_id=1,
                amount=100.0,
                transaction_type="purchase",
                created_at=datetime.utcnow()
            ),
            Transaction(
                id=2,
                user_id=2,
                amount=250.0,
                transaction_type="purchase",
                created_at=datetime.utcnow()
            )
        ]
    
    def test_dashboard_stats_model(self):
        """Test DashboardStats model"""
        stats = DashboardStats(
            total_users=100,
            active_partners=25,
            pending_moderation=5,
            today_transactions=15,
            total_revenue=10000.0,
            system_uptime="99.9%",
            users_change=12.5,
            partners_change=8.3,
            transactions_change=15.7,
            revenue_change=22.1
        )
        
        assert stats.total_users == 100
        assert stats.active_partners == 25
        assert stats.pending_moderation == 5
        assert stats.today_transactions == 15
        assert stats.total_revenue == 10000.0
        assert stats.system_uptime == "99.9%"
        assert stats.users_change == 12.5
        assert stats.partners_change == 8.3
        assert stats.transactions_change == 15.7
        assert stats.revenue_change == 22.1
    
    def test_user_response_model(self):
        """Test UserResponse model"""
        user = UserResponse(
            id=1,
            full_name="Test User",
            username="testuser",
            email="test@example.com",
            role="user",
            is_active=True,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            total_transactions=5,
            total_spent=500.0
        )
        
        assert user.id == 1
        assert user.full_name == "Test User"
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.role == "user"
        assert user.is_active is True
        assert user.total_transactions == 5
        assert user.total_spent == 500.0
    
    def test_activity_response_model(self):
        """Test ActivityResponse model"""
        activity = ActivityResponse(
            id=1,
            type="user",
            title="New user registered",
            description="User signed up",
            user_id=123,
            created_at=datetime.utcnow(),
            metadata={"role": "user"}
        )
        
        assert activity.id == 1
        assert activity.type == "user"
        assert activity.title == "New user registered"
        assert activity.description == "User signed up"
        assert activity.user_id == 123
        assert activity.metadata == {"role": "user"}
    
    @patch('web.routes_admin_enhanced.get_db')
    @patch('web.routes_admin_enhanced.get_current_admin')
    async def test_get_enhanced_dashboard_success(self, mock_get_admin, mock_get_db, mock_db_session, mock_admin_claims, sample_users, sample_transactions):
        """Test successful dashboard data retrieval"""
        # Setup mocks
        mock_get_admin.return_value = mock_admin_claims
        mock_get_db.return_value = mock_db_session
        
        # Mock database queries
        mock_db_session.query.return_value.count.return_value = 100
        mock_db_session.query.return_value.filter.return_value.count.return_value = 25
        mock_db_session.query.return_value.filter.return_value.count.return_value = 5
        mock_db_session.query.return_value.filter.return_value.count.return_value = 15
        mock_db_session.query.return_value.scalar.return_value = 10000.0
        
        # Test the endpoint
        from web.routes_admin_enhanced import get_enhanced_dashboard
        
        result = await get_enhanced_dashboard(mock_admin_claims, mock_db_session)
        
        assert isinstance(result, DashboardStats)
        assert result.total_users == 100
        assert result.active_partners == 25
        assert result.pending_moderation == 5
        assert result.today_transactions == 15
        assert result.total_revenue == 10000.0
    
    @patch('web.routes_admin_enhanced.get_db')
    @patch('web.routes_admin_enhanced.get_current_admin')
    async def test_get_admin_users_success(self, mock_get_admin, mock_get_db, mock_db_session, mock_admin_claims, sample_users):
        """Test successful user list retrieval"""
        # Setup mocks
        mock_get_admin.return_value = mock_admin_claims
        mock_get_db.return_value = mock_db_session
        
        # Mock database queries
        mock_db_session.query.return_value.count.return_value = 2
        mock_db_session.query.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = sample_users
        mock_db_session.query.return_value.filter.return_value.all.return_value = []
        
        # Test the endpoint
        from web.routes_admin_enhanced import get_admin_users
        
        result = await get_admin_users(1, 20, None, None, None, mock_admin_claims, mock_db_session)
        
        assert "users" in result
        assert "total" in result
        assert "total_pages" in result
        assert "current_page" in result
        assert result["total"] == 2
        assert result["current_page"] == 1
        assert len(result["users"]) == 2
    
    @patch('web.routes_admin_enhanced.get_db')
    @patch('web.routes_admin_enhanced.get_current_admin')
    async def test_get_recent_activity_success(self, mock_get_admin, mock_get_db, mock_db_session, mock_admin_claims, sample_users, sample_transactions):
        """Test successful recent activity retrieval"""
        # Setup mocks
        mock_get_admin.return_value = mock_admin_claims
        mock_get_db.return_value = mock_db_session
        
        # Mock database queries
        mock_db_session.query.return_value.order_by.return_value.limit.return_value.all.return_value = sample_users
        mock_db_session.query.return_value.order_by.return_value.limit.return_value.all.return_value = sample_transactions
        mock_db_session.query.return_value.order_by.return_value.limit.return_value.all.return_value = []
        
        # Test the endpoint
        from web.routes_admin_enhanced import get_recent_activity
        
        result = await get_recent_activity(20, mock_admin_claims, mock_db_session)
        
        assert isinstance(result, list)
        assert len(result) > 0
        
        # Check activity structure
        activity = result[0]
        assert hasattr(activity, 'id')
        assert hasattr(activity, 'type')
        assert hasattr(activity, 'title')
        assert hasattr(activity, 'created_at')
    
    @patch('web.routes_admin_enhanced.get_db')
    @patch('web.routes_admin_enhanced.get_current_admin')
    async def test_get_analytics_data_success(self, mock_get_admin, mock_get_db, mock_db_session, mock_admin_claims):
        """Test successful analytics data retrieval"""
        # Setup mocks
        mock_get_admin.return_value = mock_admin_claims
        mock_get_db.return_value = mock_db_session
        
        # Mock database queries
        mock_db_session.query.return_value.filter.return_value.count.return_value = 5
        mock_db_session.query.return_value.filter.return_value.count.return_value = 10
        mock_db_session.query.return_value.scalar.return_value = 1000.0
        mock_db_session.query.return_value.join.return_value.filter.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = []
        
        # Test the endpoint
        from web.routes_admin_enhanced import get_analytics_data
        
        result = await get_analytics_data("7d", mock_admin_claims, mock_db_session)
        
        assert hasattr(result, 'period')
        assert hasattr(result, 'users_growth')
        assert hasattr(result, 'transactions_trend')
        assert hasattr(result, 'revenue_breakdown')
        assert hasattr(result, 'top_partners')
        assert hasattr(result, 'popular_categories')
        assert result.period == "7d"
    
    @patch('web.routes_admin_enhanced.get_db')
    @patch('web.routes_admin_enhanced.get_current_admin')
    async def test_get_system_health_success(self, mock_get_admin, mock_get_db, mock_db_session, mock_admin_claims):
        """Test successful system health retrieval"""
        # Setup mocks
        mock_get_admin.return_value = mock_admin_claims
        mock_get_db.return_value = mock_db_session
        
        # Mock database query
        mock_db_session.query.return_value.limit.return_value.first.return_value = sample_users[0]
        
        # Test the endpoint
        from web.routes_admin_enhanced import get_system_health
        
        result = await get_system_health(mock_admin_claims, mock_db_session)
        
        assert hasattr(result, 'status')
        assert hasattr(result, 'uptime')
        assert hasattr(result, 'memory_usage')
        assert hasattr(result, 'cpu_usage')
        assert hasattr(result, 'disk_usage')
        assert hasattr(result, 'database_status')
        assert hasattr(result, 'redis_status')
        assert result.status in ["healthy", "warning", "critical"]
    
    @patch('web.routes_admin_enhanced.get_db')
    @patch('web.routes_admin_enhanced.get_current_admin')
    async def test_toggle_user_status_success(self, mock_get_admin, mock_get_db, mock_db_session, mock_admin_claims, sample_users):
        """Test successful user status toggle"""
        # Setup mocks
        mock_get_admin.return_value = mock_admin_claims
        mock_get_db.return_value = mock_db_session
        
        # Mock database query
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_users[0]
        
        # Test the endpoint
        from web.routes_admin_enhanced import toggle_user_status
        
        result = await toggle_user_status(1, mock_admin_claims, mock_db_session)
        
        assert result["success"] is True
        assert "message" in result
        assert result["user_id"] == 1
        assert "is_active" in result
    
    @patch('web.routes_admin_enhanced.get_db')
    @patch('web.routes_admin_enhanced.get_current_admin')
    async def test_change_user_role_success(self, mock_get_admin, mock_get_db, mock_db_session, mock_admin_claims, sample_users):
        """Test successful user role change"""
        # Setup mocks
        mock_get_admin.return_value = mock_admin_claims
        mock_get_db.return_value = mock_db_session
        
        # Mock database query
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_users[0]
        
        # Test the endpoint
        from web.routes_admin_enhanced import change_user_role
        
        result = await change_user_role(1, "partner", mock_admin_claims, mock_db_session)
        
        assert result["success"] is True
        assert "message" in result
        assert result["user_id"] == 1
        assert result["old_role"] == "user"
        assert result["new_role"] == "partner"
    
    @patch('web.routes_admin_enhanced.get_db')
    @patch('web.routes_admin_enhanced.get_current_admin')
    async def test_change_user_role_invalid_role(self, mock_get_admin, mock_get_db, mock_db_session, mock_admin_claims, sample_users):
        """Test user role change with invalid role"""
        # Setup mocks
        mock_get_admin.return_value = mock_admin_claims
        mock_get_db.return_value = mock_db_session
        
        # Test the endpoint
        from web.routes_admin_enhanced import change_user_role
        
        with pytest.raises(Exception):  # Should raise HTTPException
            await change_user_role(1, "invalid_role", mock_admin_claims, mock_db_session)
    
    @patch('web.routes_admin_enhanced.get_db')
    @patch('web.routes_admin_enhanced.get_current_admin')
    async def test_export_users_success(self, mock_get_admin, mock_get_db, mock_db_session, mock_admin_claims, sample_users):
        """Test successful users export"""
        # Setup mocks
        mock_get_admin.return_value = mock_admin_claims
        mock_get_db.return_value = mock_db_session
        
        # Mock database query
        mock_db_session.query.return_value.all.return_value = sample_users
        
        # Test the endpoint
        from web.routes_admin_enhanced import export_users
        
        result = await export_users("json", mock_admin_claims, mock_db_session)
        
        assert "users" in result
        assert "total" in result
        assert result["total"] == 2
        assert len(result["users"]) == 2
    
    @patch('web.routes_admin_enhanced.get_db')
    @patch('web.routes_admin_enhanced.get_current_admin')
    async def test_get_system_logs_success(self, mock_get_admin, mock_get_db, mock_db_session, mock_admin_claims):
        """Test successful system logs retrieval"""
        # Setup mocks
        mock_get_admin.return_value = mock_admin_claims
        mock_get_db.return_value = mock_db_session
        
        # Test the endpoint
        from web.routes_admin_enhanced import get_system_logs
        
        result = await get_system_logs(None, 100, mock_admin_claims)
        
        assert "logs" in result
        assert "total" in result
        assert isinstance(result["logs"], list)
    
    def test_admin_dashboard_enhanced_template(self):
        """Test admin dashboard enhanced template serving"""
        from web.routes_admin_enhanced import admin_dashboard_enhanced
        
        # Mock request
        mock_request = Mock()
        
        # Test the endpoint
        result = admin_dashboard_enhanced(mock_request)
        
        # Should return HTMLResponse
        assert hasattr(result, 'body')
        assert b"Админ-панель" in result.body
        assert b"KARMABOT1" in result.body

class TestAdminHandlers:
    """Test admin bot handlers"""
    
    @pytest.fixture
    def mock_message(self):
        """Mock Telegram message"""
        message = Mock()
        message.from_user.id = 123
        message.answer = AsyncMock()
        message.edit_text = AsyncMock()
        return message
    
    @pytest.fixture
    def mock_callback(self):
        """Mock Telegram callback query"""
        callback = Mock()
        callback.data = "admin:users"
        callback.message = mock_message
        callback.answer = AsyncMock()
        return callback
    
    @pytest.fixture
    def mock_bot(self):
        """Mock Telegram bot"""
        return Mock()
    
    @pytest.fixture
    def mock_state(self):
        """Mock FSM state"""
        return Mock()
    
    @patch('core.handlers.admin_enhanced.admins_service.is_admin')
    @patch('core.handlers.admin_enhanced.profile_service.get_lang')
    @patch('core.handlers.admin_enhanced.get_system_statistics')
    async def test_open_enhanced_admin_cabinet_success(self, mock_get_stats, mock_get_lang, mock_is_admin, mock_message, mock_bot, mock_state):
        """Test successful admin cabinet opening"""
        # Setup mocks
        mock_is_admin.return_value = True
        mock_get_lang.return_value = "ru"
        mock_get_stats.return_value = {
            "total_users": 100,
            "active_partners": 25,
            "pending_moderation": 5,
            "today_transactions": 15,
            "total_revenue": 10000
        }
        
        # Test the handler
        from core.handlers.admin_enhanced import open_enhanced_admin_cabinet
        
        await open_enhanced_admin_cabinet(mock_message, mock_bot, mock_state)
        
        # Verify message was sent
        mock_message.answer.assert_called_once()
        call_args = mock_message.answer.call_args
        assert "Расширенная админ-панель" in call_args[0][0]
        assert "100" in call_args[0][0]  # total_users
    
    @patch('core.handlers.admin_enhanced.admins_service.is_admin')
    async def test_open_enhanced_admin_cabinet_not_admin(self, mock_is_admin, mock_message, mock_bot, mock_state):
        """Test admin cabinet access denied for non-admin"""
        # Setup mocks
        mock_is_admin.return_value = False
        
        # Test the handler
        from core.handlers.admin_enhanced import open_enhanced_admin_cabinet
        
        await open_enhanced_admin_cabinet(mock_message, mock_bot, mock_state)
        
        # Verify access denied message
        mock_message.answer.assert_called_once_with("❌ Доступ запрещён.")
    
    @patch('core.handlers.admin_enhanced.get_system_statistics')
    async def test_show_user_management_success(self, mock_get_stats, mock_callback, mock_bot):
        """Test successful user management display"""
        # Setup mocks
        mock_get_stats.return_value = {
            "total_users": 100,
            "active_partners": 25,
            "pending_moderation": 5,
            "today_transactions": 15,
            "total_revenue": 10000
        }
        
        # Test the handler
        from core.handlers.admin_enhanced import show_user_management
        
        await show_user_management(mock_callback, mock_bot)
        
        # Verify message was edited
        mock_callback.message.edit_text.assert_called_once()
        call_args = mock_callback.message.edit_text.call_args
        assert "Управление пользователями" in call_args[0][0]
    
    @patch('core.handlers.admin_enhanced.get_system_statistics')
    async def test_show_moderation_panel_success(self, mock_get_stats, mock_callback, mock_bot):
        """Test successful moderation panel display"""
        # Setup mocks
        mock_get_stats.return_value = {
            "total_users": 100,
            "active_partners": 25,
            "pending_moderation": 5,
            "today_transactions": 15,
            "total_revenue": 10000
        }
        
        # Test the handler
        from core.handlers.admin_enhanced import show_moderation_panel
        
        await show_moderation_panel(mock_callback, mock_bot)
        
        # Verify message was edited
        mock_callback.message.edit_text.assert_called_once()
        call_args = mock_callback.message.edit_text.call_args
        assert "Панель модерации" in call_args[0][0]
    
    @patch('core.handlers.admin_enhanced.get_system_health')
    async def test_show_system_monitoring_success(self, mock_get_health, mock_callback, mock_bot):
        """Test successful system monitoring display"""
        # Setup mocks
        mock_get_health.return_value = {
            "status": "healthy",
            "uptime": "99.9%",
            "memory_usage": 65.2,
            "cpu_usage": 23.8,
            "disk_usage": 45.7
        }
        
        # Test the handler
        from core.handlers.admin_enhanced import show_system_monitoring
        
        await show_system_monitoring(mock_callback, mock_bot)
        
        # Verify message was edited
        mock_callback.message.edit_text.assert_called_once()
        call_args = mock_callback.message.edit_text.call_args
        assert "Мониторинг системы" in call_args[0][0]
        assert "99.9%" in call_args[0][0]
    
    async def test_open_webapp_dashboard_success(self, mock_callback, mock_bot):
        """Test successful WebApp dashboard opening"""
        # Test the handler
        from core.handlers.admin_enhanced import open_webapp_dashboard
        
        await open_webapp_dashboard(mock_callback, mock_bot)
        
        # Verify message was edited
        mock_callback.message.edit_text.assert_called_once()
        call_args = mock_callback.message.edit_text.call_args
        assert "WebApp админ-дашборд" in call_args[0][0]

if __name__ == "__main__":
    pytest.main([__file__])
