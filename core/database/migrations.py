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
    
    def mark_migration_applied(self, version: str, description: str):
        """Mark migration as applied"""
        if self._is_memory:
            conn = self.get_connection()
            cursor = conn.execute(
                "INSERT OR REPLACE INTO schema_migrations (version, description, applied_at) VALUES (?, ?, datetime('now'))",
                (version, description)
            )
            conn.commit()
        else:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    "INSERT OR REPLACE INTO schema_migrations (version, description, applied_at) VALUES (?, ?, datetime('now'))",
                    (version, description)
                )
                conn.commit()
    
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
        
        -- Partner applications table
        CREATE TABLE IF NOT EXISTS partner_applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_user_id INTEGER UNIQUE NOT NULL,
            telegram_username TEXT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT NOT NULL,
            business_description TEXT,
            status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'approved', 'rejected')),
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            reviewed_at TEXT,
            reviewed_by INTEGER
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
                    -- Ensure legacy categories table has required columns
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='categories' AND column_name='name'
                    ) THEN
                        ALTER TABLE categories ADD COLUMN name TEXT;
                    END IF;
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
                # Ensure categories table and required columns exist
                try:
                    cur0 = conn.execute("PRAGMA table_info(categories)")
                    cols0 = {row[1] for row in cur0.fetchall()}
                except sqlite3.OperationalError:
                    cols0 = set()
                if 'name' not in cols0:
                    conn.execute("ALTER TABLE categories ADD COLUMN name TEXT")
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
        """Run all pending migrations in order (guarded, idempotent)"""
        logger.info("Starting database migrations...")
        # Prevent concurrent/racey runs on Postgres via advisory lock
        advisory_locked = False
        if not self._is_memory and self._is_postgres():
            try:
                import asyncio, asyncpg, os
                database_url = os.getenv("DATABASE_URL")
                async def _lock():
                    conn_pg = await asyncpg.connect(database_url)
                    try:
                        # Arbitrary big int lock key for this app
                        await conn_pg.execute("SELECT pg_advisory_lock(8612345678901234)")
                        return conn_pg
                    except Exception:
                        await conn_pg.close()
                        raise
                try:
                    loop = asyncio.get_running_loop()
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as ex:
                        fut = ex.submit(asyncio.run, _lock())
                        self._pg_lock_conn = fut.result()
                except RuntimeError:
                    self._pg_lock_conn = asyncio.run(_lock())
                advisory_locked = True
                logger.info("🔒 Acquired PG advisory lock for migrations")
            except Exception as e:
                logger.warning(f"⚠️ Could not acquire advisory lock: {e}")
        
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
        # Fix users table - execute only if not applied; avoid noisy FORCE
        if not self.is_migration_applied("019"):
            logger.info("🔧 Executing migration 019 (users table fix)")
            self.migrate_019_fix_users_table()
        # Loyalty system expansion
        self.migrate_020_loyalty_expansion()
        # Create partners_v2 table for PostgreSQL
        self.migrate_021_create_partners_v2()
        # User features (favorites, referrals, karma_log, points_log, achievements)
        self.migrate_010_user_features()
        # Add loyalty columns to users table
        self.migrate_022_add_loyalty_columns()
        # User roles and 2FA system
        self.migrate_024_user_roles_2fa()
        # Card photos table
        self.migrate_025_card_photos()
        
        # 021: Extend qr_codes_v2 for user-scoped QR operations used by db_v2 helpers
        try:
            version = "021"
            desc = "EXPAND: Add user-scoped fields to qr_codes_v2"
            if not self.is_migration_applied(version):
                if self._is_memory or not self._is_postgres():
                    with self.get_connection() as conn:
                        cur = conn.execute("PRAGMA table_info(qr_codes_v2)")
                        cols = {row[1] for row in cur.fetchall()}
                        to_add: list[str] = []
                        if 'user_id' not in cols: to_add.append("ALTER TABLE qr_codes_v2 ADD COLUMN user_id INTEGER")
                        if 'qr_id' not in cols: to_add.append("ALTER TABLE qr_codes_v2 ADD COLUMN qr_id TEXT")
                        if 'name' not in cols: to_add.append("ALTER TABLE qr_codes_v2 ADD COLUMN name TEXT")
                        if 'discount' not in cols: to_add.append("ALTER TABLE qr_codes_v2 ADD COLUMN discount INTEGER DEFAULT 0")
                        if 'is_active' not in cols: to_add.append("ALTER TABLE qr_codes_v2 ADD COLUMN is_active INTEGER DEFAULT 1")
                        if 'created_at' not in cols: to_add.append("ALTER TABLE qr_codes_v2 ADD COLUMN created_at TEXT DEFAULT CURRENT_TIMESTAMP")
                        if 'expires_at' not in cols: to_add.append("ALTER TABLE qr_codes_v2 ADD COLUMN expires_at TEXT")
                        for stmt in to_add:
                            conn.execute(stmt)
                        conn.execute("CREATE INDEX IF NOT EXISTS idx_qr_codes_v2_user ON qr_codes_v2(user_id)")
                        conn.execute(
                            "INSERT INTO schema_migrations (version, description) VALUES (?, ?)",
                            (version, desc),
                        )
                else:
                    sql = """
                    ALTER TABLE qr_codes_v2 ADD COLUMN IF NOT EXISTS user_id BIGINT;
                    ALTER TABLE qr_codes_v2 ADD COLUMN IF NOT EXISTS qr_id VARCHAR(255);
                    ALTER TABLE qr_codes_v2 ADD COLUMN IF NOT EXISTS name VARCHAR(255);
                    ALTER TABLE qr_codes_v2 ADD COLUMN IF NOT EXISTS discount INTEGER DEFAULT 0;
                    ALTER TABLE qr_codes_v2 ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
                    ALTER TABLE qr_codes_v2 ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW();
                    ALTER TABLE qr_codes_v2 ADD COLUMN IF NOT EXISTS expires_at TIMESTAMPTZ;
                    CREATE INDEX IF NOT EXISTS idx_qr_codes_v2_user ON qr_codes_v2(user_id);
                    """
                    self.apply_migration(version, desc, sql)
        except Exception as e:
            logger.warning(f"021 migration skipped or failed safely: {e}")
        
        # 022: Ensure users.policy_accepted column exists (PG/SQLite)
        try:
            version = "022"
            desc = "EXPAND: Add users.policy_accepted column (privacy policy flag)"
            if not self.is_migration_applied(version):
                if self._is_memory or not self._is_postgres():
                    # SQLite path: add column if missing
                    with self.get_connection() as conn:
                        try:
                            cur = conn.execute("PRAGMA table_info(users)")
                            cols = {row[1] for row in cur.fetchall()}
                        except Exception:
                            cols = set()
                        if 'policy_accepted' not in cols:
                            conn.execute("ALTER TABLE users ADD COLUMN policy_accepted INTEGER DEFAULT 0")
                        conn.execute(
                            "INSERT INTO schema_migrations (version, description) VALUES (?, ?)",
                            (version, desc),
                        )
                        conn.commit()
                else:
                    # PostgreSQL path: use IF NOT EXISTS
                    sql = """
                    ALTER TABLE users ADD COLUMN IF NOT EXISTS policy_accepted BOOLEAN DEFAULT FALSE;
                    """
                    self.apply_migration(version, desc, sql)
        except Exception as e:
            logger.warning(f"022 migration skipped or failed safely: {e}")
        
        logger.info("All migrations completed successfully")
        # Release advisory lock
        if advisory_locked:
            try:
                import asyncio
                async def _unlock(conn_pg):
                    try:
                        await conn_pg.execute("SELECT pg_advisory_unlock(8612345678901234)")
                    finally:
                        await conn_pg.close()
                try:
                    loop = asyncio.get_running_loop()
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as ex:
                        fut = ex.submit(asyncio.run, _unlock(self._pg_lock_conn))
                        fut.result()
                except RuntimeError:
                    asyncio.run(_unlock(self._pg_lock_conn))
                logger.info("🔓 Released PG advisory lock for migrations")
            except Exception as e:
                logger.warning(f"⚠️ Could not release advisory lock: {e}")
        # 023: Add odoo_card_id to cards_v2 for mapping
        try:
            version = "023"
            desc = "EXPAND: Add odoo_card_id column to cards_v2 for Odoo mapping"
            if not self.is_migration_applied(version):
                if self._is_memory or not self._is_postgres():
                    with self.get_connection() as conn:
                        cur = conn.execute("PRAGMA table_info(cards_v2)")
                        cols = {row[1] for row in cur.fetchall()}
                        if 'odoo_card_id' not in cols:
                            conn.execute("ALTER TABLE cards_v2 ADD COLUMN odoo_card_id INTEGER")
                        conn.execute(
                            "INSERT INTO schema_migrations (version, description) VALUES (?, ?)",
                            (version, desc),
                        )
                        conn.commit()
                else:
                    sql = """
                    ALTER TABLE cards_v2 ADD COLUMN IF NOT EXISTS odoo_card_id BIGINT;
                    """
                    self.apply_migration(version, desc, sql)
        except Exception as e:
            logger.warning(f"023 migration skipped or failed safely: {e}")

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
        # Create users table if it doesn't exist (PostgreSQL version)
        # Users table creation removed - handled by migration 020
        
        # Add karma_points column if it doesn't exist
        # We'll do a pre-check to avoid noisy duplicate-column errors in logs
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
        if self._is_memory or not self._is_postgres():
            # Users table creation removed - handled by migration 020
            self.apply_migration(
                "016",
                "EXPAND: Create karma system and plastic cards tables (SQLite)",
                "-- Users table creation skipped",
            )
        else:
            # Users table creation removed - handled by migration 020
            self.apply_migration(
                "016",
                "EXPAND: Create karma system and plastic cards tables (PG)",
                "-- Users table creation skipped",
            )
        
        # Try to add karma_points column safely: pre-check and mark applied if exists
        try:
            column_exists = False
            if self._is_memory or not self._is_postgres():
                # SQLite path
                try:
                    with self.get_connection() as _conn_chk:
                        # First check if users table exists
                        cur = _conn_chk.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
                        if not cur.fetchone():
                            logger.info("Users table doesn't exist, skipping migration 016.1")
                            return
                        
                        cur = _conn_chk.execute("PRAGMA table_info(users)")
                        cols = {row[1] for row in cur.fetchall()}
                        column_exists = 'karma_points' in cols
                except Exception:
                    column_exists = False
            else:
                # PostgreSQL path
                try:
                    import asyncio, asyncpg, os
                    database_url = os.getenv("DATABASE_URL")
                    async def _check_pg():
                        conn_pg = await asyncpg.connect(database_url)
                        try:
                            # First check if users table exists
                            table_exists = await conn_pg.fetchval(
                                "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='users')"
                            )
                            if not table_exists:
                                logger.info("Users table doesn't exist, skipping migration 016.1")
                                return False
                            
                            return await conn_pg.fetchval(
                                "SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='karma_points')"
                            )
                        finally:
                            await conn_pg.close()
                    try:
                        loop = asyncio.get_running_loop()
                        import concurrent.futures
                        with concurrent.futures.ThreadPoolExecutor() as ex:
                            fut = ex.submit(asyncio.run, _check_pg())
                            column_exists = bool(fut.result())
                    except RuntimeError:
                        column_exists = bool(asyncio.run(_check_pg()))
                except Exception:
                    column_exists = False

            if column_exists:
                # Mark as applied with a no-op to avoid re-attempts
                self.apply_migration(
                    "016.1",
                    "EXPAND: Add karma_points column to users (skipped: exists)",
                    "SELECT 1;",
                )
            else:
                self.apply_migration(
                    "016.1",
                    "EXPAND: Add karma_points column to users",
                    karma_column_sql,
                )
        except Exception:
            # Do not spam logs on safe-check failures
            pass
        
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
            # Migration 017 disabled - external import causes issues
            # from migrations.migration_017_loyalty_system import upgrade_017
            upgrade_017 = None
            
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
                                    # await upgrade_017(pg_conn)  # Migration 017 disabled
                                    print("Migration 017 skipped - external import disabled")
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
        
        # Migration 020 only creates basic tables
        # Advanced loyalty config will be handled in migration 021

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
            # Migration 018 disabled - external import causes issues
            # from migrations.migration_018_personal_cabinets import upgrade_018
            upgrade_018 = None
            
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
                                    # await upgrade_018(pg_conn)  # Migration 018 disabled
                                    print("Migration 018 skipped - external import disabled")
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
                        # Users table creation removed - handled by migration 020
                        print("✅ Users table creation skipped - handled by migration 020")
                        
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
        # Users table creation removed - handled by migration 020
        
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
            
            # Users table creation removed - handled by migration 020
            print("✅ Users table creation skipped - handled by migration 020")
            
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
                    # Create users table if it doesn't exist
                    await conn.execute("""
                        CREATE TABLE IF NOT EXISTS users (
                            id SERIAL PRIMARY KEY,
                            user_id BIGINT UNIQUE NOT NULL,
                            username VARCHAR(255),
                            first_name VARCHAR(255),
                            last_name VARCHAR(255),
                            language_code VARCHAR(5) DEFAULT 'ru',
                            phone VARCHAR(20),
                            email VARCHAR(255),
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            is_active BOOLEAN DEFAULT TRUE,
                            is_partner BOOLEAN DEFAULT FALSE,
                            is_admin BOOLEAN DEFAULT FALSE,
                            is_super_admin BOOLEAN DEFAULT FALSE
                        );
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
                    
                    # Migration 020 only creates basic tables
                    # Advanced loyalty config will be handled in migration 021
                    
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
                    
                    # Create tariffs table
                    await conn.execute("""
                        CREATE TABLE IF NOT EXISTS tariffs (
                            id SERIAL PRIMARY KEY,
                            name VARCHAR(100) NOT NULL,
                            tariff_type VARCHAR(50) NOT NULL,
                            monthly_price_vnd INTEGER DEFAULT 0,
                            commission_percent DECIMAL(5,2) DEFAULT 0.00,
                            transaction_limit INTEGER,
                            features TEXT DEFAULT '[]',
                            is_active BOOLEAN DEFAULT TRUE,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );
                    """)
                    
                    # Create partner_tariffs table
                    await conn.execute("""
                        CREATE TABLE IF NOT EXISTS partner_tariffs (
                            id SERIAL PRIMARY KEY,
                            partner_id BIGINT NOT NULL,
                            tariff_id INTEGER NOT NULL,
                            status VARCHAR(20) DEFAULT 'active',
                            start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            end_date TIMESTAMP,
                            auto_renew BOOLEAN DEFAULT TRUE,
                            payment_method VARCHAR(50),
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (tariff_id) REFERENCES tariffs(id)
                        );
                    """)
                    
                    # Create tariff_usage table
                    await conn.execute("""
                        CREATE TABLE IF NOT EXISTS tariff_usage (
                            id SERIAL PRIMARY KEY,
                            partner_id BIGINT NOT NULL,
                            tariff_id INTEGER NOT NULL,
                            month INTEGER NOT NULL,
                            year INTEGER NOT NULL,
                            transactions_count INTEGER DEFAULT 0,
                            transactions_limit INTEGER,
                            commission_earned DECIMAL(10,2) DEFAULT 0.00,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            UNIQUE(partner_id, tariff_id, month, year)
                        );
                    """)
                    
                    # Insert default tariffs
                    await conn.execute("""
                        INSERT INTO tariffs (id, name, tariff_type, monthly_price_vnd, commission_percent, transaction_limit, features)
                        VALUES 
                            (1, 'FREE STARTER', 'free_starter', 0, 12.00, 15, '["Базовые карты лояльности", "QR-коды для скидок", "Простая аналитика", "Email поддержка"]'),
                            (2, 'BUSINESS', 'business', 490000, 6.00, 100, '["Расширенные карты лояльности", "QR-коды с кастомизацией", "Детальная аналитика", "Приоритетная поддержка", "API доступ (ограниченный)", "Интеграция с CRM"]'),
                            (3, 'ENTERPRISE', 'enterprise', 960000, 4.00, NULL, '["Полный функционал карт", "Кастомные QR-коды", "Продвинутая аналитика", "Выделенный менеджер", "Полный API доступ", "Кастомные интеграции", "Белый лейбл", "Приоритетная разработка"]')
                        ON CONFLICT (id) DO NOTHING;
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
                    
                    # Migration 020 only creates basic tables
                    # Advanced loyalty config will be handled in migration 021
                    
                    print("✅ PostgreSQL migration 020 completed successfully")
                    
                finally:
                    await conn.close()
            
            # Check if we're in an event loop
            try:
                loop = asyncio.get_running_loop()
                # We're in an event loop, use ThreadPoolExecutor
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, run_migration())
                    future.result()
            except RuntimeError:
                # No event loop running, safe to use asyncio.run
                asyncio.run(run_migration())
            
        except ImportError:
            logger.warning("asyncpg not available, skipping PostgreSQL migration")
            raise

    def _migrate_020_sqlite(self, conn):
        """SQLite-specific migration for loyalty system expansion"""
        try:
            # First, create users table if it doesn't exist
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id BIGINT UNIQUE NOT NULL,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    language_code TEXT DEFAULT 'ru',
                    is_bot BOOLEAN DEFAULT FALSE,
                    is_premium BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Migration 020 only creates the basic users table
            # Loyalty columns will be added in migration 022
            
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
                    bonus_for_points_usage REAL DEFAULT 0.30,
                    welcome_bonus_immediate INTEGER DEFAULT 51,
                    welcome_unlock_stage_1 INTEGER DEFAULT 67,
                    welcome_unlock_stage_2 INTEGER DEFAULT 50,
                    welcome_unlock_stage_3 INTEGER DEFAULT 50,
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
            
            # Create tariffs table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tariffs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    tariff_type TEXT NOT NULL,
                    monthly_price_vnd INTEGER DEFAULT 0,
                    commission_percent REAL DEFAULT 0.00,
                    transaction_limit INTEGER,
                    features TEXT DEFAULT '[]',
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Create partner_tariffs table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS partner_tariffs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    partner_id INTEGER NOT NULL,
                    tariff_id INTEGER NOT NULL,
                    status TEXT DEFAULT 'active',
                    start_date TEXT DEFAULT CURRENT_TIMESTAMP,
                    end_date TEXT,
                    auto_renew INTEGER DEFAULT 1,
                    payment_method TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (tariff_id) REFERENCES tariffs(id)
                );
            """)
            
            # Create tariff_usage table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tariff_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    partner_id INTEGER NOT NULL,
                    tariff_id INTEGER NOT NULL,
                    month INTEGER NOT NULL,
                    year INTEGER NOT NULL,
                    transactions_count INTEGER DEFAULT 0,
                    transactions_limit INTEGER,
                    commission_earned REAL DEFAULT 0.00,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(partner_id, tariff_id, month, year)
                );
            """)
            
            # Insert default tariffs
            conn.execute("""
                INSERT OR IGNORE INTO tariffs (id, name, tariff_type, monthly_price_vnd, commission_percent, transaction_limit, features)
                VALUES 
                    (1, 'FREE STARTER', 'free_starter', 0, 12.00, 15, '["Базовые карты лояльности", "QR-коды для скидок", "Простая аналитика", "Email поддержка"]'),
                    (2, 'BUSINESS', 'business', 490000, 6.00, 100, '["Расширенные карты лояльности", "QR-коды с кастомизацией", "Детальная аналитика", "Приоритетная поддержка", "API доступ (ограниченный)", "Интеграция с CRM"]'),
                    (3, 'ENTERPRISE', 'enterprise', 960000, 4.00, NULL, '["Полный функционал карт", "Кастомные QR-коды", "Продвинутая аналитика", "Выделенный менеджер", "Полный API доступ", "Кастомные интеграции", "Белый лейбл", "Приоритетная разработка"]');
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
            
            # Migration 020 only creates basic tables
            # Advanced loyalty config will be handled in migration 021
            
            print("✅ SQLite migration 020 completed successfully")
            
        except Exception as e:
            print(f"❌ Error in migration 020 (SQLite): {e}")
            raise

    def migrate_021_create_partners_v2(self):
        """Migration 021: Create partners_v2 table for PostgreSQL"""
        version = "021"
        desc = "CREATE: Create partners_v2, categories_v2, cards_v2 tables"
        
        if self.is_migration_applied(version):
            logger.info(f"Migration {version} already applied, skipping")
            return
            
        try:
            database_url = os.getenv('DATABASE_URL', '')
            
            if database_url and database_url.startswith("postgresql"):
                # PostgreSQL migration
                self._migrate_021_postgresql()
            else:
                # SQLite migration
                self._migrate_021_sqlite()
                
            self.mark_migration_applied(version, desc)
            logger.info(f"Applied migration {version}: {desc}")
            
        except Exception as e:
            logger.error(f"Error in migration {version}: {e}")
            raise

    def _migrate_021_postgresql(self):
        """PostgreSQL-specific migration for partners_v2 table"""
        try:
            # Use synchronous connection instead of asyncio.run()
            import psycopg2
            from core.settings import settings
            
            conn = psycopg2.connect(settings.database_url)
            cur = conn.cursor()
            
            # Create partners_v2 table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS partners_v2 (
                    id SERIAL PRIMARY KEY,
                    tg_user_id BIGINT UNIQUE NOT NULL,
                    display_name VARCHAR(255),
                    phone VARCHAR(20),
                    email VARCHAR(255),
                    is_verified BOOLEAN DEFAULT FALSE,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Create partner_applications table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS partner_applications (
                    id SERIAL PRIMARY KEY,
                    telegram_user_id BIGINT UNIQUE NOT NULL,
                    telegram_username VARCHAR(255),
                    name VARCHAR(255) NOT NULL,
                    phone VARCHAR(20) NOT NULL,
                    email VARCHAR(255) NOT NULL,
                    business_description TEXT,
                    status VARCHAR(20) DEFAULT 'pending' CHECK(status IN ('pending', 'approved', 'rejected')),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    reviewed_at TIMESTAMP,
                    reviewed_by BIGINT
                );
            """)
            
            # Create categories_v2 table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS categories_v2 (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    icon VARCHAR(50),
                    is_active BOOLEAN DEFAULT TRUE,
                    sort_order INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Create cards_v2 table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS cards_v2 (
                    id SERIAL PRIMARY KEY,
                    partner_id INTEGER NOT NULL,
                    category_id INTEGER NOT NULL,
                    title VARCHAR(255) NOT NULL,
                    description TEXT,
                    discount_percent INTEGER DEFAULT 0,
                    min_purchase_amount DECIMAL(10,2) DEFAULT 0,
                    max_discount_amount DECIMAL(10,2),
                    valid_from DATE,
                    valid_until DATE,
                    is_active BOOLEAN DEFAULT TRUE,
                    priority_level INTEGER DEFAULT 0,
                    view_count INTEGER DEFAULT 0,
                    is_featured BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (partner_id) REFERENCES partners_v2(id) ON DELETE CASCADE,
                            FOREIGN KEY (category_id) REFERENCES categories_v2(id) ON DELETE RESTRICT
                        );
                    """)
            
            # Create platform_loyalty_config table if it doesn't exist
            cur.execute("""
                CREATE TABLE IF NOT EXISTS platform_loyalty_config (
                    id SERIAL PRIMARY KEY,
                    redeem_rate NUMERIC(14,4) DEFAULT 5000.0,
                    rounding_rule VARCHAR(20) DEFAULT 'bankers',
                    max_accrual_percent NUMERIC(5,2) DEFAULT 20.00,
                    max_percent_per_bill NUMERIC(5,2) DEFAULT 50.00,
                    min_purchase_for_points INTEGER DEFAULT 10000,
                    max_discount_percent NUMERIC(5,2) DEFAULT 40.00,
                    bonus_for_points_usage NUMERIC(5,2) DEFAULT 0.30,
                    welcome_bonus_immediate INTEGER DEFAULT 51,
                    welcome_unlock_stage_1 INTEGER DEFAULT 67,
                    welcome_unlock_stage_2 INTEGER DEFAULT 50,
                    welcome_unlock_stage_3 INTEGER DEFAULT 50,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Insert default loyalty config
            cur.execute("""
                INSERT INTO platform_loyalty_config (redeem_rate, rounding_rule, max_accrual_percent, max_percent_per_bill, min_purchase_for_points, max_discount_percent, bonus_for_points_usage, welcome_bonus_immediate, welcome_unlock_stage_1, welcome_unlock_stage_2, welcome_unlock_stage_3)
                VALUES (5000.0, 'bankers', 20.00, 50.00, 10000, 40.00, 0.30, 51, 67, 50, 50)
                ON CONFLICT DO NOTHING;
            """)
            
            conn.commit()
            cur.close()
            conn.close()
            print("✅ Migration 021 completed - partners_v2, categories_v2, cards_v2, platform_loyalty_config tables created")
            
        except Exception as e:
            logger.error(f"Error in PostgreSQL migration 021: {e}")
            raise

    def _migrate_021_sqlite(self):
        """SQLite-specific migration for partners_v2 table"""
        try:
            conn = self.get_connection()
            
            # Create partners_v2 table
            conn.execute("""
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
            """)
            
            # Create categories_v2 table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS categories_v2 (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    icon TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    sort_order INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Create cards_v2 table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cards_v2 (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    partner_id INTEGER NOT NULL,
                    category_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    discount_percent INTEGER DEFAULT 0,
                    min_purchase_amount REAL DEFAULT 0,
                    max_discount_amount REAL,
                    valid_from TEXT,
                    valid_until TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    priority_level INTEGER DEFAULT 0,
                    view_count INTEGER DEFAULT 0,
                    is_featured BOOLEAN DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (partner_id) REFERENCES partners_v2(id) ON DELETE CASCADE,
                    FOREIGN KEY (category_id) REFERENCES categories_v2(id) ON DELETE RESTRICT
                );
            """)
            
            # Create platform_loyalty_config table if it doesn't exist
            conn.execute("""
                CREATE TABLE IF NOT EXISTS platform_loyalty_config (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    redeem_rate REAL DEFAULT 5000.0,
                    rounding_rule TEXT DEFAULT 'bankers',
                    max_accrual_percent REAL DEFAULT 20.00,
                    max_percent_per_bill REAL DEFAULT 50.00,
                    min_purchase_for_points INTEGER DEFAULT 10000,
                    max_discount_percent REAL DEFAULT 40.00,
                    bonus_for_points_usage REAL DEFAULT 0.30,
                    welcome_bonus_immediate INTEGER DEFAULT 51,
                    welcome_unlock_stage_1 INTEGER DEFAULT 67,
                    welcome_unlock_stage_2 INTEGER DEFAULT 50,
                    welcome_unlock_stage_3 INTEGER DEFAULT 50,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Insert default loyalty config
            conn.execute("""
                INSERT OR IGNORE INTO platform_loyalty_config (redeem_rate, rounding_rule, max_accrual_percent, max_percent_per_bill, min_purchase_for_points, max_discount_percent, bonus_for_points_usage, welcome_bonus_immediate, welcome_unlock_stage_1, welcome_unlock_stage_2, welcome_unlock_stage_3)
                VALUES (5000.0, 'bankers', 20.00, 50.00, 10000, 40.00, 0.30, 51, 67, 50, 50);
            """)
            
            conn.commit()
            print("✅ Migration 021 completed (SQLite) - partners_v2, categories_v2, cards_v2, platform_loyalty_config tables created")
            
        except Exception as e:
            logger.error(f"Error in SQLite migration 021: {e}")
            raise

    def migrate_022_add_loyalty_columns(self):
        """Migration 022: Add loyalty columns to users table AND create partner_applications table"""
        version = "022"
        desc = "ADD: Add loyalty columns to users table and create partner_applications table"
        
        if self.is_migration_applied(version):
            logger.info(f"Migration {version} already applied, skipping")
            return
            
        try:
            database_url = os.getenv('DATABASE_URL', '')
            
            if database_url and database_url.startswith("postgresql"):
                # PostgreSQL migration
                self._migrate_022_postgresql()
            else:
                # SQLite migration
                self._migrate_022_sqlite()
                
            self.mark_migration_applied(version, desc)
            logger.info(f"Applied migration {version}: {desc}")
            
        except Exception as e:
            logger.error(f"Error in migration {version}: {e}")
            raise

    def _migrate_022_postgresql(self):
        """PostgreSQL-specific migration for adding loyalty columns"""
        try:
            import asyncio
            import asyncpg
            
            async def run_migration():
                database_url = os.getenv("DATABASE_URL")
                conn = await asyncpg.connect(database_url)
                
                try:
                    # Add loyalty columns to users table
                    await conn.execute("""
                        ALTER TABLE users 
                        ADD COLUMN IF NOT EXISTS points_balance INTEGER DEFAULT 0,
                        ADD COLUMN IF NOT EXISTS partner_id INTEGER,
                        ADD COLUMN IF NOT EXISTS welcome_stage INTEGER DEFAULT 0,
                        ADD COLUMN IF NOT EXISTS language VARCHAR(5) DEFAULT 'ru';
                    """)
                    
                    # Create partner_applications table
                    await conn.execute("""
                        CREATE TABLE IF NOT EXISTS partner_applications (
                            id SERIAL PRIMARY KEY,
                            telegram_user_id BIGINT NOT NULL,
                            telegram_username TEXT,
                            name TEXT NOT NULL,
                            phone TEXT NOT NULL,
                            email TEXT NOT NULL,
                            business_description TEXT NOT NULL,
                            status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
                            created_at TIMESTAMPTZ DEFAULT NOW(),
                            reviewed_at TIMESTAMPTZ,
                            reviewed_by INTEGER
                        );
                    """)
                    
                    print("✅ Migration 022 completed (PostgreSQL) - loyalty columns and partner_applications table created")
                finally:
                    await conn.close()
            
            asyncio.run(run_migration())
            
        except Exception as e:
            logger.error(f"Error in PostgreSQL migration 022: {e}")
            raise

    def _migrate_022_sqlite(self):
        """SQLite-specific migration for adding loyalty columns"""
        try:
            conn = self.get_connection()
            
            # Add loyalty columns to users table
            conn.execute("""
                ALTER TABLE users 
                ADD COLUMN points_balance INTEGER DEFAULT 0;
            """)
            
            conn.execute("""
                ALTER TABLE users 
                ADD COLUMN partner_id INTEGER;
            """)
            
            conn.execute("""
                ALTER TABLE users 
                ADD COLUMN welcome_stage INTEGER DEFAULT 0;
            """)
            
            conn.execute("""
                ALTER TABLE users 
                ADD COLUMN language TEXT DEFAULT 'ru';
            """)
            
            # Create partner_applications table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS partner_applications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_user_id BIGINT NOT NULL,
                    telegram_username TEXT,
                    name TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    email TEXT NOT NULL,
                    business_description TEXT NOT NULL,
                    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    reviewed_at TIMESTAMP,
                    reviewed_by INTEGER
                );
            """)
            
            conn.commit()
            print("✅ Migration 022 completed (SQLite) - loyalty columns and partner_applications table created")
            
        except Exception as e:
            logger.error(f"Error in SQLite migration 022: {e}")
            raise

    def migrate_023_user_roles_2fa(self):
        """Migration 023: Add policy_accepted column to users table"""
        try:
            conn = self.get_connection()
            
            # Check if we're using SQLite or PostgreSQL
            is_postgres = hasattr(conn, 'execute') and callable(getattr(conn, 'execute'))
            
            if is_postgres:
                # PostgreSQL approach
                conn.execute("""
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM information_schema.columns 
                            WHERE table_name = 'users' AND column_name = 'policy_accepted'
                        ) THEN
                            ALTER TABLE users ADD COLUMN policy_accepted BOOLEAN DEFAULT FALSE;
                        END IF;
                    END
                    $$;
                """)
            else:
                # SQLite approach
                cursor = conn.cursor()
                if not _col_exists(conn, "users", "policy_accepted"):
                    cursor.execute("ALTER TABLE users ADD COLUMN policy_accepted BOOLEAN DEFAULT 0;")
            
            conn.commit()
            logger.info("Applied migration 022: Added policy_accepted column to users table")
            
        except Exception as e:
            logger.error(f"Failed to apply migration 022: {e}")
            raise
            
    def migrate_010_user_features(self):
        """Migration 010: User features tables"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Избранные заведения
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS favorites (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_telegram_id INTEGER NOT NULL,
                    place_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (place_id) REFERENCES partner_places(id)
                )
            """)
            
            # Реферальная система
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS referrals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    inviter_id INTEGER NOT NULL,
                    invited_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(invited_id)
                )
            """)
            
            # История кармы
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS karma_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_telegram_id INTEGER NOT NULL,
                    points_change INTEGER NOT NULL,
                    reason TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # История баллов
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS points_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_telegram_id INTEGER NOT NULL,
                    points_earned INTEGER DEFAULT 0,
                    points_spent INTEGER DEFAULT 0,
                    reason TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Достижения пользователей
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS achievements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_telegram_id INTEGER NOT NULL,
                    achievement_type TEXT NOT NULL,
                    achievement_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            logger.info("Applied migration 010: User features tables")
            
        except Exception as e:
            logger.error(f"Failed to apply migration 010: {e}")
            raise

    def migrate_024_user_roles_2fa(self):
        """Create user_roles, two_factor_auth, and audit_log tables"""
        version = "024"
        description = "EXPAND: Create user roles, 2FA, and audit log tables"
        
        if self.is_migration_applied(version):
            logger.info(f"Migration {version} already applied, skipping")
            return
        
        try:
            if self._is_memory or not self._is_postgres():
                # SQLite version
                with self.get_connection() as conn:
                    # Create user_roles table
                    conn.execute("""
                        CREATE TABLE IF NOT EXISTS user_roles (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id INTEGER NOT NULL UNIQUE,
                            role TEXT NOT NULL DEFAULT 'USER',
                            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                            CHECK (role IN ('USER', 'PARTNER', 'MODERATOR', 'ADMIN', 'SUPER_ADMIN'))
                        )
                    """)
                    
                    # Create two_factor_auth table
                    conn.execute("""
                        CREATE TABLE IF NOT EXISTS two_factor_auth (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id INTEGER NOT NULL UNIQUE,
                            secret_key TEXT NOT NULL,
                            is_enabled BOOLEAN DEFAULT 0,
                            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    
                    # Create audit_log table
                    conn.execute("""
                        CREATE TABLE IF NOT EXISTS audit_log (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id INTEGER,
                            action TEXT NOT NULL,
                            entity_type TEXT,
                            entity_id INTEGER,
                            old_values TEXT,
                            new_values TEXT,
                            ip_address TEXT,
                            user_agent TEXT,
                            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    
                    # Create indexes
                    conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON audit_log(user_id)")
                    conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON audit_log(created_at)")
                    conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_log_action ON audit_log(action)")
                    
                    # Insert initial admin role (только если пользователь существует)
                    from core.settings import settings
                    if hasattr(settings, 'bots') and hasattr(settings.bots, 'admin_id'):
                        admin_id = settings.bots.admin_id
                        # Проверяем что пользователь существует
                        cursor = conn.execute("SELECT 1 FROM users WHERE id = ?", (admin_id,))
                        if cursor.fetchone():
                            conn.execute("""
                                INSERT OR IGNORE INTO user_roles (user_id, role)
                                VALUES (?, 'SUPER_ADMIN')
                            """, (admin_id,))
                    
                    conn.commit()
            else:
                # PostgreSQL version
                with self.get_connection() as conn:
                    # Create user_roles table
                    conn.execute("""
                        CREATE TABLE IF NOT EXISTS user_roles (
                            id SERIAL PRIMARY KEY,
                            user_id BIGINT NOT NULL UNIQUE,
                            role VARCHAR(20) NOT NULL DEFAULT 'USER',
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                            CONSTRAINT chk_role CHECK (role IN ('USER', 'PARTNER', 'MODERATOR', 'ADMIN', 'SUPER_ADMIN'))
                        )
                    """)
                    
                    # Create two_factor_auth table
                    conn.execute("""
                        CREATE TABLE IF NOT EXISTS two_factor_auth (
                            id SERIAL PRIMARY KEY,
                            user_id BIGINT NOT NULL UNIQUE,
                            secret_key VARCHAR(50) NOT NULL,
                            is_enabled BOOLEAN DEFAULT FALSE,
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                        )
                    """)
                    
                    # Create audit_log table
                    conn.execute("""
                        CREATE TABLE IF NOT EXISTS audit_log (
                            id BIGSERIAL PRIMARY KEY,
                            user_id BIGINT,
                            action VARCHAR(100) NOT NULL,
                            entity_type VARCHAR(50),
                            entity_id BIGINT,
                            old_values JSONB,
                            new_values JSONB,
                            ip_address INET,
                            user_agent TEXT,
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                        )
                    """)
                    
                    # Create indexes
                    conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON audit_log(user_id)")
                    conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON audit_log(created_at)")
                    conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_log_action ON audit_log(action)")
                    
                    # Add comments
                    conn.execute("COMMENT ON TABLE user_roles IS 'Роли пользователей в системе'")
                    conn.execute("COMMENT ON TABLE two_factor_auth IS 'Настройки двухфакторной аутентификации'")
                    conn.execute("COMMENT ON TABLE audit_log IS 'Журнал аудита действий пользователей'")
                    
                    # Insert initial admin role (только если пользователь существует)
                    from core.settings import settings
                    if hasattr(settings, 'bots') and hasattr(settings.bots, 'admin_id'):
                        admin_id = settings.bots.admin_id
                        # Проверяем что пользователь существует
                        user_exists = conn.fetchval("SELECT 1 FROM users WHERE id = $1", admin_id)
                        if user_exists:
                            conn.execute("""
                                INSERT INTO user_roles (user_id, role)
                                VALUES ($1, 'SUPER_ADMIN')
                                ON CONFLICT (user_id) DO NOTHING
                            """, admin_id)
                    
                    conn.commit()
            
            self.apply_migration(version, description, "")
            logger.info(f"Applied migration {version}: {description}")
            
        except Exception as e:
            logger.error(f"Failed to apply migration {version}: {e}")
            raise

    def migrate_025_card_photos(self):
        """Create card_photos table for card images"""
        version = "025"
        description = "CREATE: Create card_photos table"
        
        if self.is_migration_applied(version):
            logger.info(f"Migration {version} already applied, skipping")
            return
        
        try:
            if self._is_memory or not self._is_postgres():
                # SQLite version
                with self.get_connection() as conn:
                    conn.execute("""
                        CREATE TABLE IF NOT EXISTS card_photos (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            card_id INTEGER NOT NULL,
                            photo_url TEXT NOT NULL,
                            photo_file_id TEXT,
                            caption TEXT,
                            is_main BOOLEAN DEFAULT FALSE,
                            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (card_id) REFERENCES cards_v2(id) ON DELETE CASCADE
                        )
                    """)
                    
                    # Create indexes
                    conn.execute("CREATE INDEX IF NOT EXISTS idx_card_photos_card_id ON card_photos(card_id)")
                    # Проверяем существование колонки перед созданием индекса
                    try:
                        conn.execute("CREATE INDEX IF NOT EXISTS idx_card_photos_is_main ON card_photos(is_main)")
                    except Exception as e:
                        logger.warning(f"Could not create index on is_main column: {e}")
                    
                    conn.commit()
            else:
                # PostgreSQL version
                with self.get_connection() as conn:
                    conn.execute("""
                        CREATE TABLE IF NOT EXISTS card_photos (
                            id SERIAL PRIMARY KEY,
                            card_id INTEGER NOT NULL,
                            photo_url TEXT NOT NULL,
                            photo_file_id TEXT,
                            caption TEXT,
                            is_main BOOLEAN DEFAULT FALSE,
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                            FOREIGN KEY (card_id) REFERENCES cards_v2(id) ON DELETE CASCADE
                        )
                    """)
                    
                    # Create indexes
                    conn.execute("CREATE INDEX IF NOT EXISTS idx_card_photos_card_id ON card_photos(card_id)")
                    # Проверяем существование колонки перед созданием индекса
                    try:
                        conn.execute("CREATE INDEX IF NOT EXISTS idx_card_photos_is_main ON card_photos(is_main)")
                    except Exception as e:
                        logger.warning(f"Could not create index on is_main column: {e}")
                    
                    # Add comments
                    conn.execute("COMMENT ON TABLE card_photos IS 'Фотографии карточек партнеров'")
                    conn.execute("COMMENT ON COLUMN card_photos.card_id IS 'ID карточки'")
                    conn.execute("COMMENT ON COLUMN card_photos.photo_url IS 'URL фотографии'")
                    conn.execute("COMMENT ON COLUMN card_photos.photo_file_id IS 'Telegram file_id фотографии'")
                    conn.execute("COMMENT ON COLUMN card_photos.is_main IS 'Главная фотография карточки'")
                    
                    conn.commit()
            
            self.apply_migration(version, description, "")
            logger.info(f"Applied migration {version}: {description}")
            
        except Exception as e:
            logger.error(f"Failed to apply migration {version}: {e}")
            raise

# Global migrator instance - use PostgreSQL in production
import os
db_path = os.getenv("DATABASE_URL", "core/database/data.db")
if db_path.startswith("postgresql://"):
    # Skip SQLite migrations in production with PostgreSQL
    db_path = None
migrator = DatabaseMigrator(db_path) if db_path else None

def ensure_partner_applications_table():
    """Ensure partner_applications table exists"""
    try:
        database_url = os.getenv('DATABASE_URL', '')
        
        if database_url and database_url.startswith("postgresql"):
            # PostgreSQL - use synchronous connection
            import psycopg2
            
            conn = psycopg2.connect(database_url)
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS partner_applications (
                    id SERIAL PRIMARY KEY,
                    telegram_user_id BIGINT NOT NULL,
                    telegram_username TEXT,
                    name TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    email TEXT NOT NULL,
                    business_description TEXT NOT NULL,
                    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    reviewed_at TIMESTAMPTZ,
                    reviewed_by INTEGER
                );
            """)
            conn.commit()
            cur.close()
            conn.close()
            logger.info("✅ partner_applications table created/verified in PostgreSQL")
        else:
            # SQLite
            if migrator:
                with migrator.get_connection() as conn:
                    conn.execute("""
                        CREATE TABLE IF NOT EXISTS partner_applications (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            telegram_user_id INTEGER NOT NULL,
                            telegram_username TEXT,
                            name TEXT NOT NULL,
                            phone TEXT NOT NULL,
                            email TEXT NOT NULL,
                            business_description TEXT NOT NULL,
                            status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
                            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                            reviewed_at DATETIME,
                            reviewed_by INTEGER
                        );
                    """)
                    conn.commit()
                    logger.info("✅ partner_applications table created/verified in SQLite")
                
    except Exception as e:
        logger.error(f"Error creating partner_applications table: {e}")

def ensure_user_roles_table():
    """Ensure user_roles table exists in both PostgreSQL and SQLite"""
    try:
        import os
        database_url = os.getenv("DATABASE_URL", "").lower()
        
        if database_url.startswith("postgres"):
            # PostgreSQL
            from core.settings import settings
            import psycopg2
            
            conn = psycopg2.connect(settings.database.url)
            cur = conn.cursor()
            try:
                # Create user_roles table if it doesn't exist
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS user_roles (
                        id SERIAL PRIMARY KEY,
                        user_id BIGINT NOT NULL UNIQUE,
                        role VARCHAR(20) NOT NULL DEFAULT 'USER',
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        CONSTRAINT chk_role CHECK (role IN ('USER', 'PARTNER', 'MODERATOR', 'ADMIN', 'SUPER_ADMIN'))
                    )
                """)
                
                # Insert super-admin role if it doesn't exist
                admin_id = getattr(settings.bots, 'admin_id', 6391215556)
                cur.execute("""
                    INSERT INTO user_roles (user_id, role) 
                    VALUES (%s, 'SUPER_ADMIN') 
                    ON CONFLICT (user_id) DO NOTHING
                """, (admin_id,))
                
                conn.commit()
                logger.info("✅ user_roles table created/verified in PostgreSQL")
                
            finally:
                cur.close()
                conn.close()
        else:
            # SQLite
            from core.database.db_v2 import db_v2
            conn = db_v2.get_connection()
            try:
                # Create user_roles table if it doesn't exist
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS user_roles (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL UNIQUE,
                        role TEXT NOT NULL DEFAULT 'USER',
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        CHECK (role IN ('USER', 'PARTNER', 'MODERATOR', 'ADMIN', 'SUPER_ADMIN'))
                    )
                """)
                
                # Insert super-admin role if it doesn't exist
                from core.settings import settings
                admin_id = getattr(settings.bots, 'admin_id', 6391215556)
                conn.execute("""
                    INSERT OR IGNORE INTO user_roles (user_id, role) 
                    VALUES (?, 'SUPER_ADMIN')
                """, (admin_id,))
                
                conn.commit()
                logger.info("✅ user_roles table created/verified in SQLite")
                
            finally:
                conn.close()
            
    except Exception as e:
        logger.error(f"Error creating user_roles table: {e}")

def ensure_partners_v2_columns():
    """Ensure partners_v2 table has all required columns"""
    try:
        from core.settings import settings
        import psycopg2
        
        # Connect to PostgreSQL
        conn = psycopg2.connect(settings.database.url)
        cur = conn.cursor()
        try:
            # Check if partners_v2 table exists
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'partners_v2'
                );
            """)
            
            table_exists = cur.fetchone()[0]
            
            if table_exists:
                # Check if is_verified column exists
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.columns 
                        WHERE table_schema = 'public' 
                        AND table_name = 'partners_v2' 
                        AND column_name = 'is_verified'
                    );
                """)
                
                column_exists = cur.fetchone()[0]
                
                if not column_exists:
                    # Add is_verified column
                    cur.execute("""
                        ALTER TABLE partners_v2 
                        ADD COLUMN is_verified BOOLEAN DEFAULT FALSE;
                    """)
                    logger.info("✅ Added is_verified column to partners_v2 table")
                else:
                    logger.info("✅ is_verified column already exists in partners_v2 table")
                
                # Check if is_active column exists
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.columns 
                        WHERE table_schema = 'public' 
                        AND table_name = 'partners_v2' 
                        AND column_name = 'is_active'
                    );
                """)
                
                is_active_exists = cur.fetchone()[0]
                
                if not is_active_exists:
                    # Add is_active column
                    cur.execute("""
                        ALTER TABLE partners_v2 
                        ADD COLUMN is_active BOOLEAN DEFAULT TRUE;
                    """)
                    logger.info("✅ Added is_active column to partners_v2 table")
                else:
                    logger.info("✅ is_active column already exists in partners_v2 table")
            else:
                logger.warning("⚠️ partners_v2 table does not exist")
            
            conn.commit()
            
        finally:
            cur.close()
            conn.close()
            
    except Exception as e:
        logger.error(f"Error ensuring partners_v2 columns: {e}")

