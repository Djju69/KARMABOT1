"""
Миграция 013: Многоуровневая реферальная система
"""
import sqlite3
import logging
import os
import psycopg2
from psycopg2 import errors as pg_errors
from typing import Optional

logger = logging.getLogger(__name__)

def migrate_013_multilevel_referral_system(conn: sqlite3.Connection):
    """
    Миграция 013: Создание таблиц для многоуровневой реферальной системы (SQLite)
    """
    cursor = conn.cursor()
    
    logger.info("Applying SQLite migration 013: Multilevel referral system")
    
    # Создание таблицы дерева рефералов
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS referral_tree (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id BIGINT NOT NULL,
            referrer_id BIGINT NULL,
            level INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_earnings DECIMAL(10, 2) DEFAULT 0,
            total_referrals INTEGER DEFAULT 0,
            active_referrals INTEGER DEFAULT 0
        );
    """)
    
    # Создание таблицы бонусов рефералов
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS referral_bonuses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            referrer_id BIGINT NOT NULL,
            referred_id BIGINT NOT NULL,
            level INTEGER NOT NULL,
            bonus_amount DECIMAL(10, 2) NOT NULL,
            source_transaction_id INTEGER NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # Создание таблицы статистики рефералов
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS referral_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id BIGINT NOT NULL UNIQUE,
            total_referrals INTEGER DEFAULT 0,
            active_referrals INTEGER DEFAULT 0,
            total_earnings DECIMAL(10, 2) DEFAULT 0,
            level_1_earnings DECIMAL(10, 2) DEFAULT 0,
            level_2_earnings DECIMAL(10, 2) DEFAULT 0,
            level_3_earnings DECIMAL(10, 2) DEFAULT 0,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # Добавление индексов
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_referral_tree_user_id ON referral_tree (user_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_referral_tree_referrer_id ON referral_tree (referrer_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_referral_bonuses_referrer_id ON referral_bonuses (referrer_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_referral_bonuses_referred_id ON referral_bonuses (referred_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_referral_stats_user_id ON referral_stats (user_id);")
    
    conn.commit()
    logger.info("SQLite migration 013 applied successfully.")

def ensure_multilevel_referral_system(database_url: Optional[str] = None):
    """
    Ensure multilevel referral system tables exist in PostgreSQL.
    """
    if not database_url:
        database_url = os.getenv('DATABASE_URL')
    
    if not database_url or not database_url.startswith("postgresql"):
        logger.info("Skipping PostgreSQL referral migration: not a PostgreSQL database.")
        return
    
    logger.info("Ensuring PostgreSQL multilevel referral system tables...")
    
    conn = None
    try:
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        
        # Create referral_tree table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS referral_tree (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                referrer_id BIGINT NULL,
                level INTEGER DEFAULT 1,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                total_earnings DECIMAL(10, 2) DEFAULT 0,
                total_referrals INTEGER DEFAULT 0,
                active_referrals INTEGER DEFAULT 0
            );
        """)
        
        # Create referral_bonuses table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS referral_bonuses (
                id SERIAL PRIMARY KEY,
                referrer_id BIGINT NOT NULL,
                referred_id BIGINT NOT NULL,
                level INTEGER NOT NULL,
                bonus_amount DECIMAL(10, 2) NOT NULL,
                source_transaction_id INTEGER NULL,
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
        """)
        
        # Create referral_stats table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS referral_stats (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL UNIQUE,
                total_referrals INTEGER DEFAULT 0,
                active_referrals INTEGER DEFAULT 0,
                total_earnings DECIMAL(10, 2) DEFAULT 0,
                level_1_earnings DECIMAL(10, 2) DEFAULT 0,
                level_2_earnings DECIMAL(10, 2) DEFAULT 0,
                level_3_earnings DECIMAL(10, 2) DEFAULT 0,
                last_updated TIMESTAMPTZ DEFAULT NOW()
            );
        """)
        
        # Add indexes
        cur.execute("CREATE INDEX IF NOT EXISTS idx_referral_tree_user_id ON referral_tree (user_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_referral_tree_referrer_id ON referral_tree (referrer_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_referral_bonuses_referrer_id ON referral_bonuses (referrer_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_referral_bonuses_referred_id ON referral_bonuses (referred_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_referral_stats_user_id ON referral_stats (user_id);")
        
        conn.commit()
        logger.info("✅ PostgreSQL multilevel referral system tables created/verified.")
        
    except pg_errors.DuplicateTable:
        logger.info("PostgreSQL referral tables already exist, skipping creation.")
        if conn:
            conn.rollback()
    except Exception as e:
        logger.error(f"Error ensuring PostgreSQL multilevel referral system: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()
