"""
Service layer for user cabinet functionality.
Handles all business logic related to user profile, balance, and level management.
"""
from typing import Optional, Dict, Any, List
import os
import asyncpg
import asyncio
from datetime import datetime

from core.utils.logger import get_logger
from core.services.card_service import card_service
from core.services.notification_service import notification_service
from core.services.achievement_service import achievement_service
from core.services.user_service import karma_service

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
                if not result:
                    # Создаем пользователя если его нет
                    await conn.execute("""
                        INSERT INTO users (telegram_id, karma_points, role, level, created_at, updated_at)
                        VALUES ($1, 0, 'user', 1, NOW(), NOW())
                        ON CONFLICT (telegram_id) DO NOTHING
                    """, user_id)
                    return 0
                return result['karma_points']
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
        Get complete user profile information according to TZ.
        
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
                    # Создаем пользователя если его нет
                    await conn.execute("""
                        INSERT INTO users (telegram_id, karma_points, role, level, created_at, updated_at)
                        VALUES ($1, 0, 'user', 1, NOW(), NOW())
                        ON CONFLICT (telegram_id) DO NOTHING
                    """, user_id)
                    
                    # Получаем созданного пользователя
                    user = await conn.fetchrow(
                        "SELECT * FROM users WHERE telegram_id = $1",
                        user_id
                    )
                    if not user:
                        return {}
                
                user_dict = dict(user)
                
                # Get karma and level information
                karma_points = user_dict.get('karma_points', 0)
                level = karma_service.calculate_level(karma_points)
                level_progress = await karma_service.get_level_progress(user_id)
                
                # Get cards count
                cards_count = await card_service.get_user_cards(user_id)
                
                # Get unread notifications count
                unread_notifications = await notification_service.get_unread_count(user_id)
                
                # Get achievements count
                achievement_stats = await achievement_service.get_achievement_stats(user_id)
                
                return {
                    "telegram_id": user_dict.get('telegram_id'),
                    "username": user_dict.get('username'),
                    "full_name": f"{user_dict.get('first_name', '')} {user_dict.get('last_name', '')}".strip(),
                    "karma_points": karma_points,
                    "level": level,
                    "level_progress": level_progress,
                    "registration_date": user_dict.get('created_at', 'Неизвестно'),
                    "language": user_dict.get('language_code', 'ru'),
                    "role": user_dict.get('role', 'user'),
                    "cards_count": len(cards_count),
                    "unread_notifications": unread_notifications,
                    "achievements_count": achievement_stats.get('total_count', 0),
                    "is_banned": user_dict.get('is_banned', False),
                    "ban_reason": user_dict.get('ban_reason'),
                    "last_activity": user_dict.get('last_activity')
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
    
    async def get_user_cards(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get user's bound cards.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            list: List of user's cards
        """
        try:
            return await card_service.get_user_cards(user_id)
        except Exception as e:
            logger.error(f"Error getting cards for user {user_id}: {str(e)}")
            return []
    
    async def get_user_notifications(
        self, 
        user_id: int, 
        limit: int = 10, 
        offset: int = 0,
        unread_only: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get user notifications.
        
        Args:
            user_id: Telegram user ID
            limit: Number of notifications to return
            offset: Offset for pagination
            unread_only: Return only unread notifications
            
        Returns:
            list: List of notifications
        """
        try:
            return await notification_service.get_user_notifications(
                user_id, limit, offset, unread_only
            )
        except Exception as e:
            logger.error(f"Error getting notifications for user {user_id}: {str(e)}")
            return []
    
    async def get_user_achievements(
        self, 
        user_id: int, 
        limit: int = 10, 
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get user achievements.
        
        Args:
            user_id: Telegram user ID
            limit: Number of achievements to return
            offset: Offset for pagination
            
        Returns:
            list: List of achievements
        """
        try:
            return await achievement_service.get_user_achievements(
                user_id, limit, offset
            )
        except Exception as e:
            logger.error(f"Error getting achievements for user {user_id}: {str(e)}")
            return []
    
    async def mark_notification_as_read(self, notification_id: int, user_id: int) -> bool:
        """
        Mark notification as read.
        
        Args:
            notification_id: Notification ID
            user_id: Telegram user ID
            
        Returns:
            bool: Success status
        """
        try:
            return await notification_service.mark_notification_as_read(
                notification_id, user_id
            )
        except Exception as e:
            logger.error(f"Error marking notification as read: {str(e)}")
            return False
    
    async def mark_all_notifications_as_read(self, user_id: int) -> bool:
        """
        Mark all user notifications as read.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            bool: Success status
        """
        try:
            return await notification_service.mark_all_notifications_as_read(user_id)
        except Exception as e:
            logger.error(f"Error marking all notifications as read: {str(e)}")
            return False
    
    async def get_cabinet_summary(self, user_id: int) -> Dict[str, Any]:
        """
        Get complete cabinet summary for user.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            dict: Complete cabinet summary
        """
        try:
            # Get basic profile
            profile = await self.get_user_profile(user_id)
            if not profile:
                return {}
            
            # Get recent notifications (5 latest)
            notifications = await self.get_user_notifications(user_id, limit=5)
            
            # Get recent achievements (5 latest)
            achievements = await self.get_user_achievements(user_id, limit=5)
            
            # Get recent karma history (5 latest)
            karma_history = await karma_service.get_karma_history(user_id, limit=5)
            
            # Get user cards
            cards = await self.get_user_cards(user_id)
            
            return {
                'profile': profile,
                'notifications': notifications,
                'achievements': achievements,
                'karma_history': karma_history,
                'cards': cards,
                'summary': {
                    'total_cards': len(cards),
                    'unread_notifications': profile.get('unread_notifications', 0),
                    'total_achievements': profile.get('achievements_count', 0),
                    'current_level': profile.get('level', 1),
                    'karma_points': profile.get('karma_points', 0)
                }
            }
        except Exception as e:
            logger.error(f"Error getting cabinet summary for user {user_id}: {str(e)}")
            return {}

# Create a singleton instance for easy import
user_cabinet_service = UserCabinetService()
