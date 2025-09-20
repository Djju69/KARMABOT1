"""Fixtures for integration tests."""
import pytest
import asyncio
import aiosqlite
import os
import tempfile
from unittest.mock import patch, AsyncMock
from datetime import datetime, timedelta

# Test data
TEST_ADMIN = {
    'id': 1,
    'username': 'testadmin',
    'role': 'admin',
    'is_active': True,
    'created_at': datetime.utcnow() - timedelta(days=30)
}

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="module")
async def test_database():
    """Create and set up a test SQLite database."""
    # Create a temporary database file
    db_fd, db_path = tempfile.mkstemp()
    
    # Connect to the SQLite database
    conn = await aiosqlite.connect(db_path)
    
    # Enable foreign keys
    await conn.execute("PRAGMA foreign_keys = ON")
    await conn.commit()
    
    try:
        # Set up test schema and data
        # Create users table with all required fields
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT NOT NULL,
                role TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        # Create listings table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS listings (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                status TEXT NOT NULL,
                category TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        # Create other necessary tables (listings, etc.)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS listings (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                status TEXT NOT NULL,
                category TEXT,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
        """)
        
        # Commit the schema
        await conn.commit()
        
        # Insert test admin user with all required fields
        now = datetime.utcnow().isoformat()
        await conn.execute(
            """
            INSERT INTO users (id, username, role, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                TEST_ADMIN['id'],
                TEST_ADMIN['username'],
                TEST_ADMIN['role'],
                int(TEST_ADMIN['is_active']),
                TEST_ADMIN['created_at'].isoformat(),
                now  # updated_at
            )
        )
        await conn.commit()
        
        # Yield the connection for tests to use
        yield conn
        
    finally:
        # Clean up: close connection and remove temp file
        await conn.close()
        os.close(db_fd)
        os.unlink(db_path)

@pytest.fixture(scope="module")
async def admin_application():
    """Create a test application with admin privileges."""
    from aiogram import Bot, Dispatcher
    from aiogram.types import Update
    
    # Create a mock bot
    bot = MagicMock(spec=Bot)
    
    # Create a dispatcher
    dp = Dispatcher()
    
    # Add database connection to bot data
    dp.bot = bot
    dp.bot.data = {}
    dp.bot.data['db'] = test_database
    
    # Mock admin checks
    dp['is_admin'] = AsyncMock(return_value=True)
    dp['is_superadmin'] = AsyncMock(return_value=True)
    
    # Add database to context
    dp['db'] = test_database
    
    return dp

@pytest.fixture
def mock_telegram_update():
    """Create a mock Telegram update object."""
    from telegram import Update, Message, Chat, User
    
    update = MagicMock(spec=Update)
    update.message = MagicMock(spec=Message)
    update.message.chat = MagicMock(spec=Chat)
    update.message.from_user = MagicMock(spec=User)
    update.message.from_user.id = TEST_ADMIN['id']
    update.message.from_user.username = TEST_ADMIN['username']
    update.message.from_user.first_name = 'Test'
    update.message.from_user.last_name = 'User'
    update.message.chat_id = 12345
    update.message.message_id = 1
    update.message.text = "/test"
    
    # Add reply_text mock
    update.message.reply_text = AsyncMock()
    
    return update

@pytest.fixture
def mock_telegram_context():
    """Create a mock Telegram context object."""
    context = MagicMock()
    context.bot = MagicMock()
    context.bot.send_message = AsyncMock()
    context.args = []
    context.user_data = {}
    context.chat_data = {}
    context.bot_data = {}
    return context
