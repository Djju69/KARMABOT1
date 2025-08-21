"""
Enhanced database service with backward compatibility
Implements new schema while maintaining legacy support
"""
import sqlite3
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import logging

from .migrations import ensure_database_ready

logger = logging.getLogger(__name__)

@dataclass
class Partner:
    id: Optional[int]
    tg_user_id: int
    display_name: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    is_verified: bool = False
    is_active: bool = True

@dataclass
class Card:
    id: Optional[int]
    partner_id: int
    category_id: int
    title: str
    description: Optional[str]
    contact: Optional[str]
    address: Optional[str]
    google_maps_url: Optional[str]
    photo_file_id: Optional[str]
    discount_text: Optional[str]
    status: str = 'draft'
    priority_level: int = 0

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
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Ensure database is migrated
        if not ensure_database_ready():
            raise RuntimeError("Failed to initialize database")
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory"""
        conn = sqlite3.connect(self.db_path)
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
                return Partner(**dict(row))
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
                    status, priority_level
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                card.partner_id, card.category_id, card.title, card.description,
                card.contact, card.address, card.google_maps_url, card.photo_file_id,
                card.discount_text, card.status, card.priority_level
            ))
            return cursor.lastrowid
    
    def update_card_status(self, card_id: int, status: str, moderator_id: int = None, comment: str = None) -> bool:
        """Update card status with moderation log"""
        with self.get_connection() as conn:
            # Update card status
            cursor = conn.execute(
                "UPDATE cards_v2 SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (status, card_id)
            )
            
            # Log moderation action
            if moderator_id and status in ['approved', 'rejected', 'archived']:
                conn.execute("""
                    INSERT INTO moderation_log (card_id, moderator_id, action, comment)
                    VALUES (?, ?, ?, ?)
                """, (card_id, moderator_id, status, comment))
            
            return cursor.rowcount > 0
    
    def get_cards_by_category(self, category_slug: str, status: str = 'published', limit: int = 50) -> List[Dict]:
        """Get cards by category with pagination"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT c.*, cat.name as category_name, cat.emoji as category_emoji,
                       p.display_name as partner_name
                FROM cards_v2 c
                JOIN categories_v2 cat ON c.category_id = cat.id
                JOIN partners_v2 p ON c.partner_id = p.id
                WHERE cat.slug = ? AND c.status = ? AND cat.is_active = 1
                ORDER BY c.priority_level DESC, c.created_at DESC
                LIMIT ?
            """, (category_slug, status, limit))
            
            return [dict(row) for row in cursor.fetchall()]

    def get_card_by_id(self, card_id: int) -> Optional[Dict[str, Any]]:
        """Get single card by ID with joined fields"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT c.*, cat.name as category_name, cat.slug as category_slug,
                       p.display_name as partner_name
                FROM cards_v2 c
                JOIN categories_v2 cat ON c.category_id = cat.id
                JOIN partners_v2 p ON c.partner_id = p.id
                WHERE c.id = ?
                """,
                (card_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_cards_pending_moderation(self, limit: int = 20) -> List[Dict]:
        """Get cards waiting for moderation"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT c.*, cat.name as category_name, p.display_name as partner_name
                FROM cards_v2 c
                JOIN categories_v2 cat ON c.category_id = cat.id
                JOIN partners_v2 p ON c.partner_id = p.id
                WHERE c.status = 'pending'
                ORDER BY c.created_at ASC
                LIMIT ?
            """, (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_partner_cards(self, partner_id: int) -> List[Dict]:
        """Get all cards for a partner"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT c.*, cat.name as category_name
                FROM cards_v2 c
                JOIN categories_v2 cat ON c.category_id = cat.id
                WHERE c.partner_id = ?
                ORDER BY c.updated_at DESC
            """, (partner_id,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    # Category methods
    def get_categories(self, active_only: bool = True) -> List[Category]:
        """Get all categories"""
        with self.get_connection() as conn:
            query = "SELECT * FROM categories_v2"
            params = []
            
            if active_only:
                query += " WHERE is_active = 1"
            
            query += " ORDER BY priority_level DESC, name"
            
            cursor = conn.execute(query, params)
            return [Category(**dict(row)) for row in cursor.fetchall()]
    
    def get_category_by_slug(self, slug: str) -> Optional[Category]:
        """Get category by slug"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM categories_v2 WHERE slug = ?",
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

# Global database service instance
db_v2 = DatabaseServiceV2()
