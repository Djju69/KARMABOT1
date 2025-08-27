"""Tests for loyalty points service."""
import os
import pytest
import sqlite3
from pathlib import Path
from unittest.mock import patch, MagicMock

from core.database.db_v2 import DatabaseServiceV2
from core.services.loyalty_points import LoyaltyService, loyalty_service

# Test database path
TEST_DB = "test_loyalty.db"


class MockCursor:
    def __init__(self):
        self.lastrowid = 1
        self.description = [('id',), ('created_at',)]
        
    def execute(self, query, params=None):
        self.query = query
        self.params = params
        return self
        
    def fetchone(self):
        if "SUM" in self.query:
            return (100,)  # Mock balance
        return (1, '2023-01-01T00:00:00Z')  # Mock transaction
        
    def fetchall(self):
        return [
            (1, 'checkin', 5, '2023-01-01T12:00:00Z', None),
            (2, 'geocheckin', 10, '2023-01-02T12:00:00Z', None)
        ]


@pytest.fixture(scope="module")
def test_db():
    """Set up a test database with the required tables."""
    # Delete test DB if it exists
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    
    # Create test DB and tables
    db_service = DatabaseServiceV2(TEST_DB)
    conn = db_service.get_connection()
    
    # Create loyalty_points_tx table
    conn.execute("""
    CREATE TABLE IF NOT EXISTS loyalty_points_tx (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id BIGINT NOT NULL,
        rule_code TEXT NOT NULL,
        points INTEGER NOT NULL,
        metadata TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Create index
    conn.execute("""
    CREATE INDEX IF NOT EXISTS idx_loyalty_points_tx_user_id 
    ON loyalty_points_tx(user_id)
    """)
    
    # Add test data
    test_transactions = [
        (1001, 'checkin', 5, None, '2023-01-01T12:00:00Z'),
        (1001, 'geocheckin', 10, None, '2023-01-02T12:00:00Z'),
    ]
    
    conn.executemany(
        """
        INSERT INTO loyalty_points_tx 
        (user_id, rule_code, points, metadata, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        test_transactions
    )
    conn.commit()
    
    yield db_service
    
    # Cleanup
    conn.close()
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)


def test_add_transaction_success(test_db):
    """Test adding a transaction and getting the balance."""
    user_id = 1002  # New user for this test
    rule_code = "test_rule"
    points = 10
    
    # Patch the database service to use our test DB
    with patch('core.services.loyalty_points.db', test_db):
        # Mock cache service
        with patch('core.services.loyalty_points.cache_service') as mock_cache:
            mock_cache.get.return_value = None
            mock_cache.delete.return_value = True
            
            # Test adding points
            result = loyalty_service.add_transaction(
                user_id=user_id,
                rule_code=rule_code,
                points=points,
                metadata={"test": "data"}
            )
            
            # Verify the result
            assert result["points_awarded"] == points
            assert "transaction_id" in result
            assert "balance" in result
            
            # Verify cache was invalidated
            cache_key = f"loyalty:balance:{user_id}"
            mock_cache.delete.assert_called_once_with(cache_key)


@pytest.fixture
def mock_cache():
    """Fixture to mock cache service."""
    with patch('core.services.loyalty_points.cache_service') as mock:
        yield mock

def test_get_balance_with_cache(mock_cache):
    """Test getting balance with cache hit."""
    user_id = 1001
    cached_balance = "15"
    
    # Setup mock to return cached balance
    mock_cache.get.return_value = cached_balance
    
    # Use a real DB mock to verify it's not accessed
    with patch('core.services.loyalty_points.db') as mock_db:
        # Call the method under test
        balance = loyalty_service.get_balance(user_id)
        
        # Verify cache was checked and DB was not accessed
        mock_cache.get.assert_called_once_with(f"loyalty:balance:{user_id}")
        mock_db.get_connection.assert_not_called()
        assert balance == int(cached_balance)


def test_get_balance_no_cache(test_db):
    """Test getting balance with no cache (DB fallback)."""
    user_id = 1001  # User with test data
    
    # Use test DB and mock cache
    with patch('core.services.loyalty_points.db', test_db), \
         patch('core.services.loyalty_points.cache_service.get', return_value=None), \
         patch('core.services.loyalty_points.cache_service.set') as mock_cache_set:
        
        # This should query the DB
        balance = loyalty_service.get_balance(user_id, use_cache=False)
        
        # Should be sum of test transactions (5 + 10 = 15)
        assert balance == 15
        
        # Should have tried to cache the result
        mock_cache_set.assert_called_once()
        args, kwargs = mock_cache_set.call_args
        assert args[0] == f"loyalty:balance:{user_id}"
        assert args[1] == "15"
        assert kwargs["ex"] == 3600  # TTL


def test_get_recent_transactions():
    """Test getting recent transactions."""
    user_id = 1001
    
    # Create a mock cursor with proper description and test data
    mock_cursor = MagicMock()
    mock_cursor.description = [
        ('id',), ('rule_code',), ('points',), ('created_at',), ('metadata',)
    ]
    mock_cursor.fetchall.return_value = [
        (1, 'geocheckin', 10, '2023-01-02T12:00:00Z', None),
        (2, 'checkin', 5, '2023-01-01T12:00:00Z', None)
    ]
    
    # Create a mock connection that returns our cursor
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    
    # Patch the database to use our mock connection
    with patch('core.services.loyalty_points.db.get_connection', return_value=mock_conn):
        # Test without days filter
        transactions = loyalty_service.get_recent_transactions(user_id, limit=2)
        
        # Verify the query was made correctly
        mock_cursor.execute.assert_called_once()
        args, _ = mock_cursor.execute.call_args
        assert "SELECT id, rule_code, points, created_at, metadata" in args[0]
        
        # Convert args[1] to list for comparison to avoid tuple vs list issues
        params = list(args[1])
        assert params == [user_id, 2]  # user_id and limit
        
        # Verify the results
        assert len(transactions) == 2
        assert transactions[0]["rule_code"] == "geocheckin"
        assert transactions[1]["rule_code"] == "checkin"
        
        # Reset mocks for next test
        mock_cursor.execute.reset_mock()
        
        # Test with days filter
        transactions = loyalty_service.get_recent_transactions(user_id, days=30, limit=2)
        
        # Verify the query included the days filter
        args, _ = mock_cursor.execute.call_args
        assert "created_at >=" in args[0]
        
        # Convert params to list for comparison
        params = list(args[1])
        assert params[0] == user_id  # user_id
        # Check that the second param is a string containing '30 days'
        assert '30' in str(params[1])
        assert 'day' in str(params[1]).lower()
        assert params[2] == 2        # limit


def test_add_transaction_invalid_points():
    """Test adding a transaction with invalid points."""
    with pytest.raises(ValueError):
        loyalty_service.add_transaction(1005, "test_rule", 0)