def ensure_database_ready():
    """Ensure database is migrated and ready to use"""
    # Run migrations by default, skip only if explicitly disabled
    if os.getenv("SKIP_MIGRATIONS", "0") == "1":
        logger.info("Skipping database migrations (SKIP_MIGRATIONS=1)")
        return
    
    # Skip SQLite migrations if using PostgreSQL
    if migrator is None:
        logger.info("Skipping SQLite migrations (using PostgreSQL)")
        # Still ensure required tables exist
        ensure_partner_applications_table()
        ensure_user_roles_table()
        ensure_partners_v2_columns()
        ensure_cards_v2_table()
        ensure_card_photos_table()
        # Fix invalid photo file_ids
        fix_invalid_photo_file_ids()
        # Setup Supabase RLS if configured
        setup_supabase_rls()
        # Add sample data if needed
        add_sample_cards()
        # Create favorites table
        ensure_favorites_table()
        return
        
    try:
        logger.info("Running database migrations...")
        migrator.run_all_migrations()
        
        # Ensure partner_applications table exists
        ensure_partner_applications_table()
        
    except Exception as e:
        logger.error(f"Failed to run migrations: {e}")
        if os.getenv("APP_ENV") != "production":
            raise

def ensure_cards_v2_table():
    """Ensure cards_v2 table exists"""
    try:
        database_url = os.getenv('DATABASE_URL', '')
        
        if database_url and database_url.startswith("postgresql"):
            # PostgreSQL - use synchronous connection
            import psycopg2
            
            conn = psycopg2.connect(database_url)
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS cards_v2 (
                    id SERIAL PRIMARY KEY,
                    partner_id INTEGER NOT NULL,
                    category_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    address TEXT,
                    phone TEXT,
                    website TEXT,
                    email TEXT,
                    latitude REAL,
                    longitude REAL,
                    status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'pending', 'published', 'rejected', 'archived')),
                    subcategory_id INTEGER,
                    city_id INTEGER,
                    area_id INTEGER,
                    odoo_card_id BIGINT,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                );
            """)
            
            # Create indexes
            cur.execute("CREATE INDEX IF NOT EXISTS idx_cards_v2_status ON cards_v2(status)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_cards_v2_category ON cards_v2(category_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_cards_v2_partner ON cards_v2(partner_id)")
            
            conn.commit()
            cur.close()
            conn.close()
            logger.info("✅ cards_v2 table created/verified in PostgreSQL")
        else:
            # SQLite fallback
            import sqlite3
            db_path = os.getenv('DATABASE_PATH', 'core/database/data.db')
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS cards_v2 (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    partner_id INTEGER NOT NULL,
                    category_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    address TEXT,
                    phone TEXT,
                    website TEXT,
                    email TEXT,
                    latitude REAL,
                    longitude REAL,
                    status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'pending', 'published', 'rejected', 'archived')),
                    subcategory_id INTEGER,
                    city_id INTEGER,
                    area_id INTEGER,
                    odoo_card_id INTEGER,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Create indexes
            cur.execute("CREATE INDEX IF NOT EXISTS idx_cards_v2_status ON cards_v2(status)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_cards_v2_category ON cards_v2(category_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_cards_v2_partner ON cards_v2(partner_id)")
            
            conn.commit()
            cur.close()
            conn.close()
            logger.info("✅ cards_v2 table created/verified in SQLite")
            
    except Exception as e:
        logger.error(f"Error creating cards_v2 table: {e}")

def setup_supabase_rls():
    """Setup Row Level Security for Supabase tables"""
    try:
        from core.settings import settings
        
        # Only setup if Supabase is configured
        if not settings.supabase_url or not settings.supabase_key:
            logger.info("Supabase not configured, skipping RLS setup")
            return
            
        from supabase import create_client
        
        supabase = create_client(settings.supabase_url, settings.supabase_key)
        
        # Tables that need RLS
        tables = ['partners_v2', 'cards_v2', 'categories_v2']
        
        for table in tables:
            try:
                # Enable RLS
                supabase.rpc('exec_sql', {
                    'sql': f'ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;'
                }).execute()
                
                # Create policy
                supabase.rpc('exec_sql', {
                    'sql': f'CREATE POLICY IF NOT EXISTS "Allow anonymous access" ON {table} FOR ALL USING (true);'
                }).execute()
                
                logger.info(f"✅ RLS enabled for {table}")
                
            except Exception as e:
                logger.warning(f"Could not enable RLS for {table}: {e}")
                
        logger.info("✅ Supabase RLS setup completed")
        
    except ImportError:
        logger.warning("supabase-py not available, skipping RLS setup")
    except Exception as e:
        logger.error(f"Error setting up Supabase RLS: {e}")

def ensure_favorites_table():
    """Create favorites table for storing user favorites"""
    try:
        database_url = os.getenv('DATABASE_URL', '')
        
        if database_url and database_url.startswith("postgresql"):
            import psycopg2
            
            conn = psycopg2.connect(database_url)
            cur = conn.cursor()
            
            # Create favorites table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS user_favorites (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    card_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, card_id)
                )
            """)
            
            conn.commit()
            cur.close()
            conn.close()
            logger.info("✅ user_favorites table created/verified")
            
        else:
            logger.info("Using SQLite, skipping favorites table creation")
            
    except Exception as e:
        logger.error(f"Error creating favorites table: {e}")

