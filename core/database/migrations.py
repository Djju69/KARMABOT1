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
    
    def _is_postgres(self) -> bool:
        """Check if we're using PostgreSQL"""
        if self._is_memory:
            return False
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("SELECT 1 FROM pg_catalog.pg_tables LIMIT 1")
                return True
        except:
            return False
    
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
                    # Check if we're using PostgreSQL
                    is_postgres = False
                    try:
                        cursor = conn.execute("SELECT 1 FROM pg_catalog.pg_tables LIMIT 1")
                        is_postgres = True
                    except:
                        pass
                    
                    if is_postgres:
                        # PostgreSQL migration
                        import asyncio
                        import asyncpg
                        from core.settings import get_settings
                        
                        async def run_postgres_migration():
                            settings = get_settings()
                            conn_pg = await asyncpg.connect(settings.database_url)
                            try:
                                # Split SQL into individual statements
                                statements = [stmt.strip() for stmt in sql.split(';') if stmt.strip()]
                                for statement in statements:
                                    if statement:
                                        await conn_pg.execute(statement)
                                
                                # Record migration
                                await conn_pg.execute(
                                    "INSERT INTO schema_migrations (version, description) VALUES ($1, $2)",
                                    version, description
                                )
                                logger.info(f"Applied migration {version}: {description}")
                            finally:
                                await conn_pg.close()
                        
                        # Run PostgreSQL migration
                        try:
                            loop = asyncio.get_event_loop()
                            loop.run_until_complete(run_postgres_migration())
                        except RuntimeError:
                            asyncio.run(run_postgres_migration())
                    else:
                        # SQLite migration
                        conn.executescript(sql)
                        
                        # Record migration
                        conn.execute(
                            "INSERT INTO schema_migrations (version, description) VALUES (?, ?)",
                            (version, description)
                        )
                        conn.commit()
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
        # Loyalty system and partner ecosystem
        self.migrate_017_loyalty_system()
        # Personal cabinets system
        self.migrate_018_personal_cabinets()
        # Fix users table - FORCE EXECUTE
        print("🔧 FORCE executing migration 019 for PostgreSQL...")
        self.migrate_019_fix_users_table()
        # Loyalty system expansion
        self.migrate_020_loyalty_expansion()
        
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
            id SERIAL PRIMARY KEY,
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
            id SERIAL PRIMARY KEY,
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
            id SERIAL PRIMARY KEY,
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
        
        # Cards binding table - PostgreSQL version
        cards_binding_sql_pg = """
        CREATE TABLE IF NOT EXISTS cards_binding (
            id BIGSERIAL PRIMARY KEY,
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
        
        # Cards binding table - SQLite version
        cards_binding_sql_sqlite = """
        CREATE TABLE IF NOT EXISTS cards_binding (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER NOT NULL,
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
            id SERIAL PRIMARY KEY,
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
            id SERIAL PRIMARY KEY,
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
            id SERIAL PRIMARY KEY,
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
        
        # Apply cards_binding migration with database-specific SQL
        if self._is_memory or not self._is_postgres():
            # SQLite version
            self.apply_migration(
                "016.4",
                "EXPAND: Create cards_binding table",
                cards_binding_sql_sqlite,
            )
        else:
            # PostgreSQL version
            self.apply_migration(
                "016.4",
                "EXPAND: Create cards_binding table",
                cards_binding_sql_pg,
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

    def migrate_017_loyalty_system(self):
        """
        EXPAND Phase: Create loyalty system and partner ecosystem tables.
        - Add points_balance to users table
        - Create points_history table
        - Create partner_places table (adapted from cards_v2)
        - Create partner_sales table
        - Create place_moderation_logs table
        - Create platform_loyalty_config table
        """
        # Import the migration function
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        
        try:
            from migrations.migration_017_loyalty_system import upgrade_017
            
            # For SQLite, we need to adapt the PostgreSQL-specific syntax
            if not self._is_memory:
                with self.get_connection() as conn:
                    # Check if we're using PostgreSQL
                    is_postgres = False
                    try:
                        cursor = conn.execute("SELECT 1 FROM pg_catalog.pg_tables LIMIT 1")
                        is_postgres = cursor.fetchone() is not None
                    except:
                        pass
                    
                    if is_postgres:
                        # Use PostgreSQL migration
                        import asyncpg
                        import os
                        database_url = os.getenv("DATABASE_URL")
                        if database_url:
                            import asyncio
                            async def run_migration():
                                pg_conn = await asyncpg.connect(database_url)
                                try:
                                    await upgrade_017(pg_conn)
                                finally:
                                    await pg_conn.close()
                            # Check if we're in an event loop
                            try:
                                loop = asyncio.get_running_loop()
                                # We're in an event loop, create a task
                                import concurrent.futures
                                with concurrent.futures.ThreadPoolExecutor() as executor:
                                    future = executor.submit(asyncio.run, run_migration())
                                    future.result()
                            except RuntimeError:
                                # No event loop running, safe to use asyncio.run
                                asyncio.run(run_migration())
                    else:
                        # SQLite adaptation
                        self._migrate_017_sqlite(conn)
                        
        except ImportError:
            # Fallback to SQLite-only migration
            if not self._is_memory:
                with self.get_connection() as conn:
                    self._migrate_017_sqlite(conn)
            else:
                conn = self.get_connection()
                self._migrate_017_sqlite(conn)
                conn.commit()
        
        self.apply_migration(
            "017",
            "EXPAND: Create loyalty system and partner ecosystem tables",
            "-- Migration applied programmatically",
        )

    def _migrate_017_sqlite(self, conn):
        """SQLite-specific migration for loyalty system"""
        # 1. Add points_balance and partner_id to users table
        try:
            conn.execute("ALTER TABLE users ADD COLUMN points_balance INTEGER DEFAULT 0")
        except:
            pass  # Column might already exist
            
        try:
            conn.execute("ALTER TABLE users ADD COLUMN partner_id INTEGER")
        except:
            pass  # Column might already exist
        
        # 2. Create points_history table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS points_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                change_amount INTEGER NOT NULL,
                reason TEXT,
                transaction_type TEXT DEFAULT 'earned',
                sale_id INTEGER,
                admin_id INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 3. Create partner_places table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS partner_places (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                partner_id INTEGER,
                title TEXT NOT NULL,
                status TEXT DEFAULT 'draft',
                address TEXT,
                geo_lat REAL,
                geo_lon REAL,
                hours TEXT,
                phone TEXT,
                website TEXT,
                price_level TEXT,
                rating REAL DEFAULT 0,
                reviews_count INTEGER DEFAULT 0,
                description TEXT,
                base_discount_pct REAL,
                loyalty_accrual_pct REAL DEFAULT 5.00,
                min_redeem INTEGER DEFAULT 0,
                max_percent_per_bill REAL DEFAULT 50.00,
                cover_file_id TEXT,
                gallery_file_ids TEXT DEFAULT '[]',
                categories TEXT DEFAULT '[]',
                referral_bonus_1_10 INTEGER DEFAULT 5,
                referral_bonus_11_20 INTEGER DEFAULT 7,
                referral_bonus_over_20 INTEGER DEFAULT 3,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                updated_by INTEGER
            )
        """)
        
        # 4. Create place_moderation_logs table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS place_moderation_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                place_id INTEGER,
                moderator_id INTEGER,
                action TEXT,
                old_status TEXT,
                new_status TEXT,
                reason TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 5. Create partner_sales table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS partner_sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                partner_id INTEGER,
                place_id INTEGER,
                operator_telegram_id INTEGER,
                user_telegram_id INTEGER,
                amount_gross REAL NOT NULL,
                base_discount_pct REAL NOT NULL,
                extra_discount_pct REAL DEFAULT 0.00,
                extra_value REAL DEFAULT 0.00,
                amount_partner_due REAL NOT NULL,
                amount_user_subsidy REAL NOT NULL,
                points_spent INTEGER DEFAULT 0,
                points_earned INTEGER DEFAULT 0,
                redeem_rate REAL NOT NULL,
                receipt TEXT,
                qr_token TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 6. Create platform_loyalty_config table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS platform_loyalty_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                redeem_rate REAL NOT NULL DEFAULT 5000.0,
                rounding_rule TEXT DEFAULT 'bankers',
                max_accrual_percent REAL DEFAULT 20.00,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_by INTEGER
            )
        """)
        
        # 7. Create indexes
        conn.execute("CREATE INDEX IF NOT EXISTS idx_points_history_user_id ON points_history(user_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_points_history_created_at ON points_history(created_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_partner_places_partner_id ON partner_places(partner_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_partner_places_status ON partner_places(status)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_partner_sales_partner_id ON partner_sales(partner_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_partner_sales_user_id ON partner_sales(user_telegram_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_partner_sales_created_at ON partner_sales(created_at)")
        
        # 8. Insert default loyalty config
        conn.execute("""
            INSERT OR IGNORE INTO platform_loyalty_config (redeem_rate, rounding_rule, max_accrual_percent)
            VALUES (5000.0, 'bankers', 20.00)
        """)

    def migrate_018_personal_cabinets(self):
        """
        EXPAND Phase: Create personal cabinets system tables.
        - Add missing fields to users table (role, reputation_score, level, ban fields, last_activity)
        - Create user_notifications table
        - Create user_achievements table
        - Update admin_logs table with additional fields
        - Update cards_generated table with additional fields
        """
        # Import the migration function
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        
        try:
            from migrations.migration_018_personal_cabinets import upgrade_018
            
            # For SQLite, we need to adapt the PostgreSQL-specific syntax
            if not self._is_memory:
                with self.get_connection() as conn:
                    # Check if we're using PostgreSQL
                    is_postgres = False
                    try:
                        cursor = conn.execute("SELECT 1 FROM pg_catalog.pg_tables LIMIT 1")
                        is_postgres = cursor.fetchone() is not None
                    except:
                        pass
                    
                    if is_postgres:
                        # Use PostgreSQL migration
                        import asyncpg
                        import os
                        database_url = os.getenv("DATABASE_URL")
                        if database_url:
                            import asyncio
                            async def run_migration():
                                pg_conn = await asyncpg.connect(database_url)
                                try:
                                    await upgrade_018(pg_conn)
                                finally:
                                    await pg_conn.close()
                            # Check if we're in an event loop
                            try:
                                loop = asyncio.get_running_loop()
                                # We're in an event loop, create a task
                                import concurrent.futures
                                with concurrent.futures.ThreadPoolExecutor() as executor:
                                    future = executor.submit(asyncio.run, run_migration())
                                    future.result()
                            except RuntimeError:
                                # No event loop running, safe to use asyncio.run
                                asyncio.run(run_migration())
                    else:
                        # SQLite adaptation
                        self._migrate_018_sqlite(conn)
                        
        except ImportError:
            # Fallback to SQLite-only migration
            if not self._is_memory:
                with self.get_connection() as conn:
                    self._migrate_018_sqlite(conn)
            else:
                conn = self.get_connection()
                self._migrate_018_sqlite(conn)
                conn.commit()
        
        self.apply_migration(
            "018",
            "EXPAND: Create personal cabinets system tables",
            "-- Migration applied programmatically",
        )

    def migrate_019_fix_users_table(self):
        """Migration 019: Fix users table creation"""
        try:
            database_url = os.getenv("DATABASE_URL")
            if database_url and database_url.startswith("postgresql"):
                # PostgreSQL migration - use existing event loop
                import asyncio
                import asyncpg
                
                async def run_migration():
                    conn = await asyncpg.connect(database_url)
                    try:
                        # Создаем таблицу users
                        await conn.execute("""
                            CREATE TABLE IF NOT EXISTS users (
                                id SERIAL PRIMARY KEY,
                                telegram_id BIGINT UNIQUE NOT NULL,
                                username VARCHAR(255),
                                first_name VARCHAR(255),
                                last_name VARCHAR(255),
                                language_code VARCHAR(10) DEFAULT 'ru',
                                karma_points INTEGER DEFAULT 0,
                                role VARCHAR(20) DEFAULT 'user',
                                reputation_score INTEGER DEFAULT 0,
                                level INTEGER DEFAULT 1,
                                is_banned BOOLEAN DEFAULT FALSE,
                                ban_reason TEXT,
                                banned_by BIGINT,
                                banned_at TIMESTAMP,
                                last_activity TIMESTAMP DEFAULT NOW(),
                                created_at TIMESTAMP DEFAULT NOW(),
                                updated_at TIMESTAMP DEFAULT NOW()
                            )
                        """)
                        print("✅ Users table created/verified")
                        
                        # Создаем таблицу user_notifications
                        await conn.execute("""
                            CREATE TABLE IF NOT EXISTS user_notifications (
                                id SERIAL PRIMARY KEY,
                                user_id BIGINT NOT NULL,
                                message TEXT NOT NULL,
                                is_read BOOLEAN DEFAULT FALSE,
                                notification_type VARCHAR(50),
                                created_at TIMESTAMP DEFAULT NOW()
                            )
                        """)
                        print("✅ user_notifications table created/verified")
                        
                        # Создаем таблицу user_achievements
                        await conn.execute("""
                            CREATE TABLE IF NOT EXISTS user_achievements (
                                id SERIAL PRIMARY KEY,
                                user_id BIGINT NOT NULL,
                                achievement_type VARCHAR(50) NOT NULL,
                                achievement_data TEXT,
                                earned_at TIMESTAMP DEFAULT NOW()
                            )
                        """)
                        print("✅ user_achievements table created/verified")
                        
                        # Проверяем, что таблица users существует
                        result = await conn.fetchval("SELECT COUNT(*) FROM users")
                        print(f"✅ Users table contains {result} records")
                        
                        print("✅ PostgreSQL migration 019 completed successfully")
                    finally:
                        await conn.close()
                
                # Check if we're in an event loop
                try:
                    loop = asyncio.get_running_loop()
                    # We're in an event loop, create a task
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, run_migration())
                        future.result()
                except RuntimeError:
                    # No event loop running, safe to use asyncio.run
                    asyncio.run(run_migration())
            else:
                # SQLite migration
                if not self._is_memory:
                    with self.get_connection() as conn:
                        self._migrate_019_sqlite(conn)
                else:
                    conn = self.get_connection()
                    self._migrate_019_sqlite(conn)
                    conn.commit()
                    
        except ImportError:
            # Fallback to SQLite-only migration
            if not self._is_memory:
                with self.get_connection() as conn:
                    self._migrate_019_sqlite(conn)
            else:
                conn = self.get_connection()
                self._migrate_019_sqlite(conn)
                conn.commit()
        
        self.apply_migration(
            "019",
            "FIX: Force create users table if missing",
            "-- Migration applied programmatically",
        )

    def _migrate_018_sqlite(self, conn):
        """SQLite-specific migration for personal cabinets system"""
        # 0. Create users table if it doesn't exist
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                language_code TEXT DEFAULT 'ru',
                karma_points INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 1. Add missing fields to users table
        fields_to_add = [
            ("role", "TEXT DEFAULT 'user'"),
            ("reputation_score", "INTEGER DEFAULT 0"),
            ("level", "INTEGER DEFAULT 1"),
            ("is_banned", "BOOLEAN DEFAULT 0"),
            ("ban_reason", "TEXT"),
            ("banned_by", "INTEGER"),
            ("banned_at", "TEXT"),
            ("last_activity", "TEXT")
        ]
        
        for field_name, field_type in fields_to_add:
            try:
                conn.execute(f"ALTER TABLE users ADD COLUMN {field_name} {field_type}")
            except:
                pass  # Column might already exist
        
        # 2. Create user_notifications table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                is_read BOOLEAN DEFAULT 0,
                notification_type TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 3. Create user_achievements table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                achievement_type TEXT,
                achievement_data TEXT,
                earned_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 4. Update admin_logs table with additional fields
        admin_logs_fields = [
            ("target_user_id", "INTEGER"),
            ("target_card_id", "TEXT"),
            ("details", "TEXT")
        ]
        
        for field_name, field_type in admin_logs_fields:
            try:
                conn.execute(f"ALTER TABLE admin_logs ADD COLUMN {field_name} {field_type}")
            except:
                pass  # Column might already exist
        
        # 5. Update cards_generated table with additional fields
        cards_generated_fields = [
            ("block_reason", "TEXT"),
            ("blocked_by", "INTEGER"),
            ("blocked_at", "TEXT")
        ]
        
        for field_name, field_type in cards_generated_fields:
            try:
                conn.execute(f"ALTER TABLE cards_generated ADD COLUMN {field_name} {field_type}")
            except:
                pass  # Column might already exist
        
        # 6. Create indexes for new tables
        conn.execute("CREATE INDEX IF NOT EXISTS idx_user_notifications_user_id ON user_notifications(user_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_user_notifications_type ON user_notifications(notification_type)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_user_notifications_is_read ON user_notifications(is_read)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_user_achievements_user_id ON user_achievements(user_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_user_achievements_type ON user_achievements(achievement_type)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_users_is_banned ON users(is_banned)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_users_level ON users(level)")

    def _migrate_019_sqlite(self, conn):
        """SQLite-specific migration for fixing users table"""
        try:
            print("🔧 Force creating users table (SQLite)...")
            
            # Проверяем, существует ли таблица users
            try:
                conn.execute("SELECT COUNT(*) FROM users LIMIT 1").fetchone()
                print("✅ Users table already exists")
            except:
                print("❌ Users table does not exist, creating...")
                
                # Создаем таблицу users
                conn.execute("""
                    CREATE TABLE users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        telegram_id INTEGER UNIQUE NOT NULL,
                        username TEXT,
                        first_name TEXT,
                        last_name TEXT,
                        language_code TEXT DEFAULT 'ru',
                        karma_points INTEGER DEFAULT 0,
                        role TEXT DEFAULT 'user',
                        reputation_score INTEGER DEFAULT 0,
                        level INTEGER DEFAULT 1,
                        is_banned BOOLEAN DEFAULT 0,
                        ban_reason TEXT,
                        banned_by INTEGER,
                        banned_at TEXT,
                        last_activity TEXT DEFAULT CURRENT_TIMESTAMP,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                print("✅ Users table created successfully")
            
            # Создаем таблицу user_notifications если её нет
            try:
                conn.execute("SELECT COUNT(*) FROM user_notifications LIMIT 1").fetchone()
                print("✅ user_notifications table already exists")
            except:
                print("❌ user_notifications table does not exist, creating...")
                conn.execute("""
                    CREATE TABLE user_notifications (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        message TEXT NOT NULL,
                        is_read BOOLEAN DEFAULT 0,
                        notification_type TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                print("✅ user_notifications table created successfully")
            
            # Создаем таблицу user_achievements если её нет
            try:
                conn.execute("SELECT COUNT(*) FROM user_achievements LIMIT 1").fetchone()
                print("✅ user_achievements table already exists")
            except:
                print("❌ user_achievements table does not exist, creating...")
                conn.execute("""
                    CREATE TABLE user_achievements (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        achievement_type TEXT NOT NULL,
                        achievement_data TEXT,
                        earned_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                print("✅ user_achievements table created successfully")
                
        except Exception as e:
            print(f"❌ Error in migration 019 (SQLite): {e}")
            raise

    def migrate_020_loyalty_expansion(self):
        """Migration 020: Expand users table and create loyalty system tables"""
        version = "020"
        desc = "EXPAND: Add loyalty system tables and expand users table"
        
        if self.is_migration_applied(version):
            logger.info(f"Migration {version} already applied, skipping")
            return
            
        try:
            database_url = os.getenv("DATABASE_URL")
            if database_url and database_url.startswith("postgresql"):
                # PostgreSQL migration
                self._migrate_020_postgresql()
            else:
                # SQLite migration
                if not self._is_memory:
                    with self.get_connection() as conn:
                        self._migrate_020_sqlite(conn)
                else:
                    conn = self.get_connection()
                    self._migrate_020_sqlite(conn)
                    conn.commit()
                    
        except Exception as e:
            logger.error(f"Error in migration {version}: {e}")
            raise
            
        self.apply_migration(
            version,
            desc,
            "-- Migration applied programmatically",
        )

    def _migrate_020_postgresql(self):
        """PostgreSQL-specific migration for loyalty system expansion"""
        try:
            import asyncio
            import asyncpg
            
            async def run_migration():
                database_url = os.getenv("DATABASE_URL")
                conn = await asyncpg.connect(database_url)
                
                try:
                    # Expand users table
                    await conn.execute("""
                        ALTER TABLE users 
                        ADD COLUMN IF NOT EXISTS points_balance INTEGER DEFAULT 0,
                        ADD COLUMN IF NOT EXISTS partner_id INTEGER;
                    """)
                    
                    # Create points_history table
                    await conn.execute("""
                        CREATE TABLE IF NOT EXISTS points_history (
                            id SERIAL PRIMARY KEY,
                            user_id BIGINT NOT NULL,
                            change_amount INTEGER NOT NULL,
                            reason VARCHAR(500),
                            transaction_type VARCHAR(20),
                            sale_id INTEGER,
                            admin_id BIGINT,
                            created_at TIMESTAMP DEFAULT NOW()
                        );
                    """)
                    
                    # Create partners table
                    await conn.execute("""
                        CREATE TABLE IF NOT EXISTS partners (
                            id SERIAL PRIMARY KEY,
                            code VARCHAR(50) UNIQUE NOT NULL,
                            title VARCHAR(255) NOT NULL,
                            status VARCHAR(20) DEFAULT 'pending',
                            base_discount_pct NUMERIC(5,2) DEFAULT 0,
                            contact_name VARCHAR(255),
                            contact_telegram BIGINT,
                            contact_phone VARCHAR(50),
                            contact_email VARCHAR(255),
                            legal_info TEXT,
                            created_at TIMESTAMP DEFAULT NOW(),
                            is_deleted BOOLEAN DEFAULT FALSE,
                            approved_by BIGINT,
                            approved_at TIMESTAMP
                        );
                    """)
                    
                    # Create partner_places table
                    await conn.execute("""
                        CREATE TABLE IF NOT EXISTS partner_places (
                            id SERIAL PRIMARY KEY,
                            partner_id INTEGER REFERENCES partners(id),
                            title VARCHAR(60) NOT NULL,
                            status VARCHAR(20) DEFAULT 'draft',
                            address VARCHAR(255),
                            geo_lat NUMERIC(10,6),
                            geo_lon NUMERIC(10,6),
                            hours VARCHAR(120),
                            phone VARCHAR(50),
                            website VARCHAR(255),
                            price_level VARCHAR(5),
                            rating NUMERIC(3,1) DEFAULT 0,
                            reviews_count INTEGER DEFAULT 0,
                            description TEXT,
                            base_discount_pct NUMERIC(5,2),
                            loyalty_accrual_pct NUMERIC(5,2) DEFAULT 5.00,
                            min_redeem INTEGER DEFAULT 0,
                            max_percent_per_bill NUMERIC(5,2) DEFAULT 50.00,
                            cover_file_id TEXT,
                            gallery_file_ids JSONB DEFAULT '[]',
                            categories JSONB DEFAULT '[]',
                            created_at TIMESTAMP DEFAULT NOW(),
                            created_by BIGINT
                        );
                    """)
                    
                    # Create partner_sales table
                    await conn.execute("""
                        CREATE TABLE IF NOT EXISTS partner_sales (
                            id SERIAL PRIMARY KEY,
                            partner_id INTEGER REFERENCES partners(id),
                            place_id INTEGER REFERENCES partner_places(id),
                            operator_telegram_id BIGINT,
                            user_telegram_id BIGINT,
                            amount_gross NUMERIC(12,2) NOT NULL,
                            base_discount_pct NUMERIC(5,2) NOT NULL,
                            extra_discount_pct NUMERIC(5,2) DEFAULT 0.00,
                            extra_value NUMERIC(12,2) DEFAULT 0.00,
                            amount_partner_due NUMERIC(12,2) NOT NULL,
                            amount_user_subsidy NUMERIC(12,2) DEFAULT 0.00,
                            points_spent INTEGER DEFAULT 0,
                            points_earned INTEGER DEFAULT 0,
                            redeem_rate NUMERIC(14,4) NOT NULL,
                            receipt VARCHAR(100),
                            qr_token VARCHAR(255),
                            created_at TIMESTAMP DEFAULT NOW()
                        );
                    """)
                    
                    # Create platform_loyalty_config table
                    await conn.execute("""
                        CREATE TABLE IF NOT EXISTS platform_loyalty_config (
                            id SERIAL PRIMARY KEY,
                            redeem_rate NUMERIC(14,4) DEFAULT 5000.0,
                            rounding_rule VARCHAR(20) DEFAULT 'bankers',
                            max_accrual_percent NUMERIC(5,2) DEFAULT 20.00,
                            max_percent_per_bill NUMERIC(5,2) DEFAULT 50.00,
                            min_purchase_for_points INTEGER DEFAULT 10000,
                            max_discount_percent NUMERIC(5,2) DEFAULT 40.00,
                            updated_at TIMESTAMP DEFAULT NOW(),
                            updated_by BIGINT
                        );
                    """)
                    
                    # Create payment_qr_tokens table
                    await conn.execute("""
                        CREATE TABLE IF NOT EXISTS payment_qr_tokens (
                            id SERIAL PRIMARY KEY,
                            token_hash VARCHAR(64) UNIQUE NOT NULL,
                            user_id BIGINT NOT NULL,
                            place_id INTEGER REFERENCES partner_places(id),
                            created_at TIMESTAMP DEFAULT NOW(),
                            expires_at TIMESTAMP NOT NULL,
                            is_used BOOLEAN DEFAULT FALSE,
                            used_at TIMESTAMP,
                            sale_id INTEGER
                        );
                    """)
                    
                    # Create pos_terminals table
                    await conn.execute("""
                        CREATE TABLE IF NOT EXISTS pos_terminals (
                            id SERIAL PRIMARY KEY,
                            partner_id INTEGER REFERENCES partners(id),
                            place_id INTEGER REFERENCES partner_places(id),
                            terminal_id VARCHAR(100) UNIQUE NOT NULL,
                            api_key VARCHAR(255) UNIQUE NOT NULL,
                            terminal_name VARCHAR(100),
                            status VARCHAR(20) DEFAULT 'active',
                            created_at TIMESTAMP DEFAULT NOW(),
                            last_used_at TIMESTAMP
                        );
                    """)
                    
                    # Create cards_binding table if missing
                    await conn.execute("""
                        CREATE TABLE IF NOT EXISTS cards_binding (
                            id BIGSERIAL PRIMARY KEY,
                            telegram_id BIGINT NOT NULL,
                            card_id VARCHAR(20) NOT NULL UNIQUE,
                            card_id_printable VARCHAR(50),
                            qr_url TEXT,
                            bound_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            status VARCHAR(20) DEFAULT 'active',
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );
                    """)
                    
                    # Create indexes for cards_binding
                    await conn.execute("""
                        CREATE INDEX IF NOT EXISTS idx_cards_binding_telegram_id 
                        ON cards_binding(telegram_id);
                    """)
                    await conn.execute("""
                        CREATE INDEX IF NOT EXISTS idx_cards_binding_card_id 
                        ON cards_binding(card_id);
                    """)
                    await conn.execute("""
                        CREATE INDEX IF NOT EXISTS idx_cards_binding_status 
                        ON cards_binding(status);
                    """)
                    
                    # Insert default loyalty config
                    await conn.execute("""
                        INSERT INTO platform_loyalty_config (redeem_rate, rounding_rule, max_accrual_percent, min_purchase_for_points, max_discount_percent, max_percent_per_bill)
                        VALUES (5000.0, 'bankers', 20.00, 10000, 40.00, 50.00)
                        ON CONFLICT DO NOTHING;
                    """)
                    
                    print("✅ PostgreSQL migration 020 completed successfully")
                    
                finally:
                    await conn.close()
            
            asyncio.run(run_migration())
            
        except ImportError:
            logger.warning("asyncpg not available, skipping PostgreSQL migration")
            raise

    def _migrate_020_sqlite(self, conn):
        """SQLite-specific migration for loyalty system expansion"""
        try:
            # Expand users table
            conn.execute("""
                ALTER TABLE users 
                ADD COLUMN points_balance INTEGER DEFAULT 0;
            """)
            conn.execute("""
                ALTER TABLE users 
                ADD COLUMN partner_id INTEGER;
            """)
            
            # Create points_history table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS points_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    change_amount INTEGER NOT NULL,
                    reason TEXT,
                    transaction_type TEXT,
                    sale_id INTEGER,
                    admin_id INTEGER,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Create partners table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS partners (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    base_discount_pct REAL DEFAULT 0,
                    contact_name TEXT,
                    contact_telegram INTEGER,
                    contact_phone TEXT,
                    contact_email TEXT,
                    legal_info TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    is_deleted BOOLEAN DEFAULT FALSE,
                    approved_by INTEGER,
                    approved_at TEXT
                );
            """)
            
            # Create partner_places table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS partner_places (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    partner_id INTEGER REFERENCES partners(id),
                    title TEXT NOT NULL,
                    status TEXT DEFAULT 'draft',
                    address TEXT,
                    geo_lat REAL,
                    geo_lon REAL,
                    hours TEXT,
                    phone TEXT,
                    website TEXT,
                    price_level TEXT,
                    rating REAL DEFAULT 0,
                    reviews_count INTEGER DEFAULT 0,
                    description TEXT,
                    base_discount_pct REAL,
                    loyalty_accrual_pct REAL DEFAULT 5.00,
                    min_redeem INTEGER DEFAULT 0,
                    max_percent_per_bill REAL DEFAULT 50.00,
                    cover_file_id TEXT,
                    gallery_file_ids TEXT DEFAULT '[]',
                    categories TEXT DEFAULT '[]',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER
                );
            """)
            
            # Create partner_sales table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS partner_sales (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    partner_id INTEGER REFERENCES partners(id),
                    place_id INTEGER REFERENCES partner_places(id),
                    operator_telegram_id INTEGER,
                    user_telegram_id INTEGER,
                    amount_gross REAL NOT NULL,
                    base_discount_pct REAL NOT NULL,
                    extra_discount_pct REAL DEFAULT 0.00,
                    extra_value REAL DEFAULT 0.00,
                    amount_partner_due REAL NOT NULL,
                    amount_user_subsidy REAL DEFAULT 0.00,
                    points_spent INTEGER DEFAULT 0,
                    points_earned INTEGER DEFAULT 0,
                    redeem_rate REAL NOT NULL,
                    receipt TEXT,
                    qr_token TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Create platform_loyalty_config table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS platform_loyalty_config (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    redeem_rate REAL DEFAULT 5000.0,
                    rounding_rule TEXT DEFAULT 'bankers',
                    max_accrual_percent REAL DEFAULT 20.00,
                    max_percent_per_bill REAL DEFAULT 50.00,
                    min_purchase_for_points INTEGER DEFAULT 10000,
                    max_discount_percent REAL DEFAULT 40.00,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_by INTEGER
                );
            """)
            
            # Create payment_qr_tokens table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS payment_qr_tokens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    token_hash TEXT UNIQUE NOT NULL,
                    user_id INTEGER NOT NULL,
                    place_id INTEGER REFERENCES partner_places(id),
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    expires_at TEXT NOT NULL,
                    is_used BOOLEAN DEFAULT FALSE,
                    used_at TEXT,
                    sale_id INTEGER
                );
            """)
            
            # Create pos_terminals table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS pos_terminals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    partner_id INTEGER REFERENCES partners(id),
                    place_id INTEGER REFERENCES partner_places(id),
                    terminal_id TEXT UNIQUE NOT NULL,
                    api_key TEXT UNIQUE NOT NULL,
                    terminal_name TEXT,
                    status TEXT DEFAULT 'active',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    last_used_at TEXT
                );
            """)
            
            # Insert default loyalty config
            conn.execute("""
                INSERT OR IGNORE INTO platform_loyalty_config (redeem_rate, rounding_rule, max_accrual_percent, max_percent_per_bill, min_purchase_for_points, max_discount_percent)
                VALUES (5000.0, 'bankers', 20.00, 50.00, 10000, 40.00);
            """)
            
            print("✅ SQLite migration 020 completed successfully")
            
        except Exception as e:
            print(f"❌ Error in migration 020 (SQLite): {e}")
            raise

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
