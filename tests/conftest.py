"""
Test configuration and fixtures for KarmaBot tests.
"""
import os
import sys
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from typing import Generator, AsyncGenerator

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- Environment Setup ---
# Set up test environment variables before importing any application code
os.environ["BOT_TOKEN"] = "test_token"
os.environ["ADMIN_IDS"] = "12345,67890"
os.environ["DB_URL"] = "sqlite:///:memory:"

# --- Mock Settings ---
class MockFeatures:
    """Mock feature flags for testing."""
    def __init__(self):
        self.moderation = True
        self.partner_fsm = True
        self.admin_panel = True
        self.qr_webapp = True
        self.listen_notify = True

class MockSettings:
    """Mock application settings for testing."""
    def __init__(self):
        self.features = MockFeatures()
        self.bots = MagicMock()
        self.bots.admin_id = 12345
        self.debug = False
        # Minimal fields used by webapp_auth and CORS/CSP in tests
        self.jwt_secret = "debug"  # allow dev signing
        self.environment = "development"
        self.webapp_allowed_origin = "*"
        self.csp_allowed_origin = "*"
        # Add database attribute with a mock URL
        self.database = type('Object', (), {'url': 'sqlite:///:memory:'})()

# Mock the settings module before it's imported by other modules
sys.modules['core.settings'] = MagicMock()
sys.modules['core.settings'].settings = MockSettings()

# Now import the rest of the test dependencies
from core.settings import settings  # This will use our mock
from core.services.loyalty import LoyaltyService

# --- Core Fixtures ---
@pytest.fixture(scope="session", autouse=True)
def setup_environment():
    """Set up test environment before any tests run."""
    # Patch environment variables
    with patch.dict(os.environ, {
        "BOT_TOKEN": "test_token",
        "ADMIN_IDS": "12345,67890",
        "DB_URL": "sqlite:///:memory:"
    }):
        yield

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(autouse=True)
def mock_settings():
    """Mock the settings module."""
    with patch('core.settings.settings', MockSettings()) as mock:
        yield mock

# --- Service Mocks ---
@pytest.fixture
def mock_db():
    """Mock database operations."""
    with patch('core.handlers.admin_cabinet.db_v2') as mock:
        mock.delete_card = AsyncMock(return_value=True)
        yield mock

@pytest.fixture
def loyalty_service_mock():
    """Fixture with a mock of the LoyaltyService."""
    mock = AsyncMock(spec=LoyaltyService)
    mock.get_balance.return_value = 100
    mock.get_recent_transactions.return_value = []
    mock.adjust_balance.return_value = 150  # Default new balance after adjustment
    return mock

@pytest.fixture
def mock_cache():
    """Mock cache service for loyalty tests."""
    cache = AsyncMock()
    cache.get.return_value = None  # Default to cache miss
    return cache

@pytest.fixture
def mock_admins():
    """Mock admin service."""
    with patch('core.handlers.admin_cabinet.admins_service') as mock:
        mock.is_admin.return_value = True
        yield mock

@pytest.fixture
def mock_profile():
    """Mock profile service."""
    with patch('core.handlers.admin_cabinet.profile_service') as mock:
        mock.get_lang.return_value = 'ru'
        yield mock

# --- Telegram Mocks ---
@pytest.fixture
def mock_update():
    """Create a mock Telegram update."""
    update = AsyncMock()
    update.callback_query = AsyncMock()
    update.callback_query.data = ""
    update.callback_query.from_user.id = 12345
    update.callback_query.answer = AsyncMock()
    update.callback_query.message = AsyncMock()
    return update

@pytest.fixture
def mock_context():
    """Create a mock context for handlers."""
    context = AsyncMock()
    context.bot = AsyncMock()
    context.args = []
    return context
