"""
Service layer for user cabinet functionality.
Handles all business logic related to user profile, balance, and level management.
"""
from typing import Optional, Dict, Any
import sqlite3
from pathlib import Path

from core.utils.logger import get_logger

logger = get_logger(__name__)

class UserCabinetService:
    """Service class for user cabinet operations."""
    
    def __init__(self):
        """Initialize with database connection."""
        self.db_path = Path(__file__).parent.parent / "database" / "data.db"
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    async def get_user_balance(self, user_id: int) -> int:
        """
        Get current user balance.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            int: Current balance in points
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT balance FROM users WHERE user_id = ?",
                    (user_id,)
                )
                result = cursor.fetchone()
                return result['balance'] if result else 0
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
            with self.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT * FROM users WHERE user_id = ?",
                    (user_id,)
                )
                user = cursor.fetchone()
                if not user:
                    return {}
                
                user_dict = dict(user)
                return {
                    "telegram_id": user_dict.get('user_id'),
                    "username": user_dict.get('username'),
                    "full_name": user_dict.get('full_name'),
                    "balance": user_dict.get('balance', 0),
                    "level": await self.get_user_level(user_id),
                    "registration_date": user_dict.get('created_at', 'Неизвестно'),
                    "is_partner": user_dict.get('is_partner', False),
                    "referral_code": user_dict.get('referral_code'),
                    "language": user_dict.get('language', 'ru')
                }
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
            with self.get_connection() as conn:
                # Check if user exists
                cursor = conn.execute(
                    "SELECT id FROM users WHERE user_id = ?",
                    (user_id,)
                )
                user = cursor.fetchone()
                if not user:
                    return {"transactions": [], "total": 0, "limit": limit, "offset": offset}
                
                # Get total count for pagination
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM transactions WHERE user_id = ?",
                    (user['id'],)
                )
                total = cursor.fetchone()[0]
                
                # Get paginated transactions
                cursor = conn.execute(
                    """
                    SELECT * FROM transactions 
                    WHERE user_id = ? 
                    ORDER BY created_at DESC 
                    LIMIT ? OFFSET ?
                    """,
                    (user['id'], limit, offset)
                )
                transactions = cursor.fetchall()
                
                return {
                    "transactions": [
                        {
                            "id": txn['id'],
                            "amount": txn['amount'],
                            "type": txn['transaction_type'],
                            "description": txn['description'],
                            "created_at": txn['created_at'],
                            "status": txn['status']
                        } for txn in transactions
                    ],
                    "total": total,
                    "limit": limit,
                    "offset": offset
                }
            
        except Exception as e:
            logger.error(f"Error getting transaction history for user {user_id}: {str(e)}")
            return {"transactions": [], "total": 0, "limit": limit, "offset": offset}

# Create a singleton instance for easy import
user_cabinet_service = UserCabinetService()
