from __future__ import annotations
import os
import sqlite3
from typing import Tuple

def _is_sqlite(url: str) -> bool:
    return url.startswith("sqlite:///")

def _sqlite_path(url: str) -> str:
    return url.replace("sqlite:///", "", 1)

def _table_exists_sqlite(conn: sqlite3.Connection, table: str) -> bool:
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    )
    return cur.fetchone() is not None

def _col_exists_sqlite(conn: sqlite3.Connection, table: str, col: str) -> bool:
    cur = conn.execute(f"PRAGMA table_info('{table}')")
    return any(r[1] == col for r in cur.fetchall())

def _ensure_sqlite_schema(path: str) -> Tuple[bool, str]:
    conn = sqlite3.connect(path)
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                created_at TEXT
            );
        """)
        if not _col_exists_sqlite(conn, "categories", "name_ru"):
            conn.execute("ALTER TABLE categories ADD COLUMN name_ru TEXT;")
        if not _col_exists_sqlite(conn, "categories", "name_en"):
            conn.execute("ALTER TABLE categories ADD COLUMN name_en TEXT;")

        conn.execute("""
            INSERT OR IGNORE INTO categories (id, name, name_ru, name_en, created_at)
            VALUES (1, 'Restaurants', 'Рестораны', 'Restaurants', datetime('now'));
        """)
        conn.commit()
        return True, "sqlite schema ok"
    except Exception as e:
        return False, f"sqlite schema error: {str(e)}"
    finally:
        conn.close()

def check_database_health() -> Tuple[bool, str]:
    """Check if the database is accessible and has the required schema.
    
    Returns:
        Tuple of (is_healthy: bool, message: str)
    """
    url = os.getenv("DATABASE_URL", "sqlite:///app.db").strip()
    if _is_sqlite(url):
        path = _sqlite_path(url)
        ok, detail = _ensure_sqlite_schema(path)
        if not ok:
            return False, detail
        conn = sqlite3.connect(path)
        try:
            required = ["categories"]
            missing = [t for t in required if not _table_exists_sqlite(conn, t)]
            if missing:
                return False, f"Missing required tables: {', '.join(missing)}"
        finally:
            conn.close()
        return True, "ok (sqlite)"
    else:
        return True, "ok (non-sqlite url; check skipped)"