def unify_database_structure():
    """Унификация структуры PostgreSQL с SQLite согласно ТЗ"""
    try:
        database_url = os.getenv('DATABASE_URL', '')
        
        if database_url and database_url.startswith("postgresql"):
            import psycopg2
            
            conn = psycopg2.connect(database_url)
            cur = conn.cursor()
            
            logger.info("🔧 Начинаю унификацию структуры PostgreSQL с SQLite...")
            
            # 1. Добавляем недостающую колонку position в card_photos
            try:
                cur.execute("""
                    ALTER TABLE card_photos 
                    ADD COLUMN IF NOT EXISTS position INTEGER DEFAULT 0;
                """)
                logger.info("✅ Добавлена колонка 'position' в таблицу card_photos")
            except Exception as e:
                logger.warning(f"⚠️ Колонка 'position' уже существует или ошибка: {e}")
            
            # 2. Добавляем недостающую колонку file_id в card_photos (для совместимости с SQLite)
            try:
                cur.execute("""
                    ALTER TABLE card_photos 
                    ADD COLUMN IF NOT EXISTS file_id TEXT;
                """)
                logger.info("✅ Добавлена колонка 'file_id' в таблицу card_photos")
            except Exception as e:
                logger.warning(f"⚠️ Колонка 'file_id' уже существует или ошибка: {e}")
            
            # 3. Проверяем и добавляем недостающие колонки в cards_v2
            try:
                cur.execute("""
                    ALTER TABLE cards_v2 
                    ADD COLUMN IF NOT EXISTS sub_slug VARCHAR(50);
                """)
                logger.info("✅ Добавлена колонка 'sub_slug' в таблицу cards_v2")
            except Exception as e:
                logger.warning(f"⚠️ Колонка 'sub_slug' уже существует или ошибка: {e}")
            
            # 4. Проверяем и добавляем недостающие колонки в partners_v2
            try:
                cur.execute("""
                    ALTER TABLE partners_v2 
                    ADD COLUMN IF NOT EXISTS karma_points INTEGER DEFAULT 0;
                """)
                logger.info("✅ Добавлена колонка 'karma_points' в таблицу partners_v2")
            except Exception as e:
                logger.warning(f"⚠️ Колонка 'karma_points' уже существует или ошибка: {e}")
            
            conn.commit()
            logger.info("🎯 Унификация структуры БД завершена успешно!")
            
        else:
            logger.info("ℹ️ Используется SQLite, унификация не требуется")
            
    except Exception as e:
        logger.error(f"❌ Ошибка унификации БД: {e}")
        raise

