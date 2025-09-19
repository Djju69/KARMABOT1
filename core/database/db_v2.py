"""
Enhanced database service with backward compatibility
Implements new schema while maintaining legacy support
"""
import os
import sqlite3
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import logging

from .migrations import DatabaseMigrator

logger = logging.getLogger(__name__)

def get_connection():
    """Get database connection for backward compatibility"""
    import sqlite3
    from core.settings import settings
    
    if hasattr(settings, 'database_url') and settings.database_url and 'postgresql' in settings.database_url.lower():
        # For PostgreSQL, return asyncpg connection wrapper
        import asyncpg
        import asyncio
        
        class AsyncConnectionWrapper:
            def __init__(self):
                self.conn = None
                
            async def __aenter__(self):
                self.conn = await asyncpg.connect(settings.database_url)
                return self.conn
                
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                if self.conn:
                    await self.conn.close()
        
        return AsyncConnectionWrapper()
    else:
        # SQLite fallback with unified path
        db_path = os.getenv('DATABASE_PATH') or 'core/database/data.db'
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        return sqlite3.connect(db_path)

@dataclass
class Partner:
    id: Optional[int]
    tg_user_id: int
    display_name: Optional[str]
    phone: Optional[str] = None
    email: Optional[str] = None
    is_verified: bool = False
    is_active: bool = True

@dataclass
class Card:
    id: Optional[int]
    partner_id: int
    category_id: int
    title: str
    description: Optional[str] = None
    contact: Optional[str] = None
    address: Optional[str] = None
    google_maps_url: Optional[str] = None
    photo_file_id: Optional[str] = None
    discount_text: Optional[str] = None
    status: str = 'draft'
    priority_level: int = 0
    subcategory_id: Optional[int] = None
    city_id: Optional[int] = None
    area_id: Optional[int] = None

@dataclass
class Category:
    id: Optional[int]
    slug: str
    name: str
    emoji: Optional[str]
    priority_level: int = 0
    is_active: bool = True

