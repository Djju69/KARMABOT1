"""Integration tests for admin panel workflows."""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta

# Test data
TEST_ADMIN = {
    'id': 1,
    'username': 'testadmin',
    'role': 'admin',
    'is_active': True,
    'created_at': datetime.utcnow() - timedelta(days=30)
}

TEST_LISTING = {
    'id': 1001,
    'name': 'Test Listing',
    'status': 'pending',
    'category': 'test',
    'created_at': datetime.utcnow() - timedelta(hours=1),
    'updated_at': datetime.utcnow() - timedelta(hours=1)
}

class TestAdminPanelIntegration:
    """Integration tests for admin panel workflows."""
    
    @pytest.fixture(autouse=True)
    def setup_mocks(self):
        """Setup common mocks for all tests."""
        # Mock authentication
        self.auth_patcher = patch('app.middleware.auth.is_admin', new_callable=AsyncMock, return_value=True)
        self.superadmin_patcher = patch('app.middleware.auth.is_superadmin', new_callable=AsyncMock, return_value=True)
        
        self.mock_is_admin = self.auth_patcher.start()
        self.mock_is_superadmin = self.superadmin_patcher.start()
        
        yield
        
        # Cleanup
        self.auth_patcher.stop()
        self.superadmin_patcher.stop()
    
    @pytest.mark.asyncio
    async def test_moderation_workflow(self, admin_application, test_database):
        """Test complete moderation workflow."""
        from tests.integration.utils import create_text_update, process_update
        
        # 1. Add test data to database
        await test_database.execute(
            """
            INSERT INTO users (id, username, role, is_active, created_at)
            VALUES ($1, $2, $3, $4, $5)
            """,
            TEST_ADMIN['id'],
            TEST_ADMIN['username'],
            TEST_ADMIN['role'],
            TEST_ADMIN['is_active'],
            TEST_ADMIN['created_at']
        )
        
        # 2. Add test listing
        await test_database.execute(
            """
            INSERT INTO listings (id, name, status, category, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6)
            """,
            TEST_LISTING['id'],
            TEST_LISTING['name'],
            TEST_LISTING['status'],
            TEST_LISTING['category'],
            TEST_LISTING['created_at'],
            TEST_LISTING['updated_at']
        )
        
        # 3. View moderation queue
        update = create_text_update("/admin_queue", user_id=TEST_ADMIN['id'])
        response = await process_update(admin_application, update)
        
        # Verify queue contains our test listing
        assert response is not None
        assert "Очередь модерации" in response
        assert TEST_LISTING['name'] in response
        
        # 4. View listing details
        update = create_text_update(
            f"/admin_queue_view {TEST_LISTING['id']}", 
            user_id=TEST_ADMIN['id']
        )
        response = await process_update(admin_application, update)
        
        # Verify listing details
        assert response is not None
        assert TEST_LISTING['name'] in response
        assert "Статус: pending" in response
        
        # 5. Approve the listing
        update = create_text_update(
            f"/admin_queue_approve {TEST_LISTING['id']}",
            user_id=TEST_ADMIN['id']
        )
        response = await process_update(admin_application, update)
        
        # Verify approval
        assert response is not None
        assert "✅ Одобрено" in response
        
        # 6. Verify listing is no longer in queue
        update = create_text_update("/admin_queue", user_id=TEST_ADMIN['id'])
        response = await process_update(admin_application, update)
        
        # Verify queue doesn't contain our test listing anymore
        assert response is not None
        assert TEST_LISTING['name'] not in response
    
    @pytest.mark.asyncio
    async def test_admin_management_workflow(self, admin_application, test_database):
        """Test admin management workflow (for superadmins)."""
        from tests.integration.utils import create_text_update, process_update
        
        # 1. Add test superadmin to database
        await test_database.execute(
            """
            INSERT INTO users (id, username, role, is_active, created_at)
            VALUES ($1, $2, $3, $4, $5)
            """,
            TEST_ADMIN['id'],
            TEST_ADMIN['username'],
            'superadmin',  # Superadmin role
            True,
            datetime.utcnow()
        )
        
        # 2. Add a test admin to manage
        test_admin_id = 2
        await test_database.execute(
            """
            INSERT INTO users (id, username, role, is_active, created_at)
            VALUES ($1, $2, $3, $4, $5)
            """,
            test_admin_id,
            'testadmin2',
            'admin',
            True,
            datetime.utcnow()
        )
        
        # 3. Search for the admin
        update = create_text_update(
            "/admin_search testadmin2",
            user_id=TEST_ADMIN['id']
        )
        response = await process_update(admin_application, update)
        
        # Verify search results
        assert response is not None
        assert "testadmin2" in response
        
        # 4. View admin details
        update = create_text_update(
            f"/admin_view {test_admin_id}",
            user_id=TEST_ADMIN['id']
        )
        response = await process_update(admin_application, update)
        
        # Verify admin details
        assert response is not None
        assert "testadmin2" in response
        assert "admin" in response
        
        # 5. Navigate back to search results
        update = create_text_update(
            "/admin_back",
            user_id=TEST_ADMIN['id']
        )
        response = await process_update(admin_application, update)
        
        # Verify back navigation
        assert response is not None
        assert "Результаты поиска" in response
    
    @pytest.mark.asyncio
    async def test_report_generation_workflow(self, admin_application, test_database):
        """Test report generation workflow."""
        from tests.integration.utils import create_text_update, process_update
        
        # Add test admin to database
        await test_database.execute(
            """
            INSERT INTO users (id, username, role, is_active, created_at)
            VALUES ($1, $2, $3, $4, $5)
            """,
            TEST_ADMIN['id'],
            TEST_ADMIN['username'],
            'superadmin',
            True,
            datetime.utcnow()
        )
        
        # Test daily report
        update = create_text_update(
            "/admin_reports daily",
            user_id=TEST_ADMIN['id']
        )
        response = await process_update(admin_application, update)
        
        # Verify daily report
        assert response is not None
        assert "Ежедневный отчет" in response
        
        # Test weekly report
        update = create_text_update(
            "/admin_reports weekly",
            user_id=TEST_ADMIN['id']
        )
        response = await process_update(admin_application, update)
        
        # Verify weekly report
        assert response is not None
        assert "Недельный отчет" in response
        
        # Test monthly report
        update = create_text_update(
            "/admin_reports monthly",
            user_id=TEST_ADMIN['id']
        )
        response = await process_update(admin_application, update)
        
        # Verify monthly report
        assert response is not None
        assert "Месячный отчет" in response
