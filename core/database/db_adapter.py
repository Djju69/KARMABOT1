"""
Database adapter that switches between SQLite and PostgreSQL
"""
import os
import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

# Import both services
from .db_v2 import DatabaseServiceV2, Partner as SQLitePartner, Card as SQLiteCard
from .postgresql_service import PostgreSQLService, Partner as PostgreSQLPartner, Card as PostgreSQLCard

class DatabaseAdapter:
    """Adapter that switches between SQLite and PostgreSQL based on environment"""
    
    def __init__(self):
        database_url = os.getenv('DATABASE_URL', '')
        # Check if we're in production environment
        is_production = os.getenv('APP_ENV') == 'production' or os.getenv('RAILWAY_ENVIRONMENT') == 'production'
        
        if database_url.startswith('postgresql://') and is_production:
            self.use_postgresql = True
            self.postgresql_service = PostgreSQLService(database_url)
            logger.info("🗄️ Используется PostgreSQL адаптер (production)")
        else:
            self.use_postgresql = False
            self.sqlite_service = DatabaseServiceV2()
            logger.info("🗄️ Используется SQLite адаптер (development)")
    
    async def init_postgresql(self):
        """Initialize PostgreSQL connection pool"""
        if self.use_postgresql:
            await self.postgresql_service.init_pool()
    
    async def close_postgresql(self):
        """Close PostgreSQL connection pool"""
        if self.use_postgresql:
            await self.postgresql_service.close_pool()
    
    # Partner methods
    def get_partner_by_tg_id(self, tg_user_id: int):
        """Get partner by Telegram user ID"""
        if self.use_postgresql:
            return self.postgresql_service.get_partner_by_tg_id_sync(tg_user_id)
        else:
            return self.sqlite_service.get_partner_by_tg_id(tg_user_id)
    
    def create_partner(self, partner):
        """Create new partner"""
        if self.use_postgresql:
            return self.postgresql_service.create_partner_sync(partner)
        else:
            return self.sqlite_service.create_partner(partner)
    
    def get_or_create_partner(self, tg_user_id: int, display_name: str):
        """Get existing partner or create new one"""
        if self.use_postgresql:
            return self.postgresql_service.get_or_create_partner_sync(tg_user_id, display_name)
        else:
            return self.sqlite_service.get_or_create_partner(tg_user_id, display_name)
    
    # Card methods
    def create_card(self, card):
        """Create new card"""
        if self.use_postgresql:
            return self.postgresql_service.create_card_sync(card)
        else:
            return self.sqlite_service.create_card(card)
    
    async def get_cards_by_category(self, category_slug: str, status: str = 'approved', limit: int = 50, sub_slug: str = None):
        """Get cards by category"""
        if self.use_postgresql:
            return await self.postgresql_service.get_cards_by_category(category_slug, status, limit, sub_slug)
        else:
            return self.sqlite_service.get_cards_by_category(category_slug, status, limit)
    
    def get_categories(self):
        """Get all categories"""
        if self.use_postgresql:
            return self.postgresql_service.get_categories_sync()
        else:
            return self.sqlite_service.get_categories()
    
    def get_cards_count(self):
        """Get total number of cards"""
        if self.use_postgresql:
            return self.postgresql_service.get_cards_count_sync()
        else:
            return self.sqlite_service.get_cards_count()
    
    def get_partners_count(self):
        """Get total number of partners"""
        if self.use_postgresql:
            return self.postgresql_service.get_partners_count_sync()
        else:
            return self.sqlite_service.get_partners_count()
    
    def get_partners_by_status(self, status: str):
        """Get partners by status"""
        if self.use_postgresql:
            return self.postgresql_service.get_partners_by_status_sync(status)
        else:
            return self.sqlite_service.get_partners_by_status(status)
    
    def execute_query(self, query: str, params: tuple = ()):
        """Execute a query and return results"""
        if self.use_postgresql:
            return self.postgresql_service.execute_query_sync(query, params)
        else:
            return self.sqlite_service.execute_query(query, params)
    
    def fetch_all(self, query: str, params: tuple = ()):
        """Fetch all results from a query"""
        if self.use_postgresql:
            return self.postgresql_service.fetch_all_sync(query, params)
        else:
            return self.sqlite_service.fetch_all(query, params)
    
    def fetch_one(self, query: str, params: tuple = ()):
        """Fetch one result from query"""
        if self.use_postgresql:
            return self.postgresql_service.fetch_one_sync(query, params)
        else:
            return self.sqlite_service.fetch_one(query, params)
    
    def execute(self, query: str, params: tuple = ()):
        """Execute a query without returning results"""
        if self.use_postgresql:
            return self.postgresql_service.execute_sync(query, params)
        else:
            return self.sqlite_service.execute(query, params)
    
    async def get_card_photos(self, card_id: int):
        """Get photos for a card (унифицированная структура)"""
        if self.use_postgresql:
            return await self.postgresql_service.get_card_photos(card_id)
        else:
            return self.sqlite_service.get_card_photos(card_id)
    
    async def add_to_favorites(self, user_id: int, card_id: int) -> bool:
        """Add card to user favorites"""
        if self.use_postgresql:
            return await self.postgresql_service.add_to_favorites(user_id, card_id)
        else:
            return self.sqlite_service.add_to_favorites(user_id, card_id)
    
    async def remove_from_favorites(self, user_id: int, card_id: int) -> bool:
        """Remove card from user favorites"""
        if self.use_postgresql:
            return await self.postgresql_service.remove_from_favorites(user_id, card_id)
        else:
            return self.sqlite_service.remove_from_favorites(user_id, card_id)
    
    async def is_favorite(self, user_id: int, card_id: int) -> bool:
        """Check if card is in user favorites"""
        if self.use_postgresql:
            return await self.postgresql_service.is_favorite(user_id, card_id)
        else:
            return self.sqlite_service.is_favorite(user_id, card_id)
    
    async def get_card_by_id(self, card_id: int):
        """Get card by ID"""
        if self.use_postgresql:
            return await self.postgresql_service.get_card_by_id(card_id)
        else:
            return self.sqlite_service.get_card_by_id(card_id)

# Global instance
db_v2 = DatabaseAdapter()
