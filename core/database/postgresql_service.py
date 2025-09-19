"""
PostgreSQL database service for production
"""
import os
import asyncio
import asyncpg
import logging
import threading
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class Partner:
    id: Optional[int]
    tg_user_id: int
    display_name: Optional[str]
    phone: Optional[str] = None
    email: Optional[str] = None
    is_verified: bool = False
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class Card:
    id: Optional[int]
    partner_id: int
    category_id: int
    title: str
    description: Optional[str] = None
    address: Optional[str] = None
    contact: Optional[str] = None
    discount_text: Optional[str] = None
    status: str = 'pending'
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class PostgreSQLService:
    """PostgreSQL database service"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self._pool = None
        self._lock = threading.Lock()
    
    async def init_pool(self):
        """Initialize connection pool"""
        if not self._pool:
            self._pool = await asyncpg.create_pool(self.database_url)
            logger.info("✅ PostgreSQL connection pool created")
    
    async def close_pool(self):
        """Close connection pool"""
        if self._pool:
            await self._pool.close()
            self._pool = None
            logger.info("✅ PostgreSQL connection pool closed")
    
    async def get_pool(self):
        """Get connection pool"""
        if not self._pool:
            await self.init_pool()
        return self._pool
    
    def _run_async(self, coro):
        """Run async coroutine in sync context"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're in an async context, run in separate thread
                result = [None]
                exception = [None]
                
                def target():
                    try:
                        result[0] = asyncio.run(coro)
                    except Exception as e:
                        exception[0] = e
                
                thread = threading.Thread(target=target)
                thread.start()
                thread.join()
                
                if exception[0]:
                    raise exception[0]
                return result[0]
            else:
                return loop.run_until_complete(coro)
        except RuntimeError:
            return asyncio.run(coro)
    
    # Partner methods
    async def get_partner_by_tg_id(self, tg_user_id: int) -> Optional[Partner]:
        """Get partner by Telegram user ID"""
        pool = await self.get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM partners_v2 WHERE tg_user_id = $1",
                tg_user_id
            )
            if row:
                return Partner(
                    id=row['id'],
                    tg_user_id=row['tg_user_id'],
                    display_name=row['display_name'],
                    phone=row['phone'],
                    email=row['email'],
                    is_verified=row['is_verified'],
                    is_active=row['is_active'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                )
            return None
    
    async def create_partner(self, partner: Partner) -> int:
        """Create new partner, return ID"""
        pool = await self.get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO partners_v2 (tg_user_id, display_name, phone, email, is_verified, is_active)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id
                """,
                partner.tg_user_id, partner.display_name, partner.phone, 
                partner.email, partner.is_verified, partner.is_active
            )
            return row['id']
    
    async def get_or_create_partner(self, tg_user_id: int, display_name: str) -> Partner:
        """Get existing partner or create new one"""
        partner = await self.get_partner_by_tg_id(tg_user_id)
        if partner:
            return partner
        
        new_partner = Partner(
            id=None,
            tg_user_id=tg_user_id,
            display_name=display_name,
            is_verified=False,
            is_active=True
        )
        
        partner_id = await self.create_partner(new_partner)
        new_partner.id = partner_id
        return new_partner
    
    # Card methods
    async def create_card(self, card: Card) -> int:
        """Create new card, return ID"""
        pool = await self.get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO cards_v2 (partner_id, category_id, title, description, address, contact, discount_text, status)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING id
                """,
                card.partner_id, card.category_id, card.title, card.description,
                card.address, card.contact, card.discount_text, card.status
            )
            return row['id']
    
    async def get_cards_by_category(self, category_slug: str, status: str = 'approved', limit: int = 50) -> List[Dict]:
        """Get cards by category with pagination"""
        pool = await self.get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT c.*, cat.name as category_name, cat.emoji as category_emoji,
                       p.display_name as partner_name,
                       COALESCE(COUNT(cp.id), 0) as photos_count
                FROM cards_v2 c
                JOIN categories_v2 cat ON c.category_id = cat.id
                JOIN partners_v2 p ON c.partner_id = p.id
                LEFT JOIN card_photos cp ON cp.card_id = c.id
                WHERE cat.slug = $1 AND c.status = $2 AND cat.is_active = true
                GROUP BY c.id
                ORDER BY c.priority_level DESC, c.created_at DESC
                LIMIT $3
                """,
                category_slug, status, limit
            )
            
            return [dict(row) for row in rows]
    
    async def get_categories(self) -> List[Dict]:
        """Get all active categories"""
        pool = await self.get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM categories_v2 WHERE is_active = true ORDER BY priority_level DESC, name"
            )
            return [dict(row) for row in rows]
    
    async def get_cards_count(self) -> int:
        """Get total number of cards"""
        pool = await self.get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT COUNT(*) FROM cards_v2")
            return row[0]
    
    async def get_partners_count(self) -> int:
        """Get total number of partners"""
        pool = await self.get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT COUNT(*) FROM partners_v2")
            return row[0]
    
    # Synchronous methods for compatibility
    def get_categories_sync(self) -> List[Dict]:
        """Get all active categories (sync)"""
        return self._run_async(self.get_categories())
    
    def get_cards_by_category_sync(self, category_slug: str, status: str = 'approved', limit: int = 50) -> List[Dict]:
        """Get cards by category (sync)"""
        return self._run_async(self.get_cards_by_category(category_slug, status, limit))
    
    def get_partner_by_tg_id_sync(self, tg_user_id: int) -> Optional[Partner]:
        """Get partner by Telegram user ID (sync)"""
        return self._run_async(self.get_partner_by_tg_id(tg_user_id))
    
    def create_partner_sync(self, partner: Partner) -> int:
        """Create new partner (sync)"""
        return self._run_async(self.create_partner(partner))
    
    def get_or_create_partner_sync(self, tg_user_id: int, display_name: str) -> Partner:
        """Get existing partner or create new one (sync)"""
        return self._run_async(self.get_or_create_partner(tg_user_id, display_name))
    
    def create_card_sync(self, card: Card) -> int:
        """Create new card (sync)"""
        return self._run_async(self.create_card(card))
    
    def get_cards_count_sync(self) -> int:
        """Get total number of cards (sync)"""
        return self._run_async(self.get_cards_count())
    
    def get_partners_count_sync(self) -> int:
        """Get total number of partners (sync)"""
        return self._run_async(self.get_partners_count())
    
    # User methods
    async def get_or_create_user(self, telegram_id: int, username: str = None, first_name: str = None, last_name: str = None, language_code: str = 'ru') -> Dict[str, Any]:
        """
        Get existing user or create new one with Welcome bonus.
        
        Args:
            telegram_id: Telegram user ID
            username: Telegram username
            first_name: User's first name
            last_name: User's last name
            language_code: User's language preference
            
        Returns:
            dict: User information including points balance
        """
        pool = await self.get_pool()
        async with pool.acquire() as conn:
            # Check if user exists
            row = await conn.fetchrow(
                "SELECT * FROM users WHERE telegram_id = $1",
                telegram_id
            )
            
            if row:
                # User exists, return existing data
                logger.info(f"Existing user found: {telegram_id}")
                return {
                    'telegram_id': row['telegram_id'],
                    'username': row.get('username'),
                    'first_name': row.get('first_name'),
                    'last_name': row.get('last_name'),
                    'language_code': row.get('language_code', 'ru'),
                    'points_balance': row.get('points_balance', 0),
                    'created_at': row.get('created_at'),
                    'is_new_user': False
                }
            
            # Create new user with Welcome bonus
            welcome_bonus = 167  # Welcome bonus points
            row = await conn.fetchrow("""
                INSERT INTO users (
                    telegram_id, username, first_name, last_name, 
                    language_code, points_balance, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING *
            """, (
                telegram_id, username, first_name, last_name,
                language_code, welcome_bonus, datetime.now(), datetime.now()
            ))
            
            # Add welcome bonus to points history
            await conn.execute("""
                INSERT INTO points_history (
                    user_id, change_amount, reason, transaction_type, created_at
                ) VALUES ($1, $2, $3, $4, $5)
            """, (
                telegram_id, welcome_bonus, "Welcome бонус при регистрации", "welcome_bonus", datetime.now()
            ))
            
            logger.info(f"New user created with Welcome bonus: {telegram_id}, bonus: {welcome_bonus} points")
            
            return {
                'telegram_id': telegram_id,
                'username': username,
                'first_name': first_name,
                'last_name': last_name,
                'language_code': language_code,
                'points_balance': welcome_bonus,
                'created_at': row['created_at'],
                'is_new_user': True
            }
    
    def get_or_create_user_sync(self, telegram_id: int, username: str = None, first_name: str = None, last_name: str = None, language_code: str = 'ru') -> Dict[str, Any]:
        """Get existing user or create new one with Welcome bonus (sync)"""
        return self._run_async(self.get_or_create_user(telegram_id, username, first_name, last_name, language_code))
    
    async def get_partners_by_status(self, status: str) -> List[Partner]:
        """Get partners by status"""
        pool = await self.get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM partners_v2 WHERE status = $1 ORDER BY created_at DESC",
                status
            )
            return [
                Partner(
                    id=row['id'],
                    tg_user_id=row['tg_user_id'],
                    display_name=row['display_name'],
                    phone=row['phone'],
                    email=row['email'],
                    is_verified=row['is_verified'],
                    is_active=row['is_active'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                ) for row in rows
            ]
    
    def get_partners_by_status_sync(self, status: str) -> List[Partner]:
        """Get partners by status (sync)"""
        return self._run_async(self.get_partners_by_status(status))

# Global instance
_postgresql_service = None

def get_postgresql_service() -> PostgreSQLService:
    """Get global PostgreSQL service instance"""
    global _postgresql_service
    if _postgresql_service is None:
        database_url = os.getenv('DATABASE_URL', '')
        if not database_url.startswith('postgresql://'):
            raise ValueError("DATABASE_URL must be a PostgreSQL connection string")
        _postgresql_service = PostgreSQLService(database_url)
    return _postgresql_service