async def diagnose_and_fix_catalog():
    """Диагностика и исправление каталога в продакшене"""
    
    try:
        database_url = os.getenv('DATABASE_URL', '')
        
        if database_url and database_url.startswith("postgresql"):
            import psycopg2
            
            conn = psycopg2.connect(database_url)
            cur = conn.cursor()
            
            logger.info("🔍 ДИАГНОСТИКА КАТАЛОГА В ПРОДАКШЕНЕ")
            logger.info("=" * 50)
            
            # 1. ДИАГНОСТИКА - подсчет карточек по категориям
            query = """
            SELECT 
                c.slug,
                c.name,
                COUNT(cards.id) as total_cards,
                COUNT(CASE WHEN cards.status = 'published' THEN 1 END) as published_cards
            FROM categories_v2 c
            LEFT JOIN cards_v2 cards ON c.id = cards.category_id
            GROUP BY c.id, c.slug, c.name
            ORDER BY published_cards DESC;
            """
            
            cur.execute(query)
            result = cur.fetchall()
            
            logger.info("📊 СОСТОЯНИЕ КАТЕГОРИЙ:")
            empty_categories = []
            
            for row in result:
                slug, name, total, published = row
                logger.info(f"  {slug} ({name}): {published} опубликованных карточек")
                if published == 0:  # published_cards = 0
                    empty_categories.append((slug, name))
            
            # 2. ИСПРАВЛЕНИЕ - добавить карточки в пустые категории
            if empty_categories:
                logger.info(f"🛠️ Найдено {len(empty_categories)} пустых категорий")
                
                for slug, name in empty_categories:
                    await add_test_cards_to_category(cur, slug, name)
                    
                conn.commit()
                logger.info("✅ Все пустые категории заполнены")
            else:
                logger.info("✅ Все категории содержат карточки")
                
            conn.close()
            logger.info("🎉 ДИАГНОСТИКА И ИСПРАВЛЕНИЕ КАТАЛОГА ЗАВЕРШЕНО")
            
        else:
            logger.info("ℹ️ Используется SQLite, диагностика не требуется")
            
    except Exception as e:
        logger.error(f"❌ Ошибка диагностики каталога: {e}")
        raise

