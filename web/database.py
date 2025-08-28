"""
Database health check module for KarmaBot web service.
"""
import os
from typing import Tuple

def check_database_health() -> Tuple[bool, str]:
    """
    Check database connection health.
    
    Returns:
        Tuple[bool, str]: (is_healthy, detail_message)
    """
    url = os.getenv("DATABASE_URL", "").strip()
    
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
