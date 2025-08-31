"""
Service layer for user cabinet functionality.
Handles all business logic related to user profile, balance, and level management.
"""
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from ..database.db_v2 import get_db
from ..database.models import User, LoyaltyPoints, Transaction
from ..utils.logger import get_logger

logger = get_logger(__name__)

class UserCabinetService:
    """Service class for user cabinet operations."""
    
    def __init__(self, db_session: Optional[Session] = None):
        """Initialize with optional database session (creates new if not provided)."""
        self.db = db_session if db_session else next(get_db())
    
    async def get_user_balance(self, user_id: int) -> int:
        """
        Get current user balance.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            int: Current balance in points
        """
        try:
            user = self.db.query(User).filter(User.telegram_id == user_id).first()
            return user.balance if user else 0
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
            user = self.db.query(User).filter(User.telegram_id == user_id).first()
            if not user:
                return {}
                
            return {
                "telegram_id": user.telegram_id,
                "username": user.username,
                "full_name": user.full_name,
                "balance": user.balance,
                "level": await self.get_user_level(user_id),
                "registration_date": user.created_at.strftime("%d.%m.%Y"),
                "is_partner": user.is_partner,
                "referral_code": user.referral_code
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
            user = self.db.query(User).filter(User.telegram_id == user_id).first()
            if not user:
                return {"transactions": [], "total": 0, "limit": limit, "offset": offset}
            
            # Get total count for pagination
            total = self.db.query(Transaction).filter(Transaction.user_id == user.id).count()
            
            # Get paginated transactions
            transactions = (
                self.db.query(Transaction)
                .filter(Transaction.user_id == user.id)
                .order_by(Transaction.created_at.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )
            
            return {
                "transactions": [
                    {
                        "id": txn.id,
                        "amount": txn.amount,
                        "type": txn.transaction_type,
                        "description": txn.description,
                        "created_at": txn.created_at.strftime("%d.%m.%Y %H:%M"),
                        "status": txn.status
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