async def add_test_cards_to_category(cur, category_slug, category_name):
    """Добавить тестовые карточки в категорию"""
    
    try:
        # Получить ID категории
        cur.execute("SELECT id FROM categories_v2 WHERE slug = %s", (category_slug,))
        category_result = cur.fetchone()
        
        if not category_result:
            logger.error(f"Категория {category_slug} не найдена")
            return
            
        category_id = category_result[0]
        
        # Получить или создать тестового партнера
        cur.execute("""
            INSERT INTO partners_v2 (tg_user_id, display_name, username, status, karma_points)
            VALUES (999999999, 'Sample Partner', 'sample_partner', 'active', 1000)
            ON CONFLICT (tg_user_id) DO NOTHING
            RETURNING id
        """)
        
        partner_result = cur.fetchone()
        if partner_result:
            partner_id = partner_result[0]
        else:
            cur.execute("SELECT id FROM partners_v2 WHERE tg_user_id = 999999999")
            partner_id = cur.fetchone()[0]
        
        # Определить подкатегории для каждой категории
        subcategories = {
            'transport': ['cars', 'bikes', 'bicycles', 'scooters'],
            'hotels': ['hotels', 'apartments', 'hostels'], 
            'shops': ['clothing', 'electronics', 'food', 'books'],
            'spa': ['salon', 'massage', 'wellness'],
            'tours': ['excursions', 'travel', 'adventure'],
            'beauty': ['salon', 'spa', 'massage'],
            'health': ['clinic', 'pharmacy', 'fitness'],
            'education': ['school', 'courses', 'tutoring'],
            'services': ['repair', 'cleaning', 'delivery']
        }
        
        subs = subcategories.get(category_slug, ['general'])
        
        cards_added = 0
        photos_added = 0
        
        for sub_slug in subs:
            for i in range(3):  # 3 карточки на подкатегорию
                
                # Добавить карточку
                cur.execute("""
                    INSERT INTO cards_v2 (
                        partner_id, category_id, title, description, 
                        status, sub_slug, created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, 'published', %s, NOW(), NOW())
                    RETURNING id
                """, (
                    partner_id,
                    f"Тест {category_name} {sub_slug.title()} {i+1}",
                    f"Описание тестовой карточки {i+1} в подкатегории {sub_slug}",
                    sub_slug
                ))
                
                card_result = cur.fetchone()
                if card_result:
                    card_id = card_result[0]
                    cards_added += 1
                    
                    # Добавить 2 фотографии для каждой карточки
                    for photo_num in range(1, 3):
                        cur.execute("""
                            INSERT INTO card_photos (
                                card_id, photo_url, photo_file_id, 
                                is_main, position, file_id
                            ) VALUES (%s, %s, %s, %s, %s, %s)
                        """, (
                            card_id,
                            f"https://example.com/photo_{card_id}_{photo_num}.jpg",
                            f"photo_{card_id}_{photo_num}",
                            photo_num == 1,
                            photo_num,
                            f"photo_{card_id}_{photo_num}"
                        ))
                        photos_added += 1
        
        logger.info(f"✅ Добавлено {cards_added} карточек и {photos_added} фото в категорию {category_slug}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка добавления карточек в {category_slug}: {e}")
        raise

