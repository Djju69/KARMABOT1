"""
Database configuration and session management for KarmaBot web service.
"""
import os
from typing import Tuple, Generator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./karmabot.db")

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
    pool_pre_ping=True
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """Dependency for getting database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def get_db_ctx() -> Generator[Session, None, None]:
    """Context manager for database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def check_database_health() -> Tuple[bool, str]:
    """
    Check database connection health.
    
    Returns:
        Tuple[bool, str]: (is_healthy, detail_message)
    """
    url = DATABASE_URL.strip()
    
    if not url:
        return False, "DATABASE_URL not set"
        
    if url.startswith('sqlite'):
        # SQLite health check
        try:
            import sqlite3
            db_path = url.replace('sqlite://', '')
            if db_path.startswith('/'):
                db_path = db_path[1:]
            conn = sqlite3.connect(db_path)
            conn.close()
            return True, "ok (sqlite)"
        except Exception as e:
            return False, f"SQLite check failed: {str(e)}"
    
    elif url.startswith('postgres'):
        # PostgreSQL health check
        try:
            import psycopg2
            conn = psycopg2.connect(url)
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                if cur.fetchone()[0] == 1:
                    return True, "ok (postgres)"
            return False, "PostgreSQL query failed"
        except ImportError:
            return False, "psycopg2 not installed"
        except Exception as e:
            return False, f"PostgreSQL check failed: {str(e)}"
    
    return False, f"Unsupported database type: {url.split(':')[0]}"

def init_db():
    """Initialize database tables."""
    import web.models  # Import models to register them with SQLAlchemy
    Base.metadata.create_all(bind=engine)
    return "Database tables created"
