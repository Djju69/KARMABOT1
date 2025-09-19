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
    
    def get_cards_by_category(self, category_slug: str, status: str = 'approved', limit: int = 50):
        """Get cards by category"""
        if self.use_postgresql:
            return self.postgresql_service.get_cards_by_category_sync(category_slug, status, limit)
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

# Global instance
db_v2 = DatabaseAdapter()