class DatabaseServiceV2:
    def __init__(self, db_path: str = "core/database/data.db"):
        # DatabaseServiceV2 is now SQLite-only
        # PostgreSQL is handled by PostgreSQLService via DatabaseAdapter
        self.use_postgresql = False
        self._is_memory = db_path == ":memory:" or str(db_path).startswith("file::memory:")
        if self._is_memory:
            self._memory_uri = db_path if str(db_path).startswith("file:") else "file::memory:?cache=shared"
            self._conn = sqlite3.connect(self._memory_uri, uri=True, check_same_thread=False)
            self._conn.execute("PRAGMA foreign_keys = ON")
            self._conn.row_factory = sqlite3.Row
            self.db_path = None
        else:
            self.db_path = Path(db_path)
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            self._conn = None
        
        # Run migrations only if APPLY_MIGRATIONS=1
        apply_migrations = os.environ.get('APPLY_MIGRATIONS', '0') == '1'
        if apply_migrations:
            try:
                migrator_path = self._memory_uri if self._is_memory else str(self.db_path)
                migrator = DatabaseMigrator(migrator_path)
                migrator.run_all_migrations()
                logger.info("Database migrations completed successfully")
            except Exception as e:
                # Log the error but don't crash - allow the app to start
                logger.error(f"Database migration failed: {e}")
                logger.warning("Continuing without applying migrations")
        else:
            logger.info("Skipping database migrations (APPLY_MIGRATIONS=0)")
    
    def get_connection(self):
        """Get database connection with row factory"""
        if self.use_postgresql:
            # For PostgreSQL, we need to use asyncpg
            # This is a placeholder - in production we should use async methods
            raise NotImplementedError("PostgreSQL connection not implemented in sync methods")
        
        if self._is_memory and self._conn is not None:
            return self._conn
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        return conn
    
    # Partner methods
    def create_partner(self, partner: Partner) -> int:
        """Create new partner, return ID"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO partners_v2 (tg_user_id, display_name, phone, email, is_verified, is_active)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                partner.tg_user_id, partner.display_name, partner.phone,
                partner.email, partner.is_verified, partner.is_active
            ))
            return cursor.lastrowid
    
    def get_partner_by_tg_id(self, tg_user_id: int) -> Optional[Partner]:
        """Get partner by Telegram user ID"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM partners_v2 WHERE tg_user_id = ?",
                (tg_user_id,)
            )
            row = cursor.fetchone()
            if row:
                data = dict(row)
                # Filter unknown columns (e.g., created_at, updated_at) to match dataclass fields
                allowed = {k: data[k] for k in Partner.__dataclass_fields__.keys() if k in data}
                return Partner(**allowed)
            return None
    
    def get_or_create_partner(self, tg_user_id: int, display_name: str = None) -> Partner:
        """Get existing partner or create new one"""
        partner = self.get_partner_by_tg_id(tg_user_id)
        if not partner:
            new_partner = Partner(
                id=None,
                tg_user_id=tg_user_id,
                display_name=display_name
            )
            partner_id = self.create_partner(new_partner)
            new_partner.id = partner_id
            return new_partner
        return partner
    
    # Card methods
    def create_card(self, card: Card) -> int:
        """Create new card, return ID"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO cards_v2 (
                    partner_id, category_id, title, description, contact,
                    address, google_maps_url, photo_file_id, discount_text,
                    status, priority_level, subcategory_id, city_id, area_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                card.partner_id, card.category_id, card.title, card.description,
                card.contact, card.address, card.google_maps_url, card.photo_file_id,
                card.discount_text, card.status, card.priority_level,
                card.subcategory_id, card.city_id, card.area_id
            ))
            return cursor.lastrowid

    def update_card_odoo_id(self, card_id: int, odoo_card_id: int) -> bool:
        """Store Odoo card id mapping for a bot card."""
        with self.get_connection() as conn:
            cur = conn.execute(
                "UPDATE cards_v2 SET odoo_card_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (int(odoo_card_id), int(card_id)),
            )
            return (cur.rowcount or 0) > 0
    
    def update_card_status(self, card_id: int, status: str, moderator_id: int = None, comment: str = None) -> bool:
        """Update card status with moderation log"""
        with self.get_connection() as conn:
            try:
                logger.debug("update_card_status: card_id=%s status=%s moderator_id=%s comment=%s", card_id, status, moderator_id, (comment or '')[:140])
            except Exception:
                pass
            # Update card status
            cursor = conn.execute(
                "UPDATE cards_v2 SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (status, card_id)
            )
            
            # Log moderation action
            if moderator_id:
                # Normalize action name for log to match CHECK constraint
                # Map statuses to actions: published/approved -> approve, rejected -> reject, archived -> archive
                s = (status or '').lower()
                if s in ('published', 'approved'):
                    action = 'approve'
                elif s == 'rejected':
                    action = 'reject'
                elif s == 'archived':
                    action = 'archive'
                else:
                    action = None
                if action in ['approve', 'reject', 'archive', 'feature']:
                    try:
                        conn.execute(
                            """
                            INSERT INTO moderation_log (card_id, moderator_id, action, comment)
                            VALUES (?, ?, ?, ?)
                            """,
                            (card_id, moderator_id, action, comment),
                        )
                    except sqlite3.IntegrityError as e:
                        logger.error(
                            "moderation_log insert failed: card_id=%s moderator_id=%s status=%s action=%s comment_len=%s error=%s",
                            card_id, moderator_id, status, action, len(comment or ''), e,
                        )
                        raise
                    except Exception as e:
                        logger.exception(
                            "unexpected error inserting into moderation_log: card_id=%s moderator_id=%s status=%s action=%s",
                            card_id, moderator_id, status, action,
                        )
                        raise
            
            return cursor.rowcount > 0
    
    def get_cards_by_category(self, category_slug: str, status: str = 'published', limit: int = 50) -> List[Dict]:
        """Get cards by category with pagination"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT c.*, cat.name as category_name, cat.emoji as category_emoji,
                       p.display_name as partner_name,
                       COALESCE(COUNT(cp.id), 0) as photos_count
                FROM cards_v2 c
                JOIN categories_v2 cat ON c.category_id = cat.id
                JOIN partners_v2 p ON c.partner_id = p.id
                LEFT JOIN card_photos cp ON cp.card_id = c.id
                WHERE cat.slug = ? AND c.status = ? AND cat.is_active = 1
                GROUP BY c.id
                ORDER BY c.priority_level DESC, c.created_at DESC
                LIMIT ?
                """,
                (category_slug, status, limit),
            )
            
            return [dict(row) for row in cursor.fetchall()]

    # --- Superadmin helpers: bans and deletions ---
    def ban_user(self, tg_user_id: int, reason: str = "") -> None:
        """Ban Telegram user by ID (idempotent)."""
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO banned_users(user_id, reason, banned_at)
                VALUES(?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id) DO UPDATE SET reason=excluded.reason, banned_at=CURRENT_TIMESTAMP, unbanned_at=NULL
                """,
                (int(tg_user_id), reason or ""),
            )

    def unban_user(self, tg_user_id: int) -> None:
        """Remove ban for Telegram user (idempotent)."""
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE banned_users SET unbanned_at=CURRENT_TIMESTAMP WHERE user_id = ?",
                (int(tg_user_id),),
            )
            conn.execute("DELETE FROM banned_users WHERE user_id = ?", (int(tg_user_id),))

    def is_user_banned(self, tg_user_id: int) -> bool:
        with self.get_connection() as conn:
            cur = conn.execute("SELECT 1 FROM banned_users WHERE user_id = ?", (int(tg_user_id),))
            return cur.fetchone() is not None

    def delete_user_cascade_by_tg_id(self, tg_user_id: int) -> dict:
        """Delete user-related data: partner, cards (via cascade), QR, moderation logs, loyalty.* tables.
        Returns counts per table (best-effort).
        """
        stats = {"partners_v2": 0, "cards_v2": 0, "qr_codes_v2": 0, "moderation_log": 0,
                 "loyalty_wallets": 0, "loy_spend_intents": 0, "user_cards": 0, "loyalty_transactions": 0}
        with self.get_connection() as conn:
            # Count cards before delete for stats
            partner_id = None
            cur = conn.execute("SELECT id FROM partners_v2 WHERE tg_user_id = ?", (int(tg_user_id),))
            row = cur.fetchone()
            if row:
                partner_id = int(row[0])
                # gather related counts
                cur = conn.execute("SELECT COUNT(*) FROM cards_v2 WHERE partner_id = ?", (partner_id,))
                stats["cards_v2"] = int(cur.fetchone()[0])
                cur = conn.execute("SELECT COUNT(*) FROM qr_codes_v2 WHERE card_id IN (SELECT id FROM cards_v2 WHERE partner_id = ?)", (partner_id,))
                stats["qr_codes_v2"] = int(cur.fetchone()[0])
                cur = conn.execute("SELECT COUNT(*) FROM moderation_log WHERE card_id IN (SELECT id FROM cards_v2 WHERE partner_id = ?)", (partner_id,))
                stats["moderation_log"] = int(cur.fetchone()[0])
                # delete partner (CASCADE deletes cards/qr/mod)
                conn.execute("DELETE FROM partners_v2 WHERE id = ?", (partner_id,))
                stats["partners_v2"] = 1
            # loyalty tables keyed by Telegram user_id
            loyalty_tables = ["loyalty_wallets", "loy_spend_intents", "user_cards", "loyalty_transactions"]
            for table in loyalty_tables:
                # Безопасный параметризованный запрос
                if table == "loyalty_wallets":
                    res = conn.execute("DELETE FROM loyalty_wallets WHERE user_id = ?", (int(tg_user_id),))
                elif table == "loy_spend_intents":
                    res = conn.execute("DELETE FROM loy_spend_intents WHERE user_id = ?", (int(tg_user_id),))
                elif table == "user_cards":
                    res = conn.execute("DELETE FROM user_cards WHERE user_id = ?", (int(tg_user_id),))
                elif table == "loyalty_transactions":
                    res = conn.execute("DELETE FROM loyalty_transactions WHERE user_id = ?", (int(tg_user_id),))
                stats[table] = res.rowcount or stats.get(table, 0)
            # clear ban if exists
            conn.execute("DELETE FROM banned_users WHERE user_id = ?", (int(tg_user_id),))
        return stats

    def delete_card(self, card_id: int) -> bool:
        with self.get_connection() as conn:
            cur = conn.execute("DELETE FROM cards_v2 WHERE id = ?", (int(card_id),))
            return (cur.rowcount or 0) > 0

    def delete_cards_by_partner_tg(self, tg_user_id: int) -> int:
        with self.get_connection() as conn:
            cur = conn.execute("SELECT id FROM partners_v2 WHERE tg_user_id = ?", (int(tg_user_id),))
            row = cur.fetchone()
            if not row:
                return 0
            partner_id = int(row[0])
            cur = conn.execute("DELETE FROM cards_v2 WHERE partner_id = ?", (partner_id,))
            return cur.rowcount or 0

    def delete_all_cards(self) -> int:
        with self.get_connection() as conn:
            cur = conn.execute("DELETE FROM cards_v2")
            return cur.rowcount or 0

    def admin_add_card(self, partner_tg_id: int, category_slug: str, title: str, **fields) -> Optional[int]:
        """Create a card on behalf of partner by Telegram ID and category slug. Returns new card id or None."""
        partner = self.get_or_create_partner(int(partner_tg_id))
        category = self.get_category_by_slug(category_slug)
        if not category:
            return None
        card = Card(
            id=None,
            partner_id=int(partner.id),
            category_id=int(category.id),
            title=title,
            description=fields.get("description"),
            contact=fields.get("contact"),
            address=fields.get("address"),
            google_maps_url=fields.get("google_maps_url"),
            photo_file_id=fields.get("photo_file_id"),
            discount_text=fields.get("discount_text"),
            status=fields.get("status", "draft"),
            priority_level=int(fields.get("priority_level", 0)),
            subcategory_id=fields.get("subcategory_id"),
            city_id=fields.get("city_id"),
            area_id=fields.get("area_id"),
        )
        return self.create_card(card)

    def get_card_by_id(self, card_id: int) -> Optional[Dict[str, Any]]:
        """Get single card by ID with joined fields"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT c.*, cat.name as category_name, cat.slug as category_slug,
                       p.display_name as partner_name,
                       COALESCE(COUNT(cp.id), 0) as photos_count
                FROM cards_v2 c
                JOIN categories_v2 cat ON c.category_id = cat.id
                JOIN partners_v2 p ON c.partner_id = p.id
                LEFT JOIN card_photos cp ON cp.card_id = c.id
                WHERE c.id = ?
                GROUP BY c.id
                """,
                (card_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    # --- Card photos helpers ---
    def add_card_photo(self, card_id: int, file_id: str, position: Optional[int] = None) -> int:
        """Add a photo to card_photos. If position is None, append to the end."""
        with self.get_connection() as conn:
            if position is None:
                cur = conn.execute(
                    "SELECT COALESCE(MAX(position), -1) + 1 FROM card_photos WHERE card_id = ?",
                    (int(card_id),),
                )
                position = int(cur.fetchone()[0])
            cursor = conn.execute(
                """
                INSERT INTO card_photos(card_id, file_id, position)
                VALUES(?, ?, ?)
                """,
                (int(card_id), str(file_id), int(position)),
            )
            return cursor.lastrowid

    def get_card_photos(self, card_id: int) -> List[Dict[str, Any]]:
        """Return photos for a card ordered by position ASC."""
        with self.get_connection() as conn:
            cur = conn.execute(
                "SELECT id, file_id, position, created_at FROM card_photos WHERE card_id = ? ORDER BY position ASC",
                (int(card_id),),
            )
            return [dict(r) for r in cur.fetchall()]

    def delete_card_photo(self, photo_id: int) -> bool:
        with self.get_connection() as conn:
            cur = conn.execute("DELETE FROM card_photos WHERE id = ?", (int(photo_id),))
            return (cur.rowcount or 0) > 0

    def clear_card_photos(self, card_id: int) -> int:
        with self.get_connection() as conn:
            cur = conn.execute("DELETE FROM card_photos WHERE card_id = ?", (int(card_id),))
            return cur.rowcount or 0

    def count_card_photos(self, card_id: int) -> int:
        with self.get_connection() as conn:
            cur = conn.execute("SELECT COUNT(*) FROM card_photos WHERE card_id = ?", (int(card_id),))
            return int(cur.fetchone()[0])
    
    def get_partner_cards(self, partner_id: int, statuses: Optional[List[str]] = None) -> List[Dict]:
        """Get partner cards with optional status filtering.
        If statuses is None or empty, returns all cards for the partner.
        """
        with self.get_connection() as conn:
            if statuses:
                placeholders = ",".join(["?"] * len(statuses))
                query = f"""
                    SELECT c.*, cat.name as category_name,
                           COALESCE(COUNT(cp.id), 0) as photos_count
                    FROM cards_v2 c
                    JOIN categories_v2 cat ON c.category_id = cat.id
                    LEFT JOIN card_photos cp ON cp.card_id = c.id
                    WHERE c.partner_id = ? AND c.status IN ({placeholders})
                    GROUP BY c.id
                    ORDER BY c.updated_at DESC
                """
                params = [partner_id, *statuses]
            else:
                query = """
                    SELECT c.*, cat.name as category_name,
                           COALESCE(COUNT(cp.id), 0) as photos_count
                    FROM cards_v2 c
                    JOIN categories_v2 cat ON c.category_id = cat.id
                    LEFT JOIN card_photos cp ON cp.card_id = c.id
                    WHERE c.partner_id = ?
                    GROUP BY c.id
                    ORDER BY c.updated_at DESC
                """
                params = [partner_id]
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_cards_pending_moderation(self, limit: int = 20) -> List[Dict]:
        """Get cards waiting for moderation"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT c.*, cat.name as category_name, p.display_name as partner_name
                FROM cards_v2 c
                JOIN categories_v2 cat ON c.category_id = cat.id
                JOIN partners_v2 p ON c.partner_id = p.id
                WHERE c.status = 'pending'
                ORDER BY c.created_at ASC
                LIMIT ?
                """,
                (limit,),
            )
            return [dict(row) for row in cursor.fetchall()]
    
    def get_categories(self, only_active: bool = True) -> List[Category]:
        """Return list of categories.
        If only_active=True, returns only categories with is_active=1.
        Sorted by priority_level DESC, then name ASC.
        """
        with self.get_connection() as conn:
            if only_active:
                cur = conn.execute(
                    """
                    SELECT id, slug, name, emoji, priority_level, is_active
                    FROM categories_v2
                    WHERE is_active = 1
                    ORDER BY priority_level DESC, name ASC
                    """
                )
            else:
                cur = conn.execute(
                    """
                    SELECT id, slug, name, emoji, priority_level, is_active
                    FROM categories_v2
                    ORDER BY priority_level DESC, name ASC
                    """
                )
            return [Category(**dict(row)) for row in cur.fetchall()]
    
    def get_category_by_slug(self, slug: str) -> Optional[Category]:
        """Get category by slug"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT id, slug, name, emoji, priority_level, is_active FROM categories_v2 WHERE slug = ?",
                (slug,)
            )
            row = cursor.fetchone()
            if row:
                return Category(**dict(row))
            return None
    
    # QR Code methods
    def create_qr_code(self, card_id: int, qr_token: str, expires_at: str = None) -> int:
        """Create QR code for card"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO qr_codes_v2 (card_id, qr_token, expires_at)
                VALUES (?, ?, ?)
            """, (card_id, qr_token, expires_at))
            return cursor.lastrowid
    
    def redeem_qr_code(self, qr_token: str, redeemed_by: int) -> bool:
        """Redeem QR code atomically"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                UPDATE qr_codes_v2 
                SET is_redeemed = 1, redeemed_at = CURRENT_TIMESTAMP, redeemed_by = ?
                WHERE qr_token = ? AND is_redeemed = 0 
                AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
                RETURNING id
            """, (redeemed_by, qr_token))
            
            return cursor.fetchone() is not None
    
    # Backward compatibility methods
    def get_user_qr_codes(self, user_id: int) -> List[Dict]:
        """Get QR codes for user"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT id, qr_id, name, discount, is_active, created_at, expires_at
                FROM qr_codes_v2
                WHERE user_id = ? AND is_active = 1
                  AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
                ORDER BY created_at DESC
                """,
                (user_id,)
            )
            return [dict(row) for row in cursor.fetchall()]
    
    def create_user_qr_code(self, user_id: int, qr_id: str, name: str, discount: int = 10) -> bool:
        """Create QR code for user"""
        with self.get_connection() as conn:
            try:
                # Compute expiration in Python to support both SQLite and Postgres
                from datetime import datetime, timedelta
                exp = (datetime.utcnow() + timedelta(days=30)).isoformat(sep=' ', timespec='seconds')
                cursor = conn.execute(
                    """
                    INSERT INTO qr_codes_v2 (user_id, qr_id, name, discount, is_active, created_at, expires_at)
                    VALUES (?, ?, ?, ?, 1, CURRENT_TIMESTAMP, ?)
                    """,
                    (user_id, qr_id, name, discount, exp)
                )
                return cursor.rowcount > 0
            except Exception as e:
                logger.error(f"Error creating QR code: {e}")
                return False

    def deactivate_user_qr_code(self, user_id: int, qr_id: str) -> bool:
        """Deactivate a user QR by id (mark is_active=0)."""
        with self.get_connection() as conn:
            cur = conn.execute(
                """
                UPDATE qr_codes_v2
                SET is_active = 0
                WHERE user_id = ? AND qr_id = ? AND is_active = 1
                """,
                (int(user_id), str(qr_id))
            )
            return (cur.rowcount or 0) > 0

    def get_legacy_categories(self) -> List[Dict]:
        """Get categories in legacy format for backward compatibility"""
        categories = self.get_categories()
        return [
            {
                'id': cat.id,
                'name_ru': cat.name,
                'name_en': cat.name,  # Fallback
                'name_ko': cat.name,  # Fallback
                'type': cat.slug
            }
            for cat in categories
        ]
    
    def add_legacy_place(self, name: str, category: str, address: str, discount: str, link: str, qr_code: str):
        """Add place in legacy format (backward compatibility)"""
        # Find category by name
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT id FROM categories_v2 WHERE name = ?",
                (category,)
            )
            row = cursor.fetchone()
            if not row:
                return False
            
            category_id = row[0]
            
            # Create system partner if not exists
            system_partner = self.get_or_create_partner(0, "System")
            
            # Create card
            card = Card(
                id=None,
                partner_id=system_partner.id,
                category_id=category_id,
                title=name,
                description=f"Скидка: {discount}",
                address=address,
                google_maps_url=link,
                discount_text=discount,
                status='published'  # Auto-approve legacy places
            )
            
            return self.create_card(card)
    
    def get_cards_count(self) -> int:
        """Get total number of cards"""
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM cards_v2")
            return cursor.fetchone()[0]
    
    def get_partners_count(self) -> int:
        """Get total number of partners"""
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM partners_v2")
            return cursor.fetchone()[0]
    
    def get_partners_by_status(self, status: str) -> List[Partner]:
        """Get partners by status"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM partners_v2 WHERE status = ? ORDER BY created_at DESC",
                (status,)
            )
            rows = cursor.fetchall()
            return [Partner.from_row(row) for row in rows]

# Global database service instance - use adapter instead
from .db_adapter import db_v2

def get_db():
    """
    Dependency function that yields database sessions.
    To be used in FastAPI dependencies or similar contexts.
    """
    db = db_v2.get_connection()
    try:
        yield db
    finally:
        db.close()