def add_sample_cards():
    """Add sample cards for testing in all categories and subcategories"""
    try:
        # Сначала унифицируем структуру БД
        unify_database_structure()
        
        database_url = os.getenv('DATABASE_URL', '')
        
        if database_url and database_url.startswith("postgresql"):
            import psycopg2
            
            conn = psycopg2.connect(database_url)
            cur = conn.cursor()
            
            # Check if we have any published cards at all
            cur.execute("SELECT COUNT(*) FROM cards_v2 WHERE status = 'published'")
            total_cards = cur.fetchone()[0]
            
            # Always add sample cards if we have less than 50 cards (to ensure all categories have test data)
            if total_cards < 50:
                logger.info("No test cards found, adding sample data for all categories...")
                
                # First, ensure sub_slug column exists
                try:
                    cur.execute("ALTER TABLE cards_v2 ADD COLUMN IF NOT EXISTS sub_slug VARCHAR(50)")
                    conn.commit()
                    logger.info("✅ Added sub_slug column to cards_v2")
                except Exception as e:
                    logger.warning(f"Could not add sub_slug column: {e}")
                
                # Add sample partner
                cur.execute("""
                    INSERT INTO partners_v2 (tg_user_id, display_name, username, status, karma_points)
                    VALUES (123456789, 'Sample Partner', 'sample_partner', 'active', 100)
                    ON CONFLICT (tg_user_id) DO NOTHING
                    RETURNING id
                """)
                result = cur.fetchone()
                if result:
                    partner_id = result[0]
                else:
                    cur.execute("SELECT id FROM partners_v2 WHERE tg_user_id = 123456789")
                    partner_id = cur.fetchone()[0]
                
                # Define all categories and subcategories with sample cards
                categories_data = {
                    'restaurants': {
                        'asia': [
                            ('Суши-бар "Токио"', 'Настоящие японские суши и роллы'),
                            ('Китайский ресторан "Дракон"', 'Аутентичная китайская кухня'),
                            ('Тайский ресторан "Пхукет"', 'Острые тайские блюда')
                        ],
                        'europe': [
                            ('Французский ресторан "Эйфель"', 'Изысканная французская кухня'),
                            ('Итальянская траттория "Рим"', 'Классические итальянские блюда'),
                            ('Немецкий паб "Октоберфест"', 'Традиционная немецкая кухня')
                        ],
                        'street': [
                            ('Бургерная "Street Food"', 'Сочные бургеры и картошка фри'),
                            ('Хот-дог "Быстро"', 'Горячие хот-доги с соусами'),
                            ('Тако-бар "Мехико"', 'Мексиканские тако и буррито')
                        ],
                        'vege': [
                            ('Веган-кафе "Зелень"', 'Полезная веганская еда'),
                            ('Салат-бар "Витамин"', 'Свежие салаты и смузи'),
                            ('Органик-кафе "Природа"', 'Органические продукты')
                        ],
                        'all': [
                            ('Ресторан "Вкусно"', 'Отличная кухня и атмосфера'),
                            ('Кафе "Уют"', 'Домашняя кухня и кофе'),
                            ('Пиццерия "Италия"', 'Настоящая итальянская пицца')
                        ]
                    },
                    'spa': {
                        'salon': [
                            ('Салон красоты "Элегант"', 'Парикмахерские услуги и маникюр'),
                            ('Барбершоп "Мужской"', 'Стрижки и бритье для мужчин'),
                            ('Студия красоты "Гламур"', 'Макияж и укладки')
                        ],
                        'massage': [
                            ('СПА-центр "Релакс"', 'Массаж и релаксация'),
                            ('Тайский массаж "Сиам"', 'Традиционный тайский массаж'),
                            ('Массажный салон "Здоровье"', 'Лечебный массаж')
                        ],
                        'sauna': [
                            ('Сауна "Баня"', 'Русская баня и сауна'),
                            ('Финская сауна "Север"', 'Традиционная финская сауна'),
                            ('Хаммам "Восток"', 'Турецкая баня')
                        ],
                        'all': [
                            ('СПА "Роскошь"', 'Полный спектр СПА-услуг'),
                            ('Массаж "Нежность"', 'Расслабляющий массаж'),
                            ('Сауна "Жара"', 'Горячая сауна и бассейн')
                        ]
                    },
                    'transport': {
                        'bikes': [
                            ('Прокат мотоциклов "Скорость"', 'Мотоциклы для аренды'),
                            ('Скутеры "Город"', 'Электрические скутеры'),
                            ('Мопеды "Эконом"', 'Недорогие мопеды')
                        ],
                        'cars': [
                            ('Автопрокат "Премиум"', 'Люкс автомобили'),
                            ('Эконом-кар "Бюджет"', 'Недорогие автомобили'),
                            ('Семейные авто "Комфорт"', 'Просторные автомобили')
                        ],
                        'bicycles': [
                            ('Велосипеды "Эко"', 'Экологичный транспорт'),
                            ('Горные велосипеды "Адреналин"', 'Для экстремального спорта'),
                            ('Городские велосипеды "Удобство"', 'Для городских поездок')
                        ],
                        'all': [
                            ('Транспорт "Универсал"', 'Различные виды транспорта'),
                            ('Прокат "24/7"', 'Круглосуточный прокат'),
                            ('Транспорт "Быстро"', 'Быстрая подача транспорта')
                        ]
                    },
                    'hotels': {
                        'hotel': [
                            ('Отель "Люкс"', 'Пятизвездочный отель'),
                            ('Гостиница "Комфорт"', 'Уютная гостиница'),
                            ('Отель "Бизнес"', 'Для деловых поездок')
                        ],
                        'apartments': [
                            ('Апартаменты "Дом"', 'Квартиры для длительного проживания'),
                            ('Студии "Мини"', 'Компактные студии'),
                            ('Лофты "Стиль"', 'Стильные лофты')
                        ],
                        'all': [
                            ('Отель "Гранд"', 'Большой отель с услугами'),
                            ('Гостиница "Центр"', 'В центре города'),
                            ('Отель "Тишина"', 'Спокойное место для отдыха')
                        ]
                    },
                    'tours': {
                        'group': [
                            ('Групповые экскурсии "Друзья"', 'Экскурсии для групп'),
                            ('Туры "Компания"', 'Корпоративные туры'),
                            ('Походы "Команда"', 'Групповые походы')
                        ],
                        'private': [
                            ('Индивидуальные туры "Личный"', 'Персональные экскурсии'),
                            ('VIP туры "Эксклюзив"', 'Эксклюзивные туры'),
                            ('Частные гиды "Персональный"', 'Личные гиды')
                        ],
                        'all': [
                            ('Туры "Открытие"', 'Познавательные туры'),
                            ('Экскурсии "История"', 'Исторические экскурсии'),
                            ('Путешествия "Приключение"', 'Приключенческие туры')
                        ]
                    },
                    'shops': {
                        'shops': [
                            ('Магазин "Мода"', 'Одежда и аксессуары'),
                            ('Бутик "Стиль"', 'Дизайнерская одежда'),
                            ('Торговый центр "Мега"', 'Большой торговый центр')
                        ],
                        'services': [
                            ('Сервис "Ремонт"', 'Ремонтные услуги'),
                            ('Услуги "Красота"', 'Косметические услуги'),
                            ('Сервис "Доставка"', 'Служба доставки')
                        ],
                        'all': [
                            ('Магазин "Универсал"', 'Различные товары'),
                            ('Сервис "Удобство"', 'Удобные услуги'),
                            ('Торговля "Качество"', 'Качественные товары')
                        ]
                    }
                }
                
                # Add cards for each category and subcategory
                for category_slug, subcategories in categories_data.items():
                    cur.execute("SELECT id FROM categories_v2 WHERE slug = %s", (category_slug,))
                    cat_result = cur.fetchone()
                    if cat_result:
                        category_id = cat_result[0]
                        
                        for sub_slug, cards in subcategories.items():
                            for title, description in cards:
                                # Check if card already exists (by title and category)
                                cur.execute("""
                                    SELECT id FROM cards_v2 
                                    WHERE partner_id = %s AND category_id = %s AND title = %s
                                """, (partner_id, category_id, title))
                                
                                existing_card = cur.fetchone()
                                if not existing_card:
                                    cur.execute("""
                                        INSERT INTO cards_v2 (partner_id, category_id, title, description, status, sub_slug)
                                        VALUES (%s, %s, %s, %s, %s, %s)
                                        RETURNING id
                                    """, (partner_id, category_id, title, description, 'published', sub_slug))
                                
                                result = cur.fetchone()
                                if result:
                                    card_id = result[0]
                                    # Add 2 photos for each card (унифицированная структура)
                                    for photo_num in range(1, 3):
                                        cur.execute("""
                                            INSERT INTO card_photos (card_id, photo_url, photo_file_id, is_main, position, file_id)
                                            VALUES (%s, %s, %s, %s, %s, %s)
                                            ON CONFLICT DO NOTHING
                                        """, (card_id, f"https://example.com/photo_{card_id}_{photo_num}.jpg", 
                                              f"photo_{card_id}_{photo_num}", photo_num == 1, photo_num, f"photo_{card_id}_{photo_num}"))
                        
                        logger.info(f"✅ Sample cards added to {category_slug} category")
                
                conn.commit()
                logger.info("✅ All sample cards added successfully")
            else:
                logger.info(f"Found {total_cards} published cards, skipping sample data")
            
            cur.close()
            conn.close()
            
        else:
            logger.info("Using SQLite, skipping sample data")
            
    except Exception as e:
        logger.error(f"Error adding sample cards: {e}")

