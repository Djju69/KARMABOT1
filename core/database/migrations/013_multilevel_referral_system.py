"""
Миграция 013: Многоуровневая реферальная система
"""
import sqlite3
import logging
import os
from datetime import datetime
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

def migrate_013_multilevel_referral_system(conn: sqlite3.Connection | Any):
    """Migration 013: Multilevel referral system"""
    version = "013"
    description = "Create multilevel referral system tables and triggers"
    
    is_postgres = isinstance(conn, Any) and hasattr(conn, 'cursor') # Simplified check for psycopg2 connection
    
    try:
        if is_postgres:
            cursor = conn.cursor()
            
            # Create referral_tree table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS referral_tree (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    referrer_id BIGINT NULL,
                    level INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT NOW(),
                    total_earnings DECIMAL(10, 2) DEFAULT 0,
                    total_referrals INTEGER DEFAULT 0,
                    active_referrals INTEGER DEFAULT 0,
                    
                    FOREIGN KEY (referrer_id) REFERENCES referral_tree(id) ON DELETE SET NULL
                );
            """)
            
            # Create referral_bonuses table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS referral_bonuses (
                    id SERIAL PRIMARY KEY,
                    referrer_id BIGINT NOT NULL,
                    referred_id BIGINT NOT NULL,
                    level INTEGER NOT NULL,
                    bonus_amount DECIMAL(10, 2) NOT NULL,
                    source_transaction_id INTEGER NULL,
                    created_at TIMESTAMP DEFAULT NOW(),
                    
                    FOREIGN KEY (source_transaction_id) REFERENCES loyalty_transactions(id) ON DELETE SET NULL
                );
            """)
            
            # Create referral_stats table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS referral_stats (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL UNIQUE,
                    level_1_referrals INTEGER DEFAULT 0,
                    level_2_referrals INTEGER DEFAULT 0,
                    level_3_referrals INTEGER DEFAULT 0,
                    total_earnings DECIMAL(10, 2) DEFAULT 0,
                    last_bonus_at TIMESTAMP NULL,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                );
            """)
            
            # Create indexes
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_referral_tree_user_id ON referral_tree(user_id);
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_referral_tree_referrer_id ON referral_tree(referrer_id);
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_referral_tree_level ON referral_tree(level);
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_referral_bonuses_referrer ON referral_bonuses(referrer_id);
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_referral_bonuses_referred ON referral_bonuses(referred_id);
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_referral_bonuses_level ON referral_bonuses(level);
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_referral_stats_user_id ON referral_stats(user_id);
            """)
            
            conn.commit()
            cursor.close()
            
        else: # SQLite
            cursor = conn.cursor()
            
            # Create referral_tree table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS referral_tree (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    referrer_id INTEGER NULL,
                    level INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT (datetime('now')),
                    total_earnings REAL DEFAULT 0,
                    total_referrals INTEGER DEFAULT 0,
                    active_referrals INTEGER DEFAULT 0,
                    
                    FOREIGN KEY (referrer_id) REFERENCES referral_tree(id) ON DELETE SET NULL
                )
            """)
            
            # Create referral_bonuses table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS referral_bonuses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    referrer_id INTEGER NOT NULL,
                    referred_id INTEGER NOT NULL,
                    level INTEGER NOT NULL,
                    bonus_amount REAL NOT NULL,
                    source_transaction_id INTEGER NULL,
                    created_at TEXT DEFAULT (datetime('now')),
                    
                    FOREIGN KEY (source_transaction_id) REFERENCES loyalty_transactions(id) ON DELETE SET NULL
                )
            """)
            
            # Create referral_stats table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS referral_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL UNIQUE,
                    level_1_referrals INTEGER DEFAULT 0,
                    level_2_referrals INTEGER DEFAULT 0,
                    level_3_referrals INTEGER DEFAULT 0,
                    total_earnings REAL DEFAULT 0,
                    last_bonus_at TEXT NULL,
                    created_at TEXT DEFAULT (datetime('now')),
                    updated_at TEXT DEFAULT (datetime('now'))
                )
            """)
            
            # Create indexes
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_referral_tree_user_id ON referral_tree(user_id);
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_referral_tree_referrer_id ON referral_tree(referrer_id);
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_referral_tree_level ON referral_tree(level);
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_referral_bonuses_referrer ON referral_bonuses(referrer_id);
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_referral_bonuses_referred ON referral_bonuses(referred_id);
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_referral_bonuses_level ON referral_bonuses(level);
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_referral_stats_user_id ON referral_stats(user_id);
            """)
            
            conn.commit()
        
        logger.info(f"Applied migration {version}: {description}")
        
    except Exception as e:
        logger.error(f"Failed to apply migration {version}: {e}")
        raise

def ensure_multilevel_referral_system():
    """Ensure multilevel referral system is ready for PostgreSQL"""
    try:
        import psycopg2
        from core.settings import settings
        
        # Parse database URL
        parsed_url = urlparse(settings.database.url)
        
        # Connect to PostgreSQL
        conn = psycopg2.connect(
            host=parsed_url.hostname,
            port=parsed_url.port or 5432,
            database=parsed_url.path[1:],  # Remove leading slash
            user=parsed_url.username,
            password=parsed_url.password
        )
        
        try:
            migrate_013_multilevel_referral_system(conn)
            logger.info("✅ Multilevel referral system ready for PostgreSQL")
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"❌ Failed to ensure multilevel referral system: {e}")
        raise
