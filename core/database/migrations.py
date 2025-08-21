"""
Database migrations for KARMABOT1 following EXPAND → MIGRATE → CONTRACT strategy
Non-breaking migrations with backward compatibility
"""
import sqlite3
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class DatabaseMigrator:
    def __init__(self, db_path: str = "core/database/data.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection with foreign keys enabled"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    
    def init_migration_table(self):
        """Initialize migration tracking table"""
        with self.get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version TEXT PRIMARY KEY,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    description TEXT
                )
            """)
    
    def is_migration_applied(self, version: str) -> bool:
        """Check if migration is already applied"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT 1 FROM schema_migrations WHERE version = ?", 
                (version,)
            )
            return cursor.fetchone() is not None
    
    def apply_migration(self, version: str, description: str, sql: str):
        """Apply migration if not already applied (idempotent)"""
        if self.is_migration_applied(version):
            logger.info(f"Migration {version} already applied, skipping")
            return
        
        with self.get_connection() as conn:
            try:
                # Execute migration SQL
                conn.executescript(sql)
                
                # Record migration
                conn.execute(
                    "INSERT INTO schema_migrations (version, description) VALUES (?, ?)",
                    (version, description)
                )
                
                logger.info(f"Applied migration {version}: {description}")
            except Exception as e:
                logger.error(f"Failed to apply migration {version}: {e}")
                raise
    
    def migrate_001_expand_legacy_tables(self):
        """
        EXPAND Phase: Create legacy tables for backward compatibility
        """
        sql = """
        -- Legacy categories table (keep existing structure)
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name_ru TEXT,
            name_en TEXT,
            name_ko TEXT,
            type TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Legacy restaurants table (keep existing structure)
        CREATE TABLE IF NOT EXISTS restaurants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            description TEXT,
            latitude REAL,
            longitude REAL,
            category_id INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories(id)
        );
        
        -- Legacy services table (keep existing structure)
        CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name_ru TEXT,
            name_en TEXT,
            name_ko TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        self.apply_migration(
            "001", 
            "EXPAND: Create legacy tables for backward compatibility",
            sql
        )
    
    def migrate_002_expand_new_schema(self):
        """
        EXPAND Phase: Add new tables for partners and cards system
        """
        sql = """
        -- New categories table with enhanced structure
        CREATE TABLE IF NOT EXISTS categories_v2 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            emoji TEXT,
            priority_level INTEGER DEFAULT 0,
            is_active BOOLEAN DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Partners table for business owners
        CREATE TABLE IF NOT EXISTS partners_v2 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tg_user_id INTEGER UNIQUE NOT NULL,
            display_name TEXT,
            phone TEXT,
            email TEXT,
            is_verified BOOLEAN DEFAULT 0,
            is_active BOOLEAN DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Cards table for business listings
        CREATE TABLE IF NOT EXISTS cards_v2 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            partner_id INTEGER NOT NULL,
            category_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            contact TEXT,
            address TEXT,
            google_maps_url TEXT,
            photo_file_id TEXT,
            discount_text TEXT,
            status TEXT NOT NULL CHECK(status IN ('draft','pending','approved','published','rejected','archived')) DEFAULT 'draft',
            priority_level INTEGER DEFAULT 0,
            view_count INTEGER DEFAULT 0,
            is_featured BOOLEAN DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (partner_id) REFERENCES partners_v2(id) ON DELETE CASCADE,
            FOREIGN KEY (category_id) REFERENCES categories_v2(id) ON DELETE RESTRICT
        );
        
        -- QR codes table for tracking
        CREATE TABLE IF NOT EXISTS qr_codes_v2 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            card_id INTEGER NOT NULL,
            qr_token TEXT UNIQUE NOT NULL,
            is_redeemed BOOLEAN DEFAULT 0,
            redeemed_at TEXT,
            redeemed_by INTEGER,
            expires_at TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (card_id) REFERENCES cards_v2(id) ON DELETE CASCADE
        );
        
        -- Moderation log
        CREATE TABLE IF NOT EXISTS moderation_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            card_id INTEGER NOT NULL,
            moderator_id INTEGER NOT NULL,
            action TEXT NOT NULL CHECK(action IN ('approve','reject','archive','feature')),
            comment TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (card_id) REFERENCES cards_v2(id) ON DELETE CASCADE
        );
        
        -- Indexes for performance
        CREATE INDEX IF NOT EXISTS idx_cards_v2_status ON cards_v2(status);
        CREATE INDEX IF NOT EXISTS idx_cards_v2_category ON cards_v2(category_id);
        CREATE INDEX IF NOT EXISTS idx_cards_v2_partner ON cards_v2(partner_id);
        CREATE INDEX IF NOT EXISTS idx_qr_codes_v2_token ON qr_codes_v2(qr_token);
        """
        
        self.apply_migration(
            "002",
            "EXPAND: Add new schema for partners and cards system",
            sql
        )
    
    def migrate_003_seed_default_data(self):
        """
        EXPAND Phase: Seed default categories (idempotent)
        """
        sql = """
        -- Insert default categories if they don't exist
        INSERT OR IGNORE INTO categories_v2 (slug, name, emoji, priority_level) VALUES
        ('restaurants', '🍜 Рестораны', '🍜', 100),
        ('spa', '🧘 SPA и массаж', '🧘', 90),
        ('transport', '🛵 Аренда байков', '🛵', 80),
        ('hotels', '🏨 Отели', '🏨', 70),
        ('tours', '🗺️ Экскурсии', '🗺️', 60);
        
        -- Backward compatibility: sync with legacy categories
        INSERT OR IGNORE INTO categories (name_ru, type) 
        SELECT name, slug FROM categories_v2;
        """
        
        self.apply_migration(
            "003",
            "EXPAND: Seed default categories with backward compatibility",
            sql
        )
    
    def run_all_migrations(self):
        """Run all pending migrations in order"""
        logger.info("Starting database migrations...")
        
        self.init_migration_table()
        self.migrate_001_expand_legacy_tables()
        self.migrate_002_expand_new_schema()
        self.migrate_003_seed_default_data()
        
        logger.info("All migrations completed successfully")

# Global migrator instance
migrator = DatabaseMigrator()

def ensure_database_ready():
    """Ensure database is migrated and ready to use"""
    try:
        migrator.run_all_migrations()
        return True
    except Exception as e:
        logger.error(f"Database migration failed: {e}")
        return False
