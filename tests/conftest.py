"""
Test configuration and fixtures for admin panel tests.
"""
import os
import sys
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock settings
class MockFeatures:
    """Mock feature flags for testing."""
    moderation = True
    partner_fsm = True

class MockSettings:
    """Mock settings for testing."""
    features = MockFeatures()
    bots = MagicMock(admin_id=12345)

# Apply mocks
@pytest.fixture(autouse=True)
def mock_settings():
    """Mock the settings module."""
    with patch('core.settings.settings', MockSettings()) as mock:
        yield mock

# Database mock
@pytest.fixture
def mock_db():
    """Mock database operations."""
    with patch('core.handlers.admin_cabinet.db_v2') as mock:
        yield mock

# Admin service mock
@pytest.fixture
def mock_admins():
    """Mock admin service."""
    with patch('core.handlers.admin_cabinet.admins_service') as mock:
        mock.is_admin.return_value = True
        yield mock

# Profile service mock
@pytest.fixture
def mock_profile():
    """Mock profile service."""
    with patch('core.handlers.admin_cabinet.profile_service') as mock:
        mock.get_lang.return_value = 'ru'
        yield mock
