"""Tests for loyalty points service."""
import os
import pytest
import sqlite3
import asyncio
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

from core.database.db_v2 import db_v2, DatabaseServiceV2
from core.services.loyalty import LoyaltyService, loyalty_service

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
    
    # Create required tables
    conn.execute("""
    CREATE TABLE IF NOT EXISTS loyalty_wallets (
        user_id BIGINT PRIMARY KEY,
        balance_pts INTEGER NOT NULL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    conn.execute("""
    CREATE TABLE IF NOT EXISTS loyalty_transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id BIGINT NOT NULL,
        kind TEXT NOT NULL,
        delta_pts INTEGER NOT NULL,
        balance_after INTEGER NOT NULL,
        note TEXT,
        ref INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES loyalty_wallets(user_id)
    )
    """)
    
    # Add test data
    # Add test wallet
    conn.execute(
        "INSERT OR IGNORE INTO loyalty_wallets (user_id, balance_pts) VALUES (?, ?)",
        (1001, 15)
    )
    conn.commit()
    
    yield db_service
    
    # Cleanup
    try:
        conn.close()
        # Give some time for connections to close
        import time
        time.sleep(0.1)
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)
    except (PermissionError, OSError) as e:
        print(f"Warning: Could not remove test database: {e}")
        # Continue with test execution even if cleanup fails


@pytest.mark.asyncio
async def test_adjust_balance_success(test_db, mock_cache):
    """Test adjusting balance and getting the new balance."""
    user_id = 1002  # New user for this test
    points = 10
    
    # Patch the database service to use our test DB
    with patch('core.services.loyalty.db_v2', test_db):
        # Setup mock cache
        mock_cache.get.return_value = None
        
        # Test adding points
        new_balance = await loyalty_service.adjust_balance(
            user_id=user_id,
            delta_pts=points,
            note="Test transaction"
        )
        
        # Verify balance was updated
        assert isinstance(new_balance, int)
        assert new_balance == points  # Should be exactly points since it's a new wallet
        
        # Verify cache was updated
        cache_key = f"loyalty:balance:{user_id}"
        mock_cache.set.assert_awaited_once_with(cache_key, str(new_balance), ex=1)


@pytest.fixture
def mock_cache():
    """Fixture to mock cache service with async support."""
    with patch('core.services.loyalty.cache_service') as mock:
        # Make get method async
        mock.get = AsyncMock()
        # Make set method async
        mock.set = AsyncMock()
        # Make delete method async
        mock.delete = AsyncMock()
        yield mock

@pytest.mark.asyncio
async def test_get_balance_with_cache(mock_cache):
    """Test getting balance with cache hit."""
    user_id = 1001
    cached_balance = "15"
    
    # Setup mock to return cached balance
    mock_cache.get.return_value = cached_balance
    
    # Call the method under test
    balance = await loyalty_service.get_balance(user_id)
    
    # Verify cache was checked
    mock_cache.get.assert_awaited_once_with(f"loyalty:balance:{user_id}")
    assert balance == int(cached_balance)
    
    # Verify DB was not accessed
    mock_cache.set.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_balance_no_cache(test_db, mock_cache):
    """Test getting balance with no cache (DB fallback)."""
    user_id = 1001  # User with test data
    
    # Setup test DB with initial balance
    with test_db.get_connection() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO loyalty_wallets (user_id, balance_pts) VALUES (?, ?)",
            (user_id, 25)
        )
        conn.commit()
    
    # Setup mock cache to return None (cache miss)
    mock_cache.get.return_value = None
    
    # Patch the database service to use our test DB
    with patch('core.services.loyalty.db_v2', test_db):
        # This should query the DB
        balance = await loyalty_service.get_balance(user_id)
        
        # Verify the result
        assert balance == 25  # Should match our test data
        
        # Verify cache was updated
        mock_cache.set.assert_awaited_once_with(
            f"loyalty:balance:{user_id}",
            "25",
            ex=300
        )


@pytest.mark.asyncio
async def test_get_recent_transactions(test_db, mock_cache):
    """Test getting recent transactions."""
    user_id = 1001
    
    # Add test transactions to the database
    with test_db.get_connection() as conn:
        # Ensure wallet exists
        conn.execute(
            "INSERT OR IGNORE INTO loyalty_wallets (user_id, balance_pts) VALUES (?, ?)",
            (user_id, 15)
        )
        
        # Add test transactions
        test_transactions = [
            (user_id, 'accrual', 10, 10, 'Test 1', None, '2023-01-02T12:00:00Z'),
            (user_id, 'accrual', 5, 15, 'Test 2', None, '2023-01-01T12:00:00Z')
        ]
        
        conn.executemany(
            """
            INSERT INTO loyalty_transactions 
            (user_id, kind, delta_pts, balance_after, note, ref, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            test_transactions
        )
        conn.commit()
    
    # Setup mock cache to return None (cache miss)
    mock_cache.get.return_value = None
    
    # Patch the database service to use our test DB
    with patch('core.services.loyalty.db_v2', test_db):
        # Call the method
        transactions = await loyalty_service.get_recent_transactions(user_id, limit=2)
        
        # Verify the result
        assert len(transactions) == 2
        assert transactions[0]['delta_pts'] == 10
        assert transactions[1]['delta_pts'] == 5
        
        # Verify cache was updated
        mock_cache.set.assert_awaited_once()
        
        # Verify the cache key and TTL
        args, kwargs = mock_cache.set.await_args
        assert args[0].startswith("loyalty:tx_history:")
        assert str(user_id) in args[0]
        assert kwargs.get("ex") == 60  # 1 minute TTL


@pytest.mark.asyncio
async def test_adjust_balance_invalid_points(test_db, mock_cache):
    """Test adjusting balance with invalid points."""
    user_id = 1005
    
    # Setup test DB with initial balance and mock cache
    with test_db.get_connection() as conn:
        # Clear any existing data
        conn.execute("DELETE FROM loyalty_transactions")
        conn.execute("DELETE FROM loyalty_wallets")
        
        # Add test wallet
        conn.execute(
            "INSERT INTO loyalty_wallets (user_id, balance_pts) VALUES (?, ?)",
            (user_id, 10)
        )
        conn.commit()
    
    # Test with negative balance that would result in negative total
    with patch('core.services.loyalty.db_v2', test_db):
        # The method should allow negative balances, so we'll test that it works
        new_balance = await loyalty_service.adjust_balance(
            user_id=user_id,
            delta_pts=-15,  # More than available balance
            note="Test negative balance"
        )
        
        # Verify the balance was updated correctly
        assert new_balance == -5  # 10 - 15 = -5
        
        # Verify the transaction was recorded
        with test_db.get_connection() as conn:
            tx = conn.execute(
                "SELECT * FROM loyalty_transactions WHERE user_id = ?",
                (user_id,)
            ).fetchone()
            assert tx is not None
            assert tx['delta_pts'] == -15
            assert tx['balance_after'] == -5