def ensure_card_photos_table():
    """Ensure card_photos table exists"""
    try:
        database_url = os.getenv('DATABASE_URL', '')
        
        if database_url and database_url.startswith("postgresql"):
            # PostgreSQL - use synchronous connection
            import psycopg2
            
            conn = psycopg2.connect(database_url)
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS card_photos (
                    id SERIAL PRIMARY KEY,
                    card_id INTEGER NOT NULL,
                    photo_url TEXT NOT NULL,
                    photo_file_id TEXT,
                    caption TEXT,
                    is_main BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    FOREIGN KEY (card_id) REFERENCES cards_v2(id) ON DELETE CASCADE
                );
            """)
            
            # Create indexes
            cur.execute("CREATE INDEX IF NOT EXISTS idx_card_photos_card_id ON card_photos(card_id)")
            try:
                cur.execute("CREATE INDEX IF NOT EXISTS idx_card_photos_is_main ON card_photos(is_main)")
            except Exception as e:
                logger.warning(f"Could not create index on is_main column: {e}")
            
            conn.commit()
            cur.close()
            conn.close()
            logger.info("✅ card_photos table created/verified in PostgreSQL")
        else:
            # SQLite fallback
            import sqlite3
            db_path = os.getenv('DATABASE_PATH', 'core/database/data.db')
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS card_photos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    card_id INTEGER NOT NULL,
                    photo_url TEXT NOT NULL,
                    photo_file_id TEXT,
                    caption TEXT,
                    is_main BOOLEAN DEFAULT FALSE,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (card_id) REFERENCES cards_v2(id) ON DELETE CASCADE
                );
            """)
            
            # Create indexes
            cur.execute("CREATE INDEX IF NOT EXISTS idx_card_photos_card_id ON card_photos(card_id)")
            try:
                cur.execute("CREATE INDEX IF NOT EXISTS idx_card_photos_is_main ON card_photos(is_main)")
            except Exception as e:
                logger.warning(f"Could not create index on is_main column: {e}")
            
            conn.commit()
            cur.close()
            conn.close()
            logger.info("✅ card_photos table created/verified in SQLite")
            
    except Exception as e:
        logger.error(f"Error creating card_photos table: {e}")

