"""
Database migrations for KARMABOT1 following EXPAND → MIGRATE → CONTRACT strategy
Non-breaking migrations with backward compatibility
"""
import sqlite3
from pathlib import Path
from typing import Optional, Any
import logging
import os

logger = logging.getLogger(__name__)

def _col_exists(conn: sqlite3.Connection, table: str, col: str) -> bool:
    """Check if a column exists in a SQLite table"""
    try:
        cur = conn.execute(f"PRAGMA table_info('{table}')")
        return any(r[1] == col for r in cur.fetchall())
    except sqlite3.Error as e:
        logger.warning(f"Error checking column {col} in {table}: {e}")
        return False

def _ensure_table_categories(conn: sqlite3.Connection) -> None:
    """Ensure categories table exists with all required columns"""
    # Create the base table if it doesn't exist
    conn.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            created_at TEXT
        );
    """)
    
    # Add columns if they don't exist
    for col in ["name_ru", "name_en", "type"]:
        if not _col_exists(conn, "categories", col):
            default = "''" if col.startswith("name_") else "'shop'"
            conn.execute(f"ALTER TABLE categories ADD COLUMN {col} TEXT DEFAULT {default};")
    
    conn.commit()

class DatabaseMigrator:
    def __init__(self, db_path: str = "core/database/data.db"):
        # Поддержка in-memory БД для тестов: нужно единое соединение
        self._is_memory = db_path == ":memory:" or str(db_path).startswith("file::memory:")
        if self._is_memory:
            # Используем shared cache для возможных множественных подключений
            uri = db_path if str(db_path).startswith("file:") else "file::memory:?cache=shared"
            self._conn = sqlite3.connect(uri, uri=True, check_same_thread=False)
            self._conn.execute("PRAGMA foreign_keys = ON")
            self.db_path = None
        else:
            self.db_path = Path(db_path)
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self._conn = None
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection with foreign keys enabled"""
        if self._is_memory and self._conn is not None:
            return self._conn
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    
    def init_migration_table(self):
        """Initialize migration tracking table"""
        if self._is_memory:
            conn = self.get_connection()
            conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version TEXT PRIMARY KEY,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    description TEXT
                )
            """)
            conn.commit()
        else:
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
        if self._is_memory:
            conn = self.get_connection()
            cursor = conn.execute(
                "SELECT 1 FROM schema_migrations WHERE version = ?",
                (version,)
            )
            return cursor.fetchone() is not None
        else:
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
        
        if self._is_memory:
            conn = self.get_connection()
            try:
                conn.executescript(sql)
                conn.execute(
                    "INSERT INTO schema_migrations (version, description) VALUES (?, ?)",
                    (version, description)
                )
                conn.commit()
                logger.info(f"Applied migration {version}: {description}")
            except Exception as e:
                logger.error(f"Failed to apply migration {version}: {e}")
                raise
        else:
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
    
    def migrate_005_loyalty_tables(self):
        """
        EXPAND Phase: Loyalty subsystem tables
        - loyalty_wallets: per-user balance
        - loy_spend_intents: spending intents with TTL and single-active constraint
        - user_cards: bound card registry with uid_hash and last4 only
        - loyalty_transactions: audit log of accruals/redemptions
        """
        sql = """
        -- Wallets: one per Telegram user
        CREATE TABLE IF NOT EXISTS loyalty_wallets (
            user_id INTEGER PRIMARY KEY,
            balance_pts INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        -- Spend intents: ephemeral tokens for redemption flow
        CREATE TABLE IF NOT EXISTS loy_spend_intents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            intent_token TEXT UNIQUE NOT NULL,
            amount_pts INTEGER NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('active','consumed','expired','canceled')) DEFAULT 'active',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            expires_at TEXT,
            consumed_at TEXT,
            UNIQUE(user_id, status) ON CONFLICT IGNORE
        );

        -- Bound user cards: store only hashed UID and last4 for privacy
        CREATE TABLE IF NOT EXISTS user_cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            uid_hash TEXT NOT NULL UNIQUE,
            last4 TEXT NOT NULL,
            is_blocked BOOLEAN DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        -- Loyalty transactions: audit trail
        CREATE TABLE IF NOT EXISTS loyalty_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            kind TEXT NOT NULL CHECK(kind IN ('accrual','redeem','adjust')),
            delta_pts INTEGER NOT NULL,
            balance_after INTEGER NOT NULL,
            ref INT,
            note TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        -- Indexes
        CREATE INDEX IF NOT EXISTS idx_loy_spend_intents_user_status ON loy_spend_intents(user_id, status);
        CREATE INDEX IF NOT EXISTS idx_loy_spend_intents_expires ON loy_spend_intents(expires_at);
        CREATE INDEX IF NOT EXISTS idx_loy_tx_user_time ON loyalty_transactions(user_id, created_at);
        """
        self.apply_migration(
            "005",
            "EXPAND: Loyalty wallets, spend intents, user cards, transactions",
            sql,
        )
    
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
        version = "003"
        desc = "EXPAND: Seed default categories with backward compatibility"
        if self.is_migration_applied(version):
            logger.info(f"Migration {version} already applied, skipping")
            return

        def _apply(conn: sqlite3.Connection):
            # Check if we're using PostgreSQL (has pg_catalog) or SQLite
            is_postgres = False
            try:
                cursor = conn.execute("SELECT 1 FROM pg_catalog.pg_tables LIMIT 1")
                is_postgres = cursor.fetchone() is not None
            except (sqlite3.OperationalError, sqlite3.DatabaseError):
                pass  # Not PostgreSQL

            # Add missing columns if they don't exist
            if is_postgres:
                # PostgreSQL version
                conn.execute("""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='categories' AND column_name='name_ru'
                    ) THEN
                        ALTER TABLE categories ADD COLUMN name_ru TEXT;
                    END IF;
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='categories' AND column_name='name_en'
                    ) THEN
                        ALTER TABLE categories ADD COLUMN name_en TEXT;
                    END IF;
                END $$;
                """)
            else:
                # SQLite version
                cursor = conn.execute("PRAGMA table_info(categories)")
                columns = {row[1] for row in cursor.fetchall()}
                if 'name_ru' not in columns:
                    conn.execute("ALTER TABLE categories ADD COLUMN name_ru TEXT")
                if 'name_en' not in columns:
                    conn.execute("ALTER TABLE categories ADD COLUMN name_en TEXT")

            # Insert default categories if they don't exist
            conn.execute("""
            INSERT OR IGNORE INTO categories_v2 (slug, name, emoji, priority_level) VALUES
            ('restaurants', '🍜 Рестораны', '🍜', 100),
            ('spa', '🧘 SPA и массаж', '🧘', 90),
            ('transport', '🛵 Аренда байков', '🛵', 80),
            ('hotels', '🏨 Отели', '🏨', 70),
            ('tours', '🗺️ Экскурсии', '🗺️', 60);
            """)
            
            # Backward compatibility: sync with legacy categories
            # First try with all columns, if it fails, fallback to minimal columns
            try:
                conn.execute("""
                INSERT OR IGNORE INTO categories (id, name, name_ru, name_en, created_at)
                SELECT id, name, name, slug, datetime('now') FROM categories_v2;
                """)
            except sqlite3.OperationalError as e:
                logger.warning(f"Could not insert with all columns, falling back to minimal: {e}")
                conn.execute("""
                INSERT OR IGNORE INTO categories (id, name, name_ru, name_en)
                SELECT id, name, name, slug FROM categories_v2;
                """)

            # Record migration
            conn.execute(
                "INSERT INTO schema_migrations (version, description) VALUES (?, ?)",
                (version, desc),
            )

        if self._is_memory:
            conn = self.get_connection()
            try:
                _apply(conn)
                conn.commit()
                logger.info(f"Applied migration {version}: {desc}")
            except Exception as e:
                logger.error(f"Failed to apply migration {version}: {e}")
                raise
        else:
            with self.get_connection() as conn:
                try:
                    _apply(conn)
                    logger.info(f"Applied migration {version}: {desc}")
                except Exception as e:
                    logger.error(f"Failed to apply migration {version}: {e}")
                    raise

    def migrate_004_add_cards_optional_fields(self):
        """
        EXPAND Phase: Conditionally add optional fields to cards_v2:
        - subcategory_id INTEGER NULL
        - city_id INTEGER NULL
        - area_id INTEGER NULL

        Idempotent: checks existing columns before altering.
        """
        version = "004"
        desc = "EXPAND: Add optional subcategory_id, city_id, area_id to cards_v2"
        if self.is_migration_applied(version):
            logger.info(f"Migration {version} already applied, skipping")
            return
        def _apply(conn: sqlite3.Connection):
            cur = conn.execute("PRAGMA table_info(cards_v2)")
            have = {str(r[1]) for r in cur.fetchall()}
            to_add: list[tuple[str, str]] = []
            if "subcategory_id" not in have:
                to_add.append(("subcategory_id", "INTEGER"))
            if "city_id" not in have:
                to_add.append(("city_id", "INTEGER"))
            if "area_id" not in have:
                to_add.append(("area_id", "INTEGER"))
            for name, typ in to_add:
                conn.execute(f"ALTER TABLE cards_v2 ADD COLUMN {name} {typ}")
            # record migration
            conn.execute(
                "INSERT INTO schema_migrations (version, description) VALUES (?, ?)",
                (version, desc),
            )
        if self._is_memory:
            conn = self.get_connection()
            try:
                _apply(conn)
                conn.commit()
                logger.info(f"Applied migration {version}: {desc}")
            except Exception as e:
                logger.error(f"Failed to apply migration {version}: {e}")
                raise
        else:
            with self.get_connection() as conn:
                try:
                    _apply(conn)
                    logger.info(f"Applied migration {version}: {desc}")
                except Exception as e:
                    logger.error(f"Failed to apply migration {version}: {e}")
                    raise
    
    def run_all_migrations(self):
        """Run all pending migrations in order"""
        logger.info("Starting database migrations...")
        
        self.init_migration_table()
        self.migrate_001_expand_legacy_tables()
        # Ensure legacy categories.created_at exists for compatibility
        self.migrate_001_1_add_categories_created_at()
        self.migrate_002_expand_new_schema()
        self.migrate_003_seed_default_data()
        # Add optional fields to cards_v2 (subcategory_id, city_id, area_id)
        self.migrate_004_add_cards_optional_fields()
        # Loyalty subsystem (wallets, spend intents, cards, transactions)
        self.migrate_005_loyalty_tables()
        # Add name_ko column to categories table if it doesn't exist
        self.migrate_005_5_add_name_ko_column()
        # Seed additional categories
        self.migrate_006_seed_shops_services()
        # Bans table
        self.migrate_007_banned_users()
        # Card photos table for multi-photo support
        self.migrate_008_card_photos()
        # Karma system and plastic cards
        self.migrate_016_plastic_cards()
        
        logger.info("All migrations completed successfully")

    def migrate_001_1_add_categories_created_at(self):
        """
        EXPAND Phase: Ensure 'created_at' exists in legacy categories table
        """
        version = "001.1"
        desc = "EXPAND: Add created_at column to categories if missing"
        if self.is_migration_applied(version):
            logger.info(f"Migration {version} already applied, skipping")
            return
        def _apply(conn: sqlite3.Connection):
            # SQLite path: add column if missing
            try:
                cur = conn.execute("PRAGMA table_info(categories)")
                cols = {row[1] for row in cur.fetchall()}
                if 'created_at' not in cols:
                    # В SQLite запрещён неконстантный DEFAULT при ALTER TABLE.
                    # Добавляем без DEFAULT, затем заполняем существующие строки.
                    conn.execute("ALTER TABLE categories ADD COLUMN created_at TEXT")
                    conn.execute("UPDATE categories SET created_at = COALESCE(created_at, datetime('now'))")
                conn.execute(
                    "INSERT INTO schema_migrations (version, description) VALUES (?, ?)",
                    (version, desc),
                )
            except Exception as e:
                logger.error(f"Failed to apply {version}: {e}")
                raise
        if self._is_memory:
            conn = self.get_connection()
            _apply(conn)
            conn.commit()
            logger.info(f"Applied migration {version}: {desc}")
        else:
            with self.get_connection() as conn:
                _apply(conn)
                logger.info(f"Applied migration {version}: {desc}")

    def migrate_005_5_add_name_ko_column(self):
        """
        EXPAND Phase: Add name_ko column to categories table if it doesn't exist
        This is a compatibility migration to support Korean language in categories
        """
        with self.get_connection() as conn:
            # Check if column already exists
            if not _col_exists(conn, "categories", "name_ko"):
                conn.execute("""
                    ALTER TABLE categories 
                    ADD COLUMN name_ko TEXT DEFAULT ''
                """)
                conn.commit()
                
        self.apply_migration(
            "005.5",
            "EXPAND: Add name_ko column to categories table",
            """
            -- This migration is applied programmatically
            -- to ensure SQLite compatibility
            SELECT 1;
            """
        )

    def migrate_006_seed_shops_services(self):
        """
        EXPAND Phase: Seed additional category '🛍️ Магазины и услуги'
        Idempotent: uses INSERT OR IGNORE
        """
        # Ensure categories table exists with all required columns
        with self.get_connection() as conn:
            _ensure_table_categories(conn)
            # Ensure name_ko column exists
            if not _col_exists(conn, "categories", "name_ko"):
                conn.execute("ALTER TABLE categories ADD COLUMN name_ko TEXT DEFAULT ''")
                conn.commit()
            
        sql = """
        -- Insert into new categories_v2 table if it exists
        INSERT OR IGNORE INTO categories_v2 (slug, name, emoji, priority_level)
        VALUES ('shops', '🛍️ Магазины и услуги', '🛍️', 65);

        -- Backward compatibility: ensure legacy categories has this row
        INSERT OR IGNORE INTO categories (name_ru, name_en, name_ko, type)
        VALUES ('🛍️ Магазины и услуги', '🛍️ Shops & Services', '🛍️ 쇼핑 & 서비스', 'shops');
        """
        self.apply_migration(
            "006",
            "EXPAND: Seed category '🛍️ Магазины и услуги'",
            sql,
        )

    def migrate_007_banned_users(self):
        """
        EXPAND Phase: Banned users registry
        - banned_users: list of banned Telegram user IDs with reason and timestamps
        """
        sql = """
        CREATE TABLE IF NOT EXISTS banned_users (
            user_id INTEGER PRIMARY KEY,
            reason TEXT,
            banned_at TEXT DEFAULT CURRENT_TIMESTAMP,
            unbanned_at TEXT
        );
        """
        self.apply_migration(
            "007",
            "EXPAND: Create banned_users table",
            sql,
        )

    def migrate_008_card_photos(self):
        """
        EXPAND Phase: Create card_photos table to support multiple photos per card.
        - card_photos: id, card_id (FK -> cards_v2), file_id, position, created_at
        Indices on (card_id, position) for ordering.
        """
        sql = """
        CREATE TABLE IF NOT EXISTS card_photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            card_id INTEGER NOT NULL,
            file_id TEXT NOT NULL,
            position INTEGER NOT NULL DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (card_id) REFERENCES cards_v2(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_card_photos_card ON card_photos(card_id);
        CREATE INDEX IF NOT EXISTS idx_card_photos_card_pos ON card_photos(card_id, position);
        """
        self.apply_migration(
            "008",
            "EXPAND: Create card_photos table for multi-photo support",
            sql,
        )

    def migrate_016_plastic_cards(self):
        """
        EXPAND Phase: Create karma system and plastic cards tables.
        - users: Add karma_points column
        - karma_transactions: Track karma changes
        - cards_generated: Generated plastic cards
        - cards_binding: Card-to-user bindings
        - complaints: User complaints system
        - thanks: User thanks system
        - admin_logs: Admin action logs
        """
        # Create users table if it doesn't exist
        users_sql = """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id BIGINT UNIQUE NOT NULL,
            username VARCHAR(255),
            first_name VARCHAR(255),
            last_name VARCHAR(255),
            language_code VARCHAR(10) DEFAULT 'ru',
            karma_points INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        # Add karma_points column if it doesn't exist
        karma_column_sql = """
        ALTER TABLE users ADD COLUMN karma_points INTEGER DEFAULT 0;
        """
        
        # Karma transactions table
        karma_transactions_sql = """
        CREATE TABLE IF NOT EXISTS karma_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id BIGINT NOT NULL,
            amount INTEGER NOT NULL,
            reason TEXT,
            admin_id BIGINT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_karma_transactions_user_id 
        ON karma_transactions(user_id);
        """
        
        # Cards generated table
        cards_generated_sql = """
        CREATE TABLE IF NOT EXISTS cards_generated (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            card_id VARCHAR(20) UNIQUE NOT NULL,
            card_id_printable VARCHAR(20) NOT NULL,
            qr_url TEXT NOT NULL,
            created_by BIGINT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_blocked BOOLEAN DEFAULT FALSE,
            is_deleted BOOLEAN DEFAULT FALSE,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_cards_generated_card_id 
        ON cards_generated(card_id);
        """
        
        # Cards binding table
        cards_binding_sql = """
        CREATE TABLE IF NOT EXISTS cards_binding (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id BIGINT NOT NULL,
            card_id VARCHAR(20) NOT NULL UNIQUE,
            card_id_printable VARCHAR(50),
            qr_url TEXT,
            bound_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status VARCHAR(20) DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_cards_binding_telegram_id 
        ON cards_binding(telegram_id);
        
        CREATE INDEX IF NOT EXISTS idx_cards_binding_card_id 
        ON cards_binding(card_id);
        
        CREATE INDEX IF NOT EXISTS idx_cards_binding_status 
        ON cards_binding(status);
        """
        
        # Complaints table
        complaints_sql = """
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_user_id BIGINT NOT NULL,
            target_user_id BIGINT NOT NULL,
            reason TEXT NOT NULL,
            description TEXT,
            status VARCHAR(20) DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resolved_at TIMESTAMP,
            resolved_by BIGINT
        );
        
        CREATE INDEX IF NOT EXISTS idx_complaints_target_user_id 
        ON complaints(target_user_id);
        """
        
        # Thanks table
        thanks_sql = """
        CREATE TABLE IF NOT EXISTS thanks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_user_id BIGINT NOT NULL,
            target_user_id BIGINT NOT NULL,
            reason TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_thanks_target_user_id 
        ON thanks(target_user_id);
        """
        
        # Admin logs table
        admin_logs_sql = """
        CREATE TABLE IF NOT EXISTS admin_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id BIGINT NOT NULL,
            action VARCHAR(50) NOT NULL,
            target_id VARCHAR(50),
            reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_admin_logs_admin_id 
        ON admin_logs(admin_id);
        """
        
        # Apply all migrations
        self.apply_migration(
            "016",
            "EXPAND: Create karma system and plastic cards tables",
            users_sql,
        )
        
        # Try to add karma_points column (might fail if already exists)
        try:
            self.apply_migration(
                "016.1",
                "EXPAND: Add karma_points column to users",
                karma_column_sql,
            )
        except:
            pass  # Column might already exist
        
        self.apply_migration(
            "016.2",
            "EXPAND: Create karma_transactions table",
            karma_transactions_sql,
        )
        
        self.apply_migration(
            "016.3",
            "EXPAND: Create cards_generated table",
            cards_generated_sql,
        )
        
        self.apply_migration(
            "016.4",
            "EXPAND: Create cards_binding table",
            cards_binding_sql,
        )
        
        self.apply_migration(
            "016.5",
            "EXPAND: Create complaints table",
            complaints_sql,
        )
        
        self.apply_migration(
            "016.6",
            "EXPAND: Create thanks table",
            thanks_sql,
        )
        
        self.apply_migration(
            "016.7",
            "EXPAND: Create admin_logs table",
            admin_logs_sql,
        )

# Global migrator instance
migrator = DatabaseMigrator()

def ensure_database_ready():
    """Ensure database is migrated and ready to use"""
    # Only run migrations if APPLY_MIGRATIONS=1
    if os.getenv("APPLY_MIGRATIONS", "0") != "1":
        logger.info("Skipping database migrations (APPLY_MIGRATIONS != 1)")
        return
        
    try:
        logger.info("Running database migrations...")
        migrator.run_all_migrations()
    except Exception as e:
        logger.error(f"Failed to run migrations: {e}")
        if os.getenv("APP_ENV") != "production":
            raise
