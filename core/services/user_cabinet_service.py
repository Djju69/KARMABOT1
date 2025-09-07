"""
Service layer for user cabinet functionality.
Handles all business logic related to user profile, balance, and level management.
"""
from typing import Optional, Dict, Any
import os
import asyncpg
import asyncio

from core.utils.logger import get_logger

logger = get_logger(__name__)

class UserCabinetService:
    """Service class for user cabinet operations."""
    
    def __init__(self):
        """Initialize with database connection."""
        self.database_url = os.getenv("DATABASE_URL", "")
    
    async def get_connection(self) -> asyncpg.Connection:
        """Get database connection."""
        return await asyncpg.connect(self.database_url)
    
    async def get_user_balance(self, user_id: int) -> int:
        """
        Get current user balance.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            int: Current balance in points
        """
        try:
            conn = await self.get_connection()
            try:
                result = await conn.fetchrow(
                    "SELECT karma_points FROM users WHERE telegram_id = $1",
                    user_id
                )
                return result['karma_points'] if result else 0
            finally:
                await conn.close()
        except Exception as e:
            logger.error(f"Error getting balance for user {user_id}: {str(e)}")
            return 0
    
    async def get_user_level(self, user_id: int) -> str:
        """
        Determine user level based on their balance.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            str: User level (Bronze, Silver, Gold)
        """
        balance = await self.get_user_balance(user_id)
        if balance >= 1000:
            return "Gold"
        elif balance >= 500:
            return "Silver"
        return "Bronze"
    
    async def get_user_profile(self, user_id: int) -> Dict[str, Any]:
        """
        Get complete user profile information.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            dict: User profile data
        """
        try:
            conn = await self.get_connection()
            try:
                user = await conn.fetchrow(
                    "SELECT * FROM users WHERE telegram_id = $1",
                    user_id
                )
                if not user:
                    return {}
                
                user_dict = dict(user)
                return {
                    "telegram_id": user_dict.get('telegram_id'),
                    "username": user_dict.get('username'),
                    "full_name": f"{user_dict.get('first_name', '')} {user_dict.get('last_name', '')}".strip(),
                    "balance": user_dict.get('karma_points', 0),
                    "level": await self.get_user_level(user_id),
                    "registration_date": user_dict.get('created_at', 'Неизвестно'),
                    "language": user_dict.get('language_code', 'ru')
                }
            finally:
                await conn.close()
        except Exception as e:
            logger.error(f"Error getting profile for user {user_id}: {str(e)}")
            return {}
    
    async def get_transaction_history(
        self, 
        user_id: int, 
        limit: int = 10, 
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get user's transaction history with pagination.
        
        Args:
            user_id: Telegram user ID
            limit: Number of transactions to return
            offset: Number of transactions to skip
            
        Returns:
            dict: Transaction history with pagination info
        """
        try:
            conn = await self.get_connection()
            try:
                # Check if user exists
                user = await conn.fetchrow(
                    "SELECT id FROM users WHERE telegram_id = $1",
                    user_id
                )
                if not user:
                    return {"transactions": [], "total": 0, "limit": limit, "offset": offset}
                
                # Get total count for pagination
                total = await conn.fetchval(
                    "SELECT COUNT(*) FROM karma_transactions WHERE user_id = $1",
                    user['id']
                )
                
                # Get paginated transactions
                transactions = await conn.fetch(
                    """
                    SELECT * FROM karma_transactions 
                    WHERE user_id = $1 
                    ORDER BY created_at DESC 
                    LIMIT $2 OFFSET $3
                    """,
                    user['id'], limit, offset
                )
                
                return {
                    "transactions": [
                        {
                            "id": txn['id'],
                            "amount": txn['amount'],
                            "reason": txn['reason'],
                            "created_at": txn['created_at']
                        } for txn in transactions
                    ],
                    "total": total,
                    "limit": limit,
                    "offset": offset
                }
            finally:
                await conn.close()
            
        except Exception as e:
            logger.error(f"Error getting transaction history for user {user_id}: {str(e)}")
            return {"transactions": [], "total": 0, "limit": limit, "offset": offset}

# Create a singleton instance for easy import
user_cabinet_service = UserCabinetService()