def fix_invalid_photo_file_ids():
    """Fix invalid photo file_ids in card_photos table"""
    try:
        if os.getenv('DATABASE_URL'):
            # PostgreSQL
            import asyncpg
            import asyncio
            
            async def fix_postgresql():
                conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
                try:
                    # Очищаем неправильные file_id
                    result = await conn.execute("""
                        UPDATE card_photos 
                        SET file_id = NULL 
                        WHERE file_id IS NOT NULL 
                        AND (
                            LENGTH(file_id) < 10 
                            OR file_id LIKE '%wrong%' 
                            OR file_id LIKE '%error%'
                            OR file_id = ''
                        )
                    """)
                    logger.info(f"✅ Очищены неправильные file_id в PostgreSQL: {result}")
                    
                    # Также очищаем photo_file_id если он есть
                    result2 = await conn.execute("""
                        UPDATE card_photos 
                        SET photo_file_id = NULL 
                        WHERE photo_file_id IS NOT NULL 
                        AND (
                            LENGTH(photo_file_id) < 10 
                            OR photo_file_id LIKE '%wrong%' 
                            OR photo_file_id LIKE '%error%'
                            OR photo_file_id = ''
                        )
                    """)
                    logger.info(f"✅ Очищены неправильные photo_file_id в PostgreSQL: {result2}")
                    
                finally:
                    await conn.close()
            
            asyncio.run(fix_postgresql())
        else:
            # SQLite
            import sqlite3
            conn = sqlite3.connect('bot_database.db')
            try:
                cur = conn.cursor()
                
                # Очищаем неправильные file_id
                cur.execute("""
                    UPDATE card_photos 
                    SET file_id = NULL 
                    WHERE file_id IS NOT NULL 
                    AND (
                        LENGTH(file_id) < 10 
                        OR file_id LIKE '%wrong%' 
                        OR file_id LIKE '%error%'
                        OR file_id = ''
                    )
                """)
                logger.info(f"✅ Очищены неправильные file_id в SQLite: {cur.rowcount}")
                
                conn.commit()
            finally:
                conn.close()
                
    except Exception as e:
        logger.error(f"Error fixing photo file_ids: {e}")
