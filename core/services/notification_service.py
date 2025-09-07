"""
Notification service module for handling user notifications.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncpg
import os
from core.utils.logger import get_logger

logger = get_logger(__name__)


class NotificationService:
    """Service for user notifications."""
    
    def __init__(self):
        """Initialize with database connection."""
        self.database_url = os.getenv("DATABASE_URL", "")
    
    async def get_connection(self) -> asyncpg.Connection:
        """Get database connection."""
        return await asyncpg.connect(self.database_url)
    
    async def add_notification(
        self, 
        user_id: int, 
        message: str, 
        notification_type: str = "system"
    ) -> bool:
        """
        Add notification to user.
        
        Args:
            user_id: Telegram user ID
            message: Notification message
            notification_type: Type of notification
            
        Returns:
            bool: Success status
        """
        try:
            conn = await self.get_connection()
            try:
                await conn.execute("""
                    INSERT INTO user_notifications 
                    (user_id, message, notification_type, created_at)
                    VALUES ($1, $2, $3, NOW())
                """, user_id, message, notification_type)
                
                logger.info(f"Notification added for user {user_id}: {message[:50]}...")
                return True
            finally:
                await conn.close()
        except Exception as e:
            logger.error(f"Error adding notification for user {user_id}: {str(e)}")
            return False
    
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
            conn = await self.get_connection()
            try:
                query = """
                    SELECT id, message, notification_type, is_read, created_at
                    FROM user_notifications 
                    WHERE user_id = $1
                """
                params = [user_id]
                
                if unread_only:
                    query += " AND is_read = FALSE"
                
                query += " ORDER BY created_at DESC LIMIT $2 OFFSET $3"
                params.extend([limit, offset])
                
                notifications = await conn.fetch(query, *params)
                
                return [
                    {
                        'id': notif['id'],
                        'message': notif['message'],
                        'notification_type': notif['notification_type'],
                        'is_read': notif['is_read'],
                        'created_at': notif['created_at']
                    }
                    for notif in notifications
                ]
            finally:
                await conn.close()
        except Exception as e:
            logger.error(f"Error getting notifications for user {user_id}: {str(e)}")
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
            conn = await self.get_connection()
            try:
                result = await conn.execute("""
                    UPDATE user_notifications 
                    SET is_read = TRUE 
                    WHERE id = $1 AND user_id = $2
                """, notification_id, user_id)
                
                return result != "UPDATE 0"
            finally:
                await conn.close()
        except Exception as e:
            logger.error(f"Error marking notification {notification_id} as read: {str(e)}")
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
            conn = await self.get_connection()
            try:
                await conn.execute("""
                    UPDATE user_notifications 
                    SET is_read = TRUE 
                    WHERE user_id = $1 AND is_read = FALSE
                """, user_id)
                
                logger.info(f"All notifications marked as read for user {user_id}")
                return True
            finally:
                await conn.close()
        except Exception as e:
            logger.error(f"Error marking all notifications as read for user {user_id}: {str(e)}")
            return False
    
    async def get_unread_count(self, user_id: int) -> int:
        """
        Get count of unread notifications.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            int: Count of unread notifications
        """
        try:
            conn = await self.get_connection()
            try:
                count = await conn.fetchval("""
                    SELECT COUNT(*) FROM user_notifications 
                    WHERE user_id = $1 AND is_read = FALSE
                """, user_id)
                
                return count or 0
            finally:
                await conn.close()
        except Exception as e:
            logger.error(f"Error getting unread count for user {user_id}: {str(e)}")
            return 0
    
    async def delete_old_notifications(self, days_old: int = 30) -> int:
        """
        Delete old notifications.
        
        Args:
            days_old: Delete notifications older than this many days
            
        Returns:
            int: Number of deleted notifications
        """
        try:
            conn = await self.get_connection()
            try:
                result = await conn.execute("""
                    DELETE FROM user_notifications 
                    WHERE created_at < NOW() - INTERVAL '%s days'
                """, days_old)
                
                deleted_count = int(result.split()[-1]) if result.startswith("DELETE") else 0
                logger.info(f"Deleted {deleted_count} old notifications")
                return deleted_count
            finally:
                await conn.close()
        except Exception as e:
            logger.error(f"Error deleting old notifications: {str(e)}")
            return 0


# Create singleton instance
notification_service = NotificationService()


# Export functions
__all__ = [
    'NotificationService',
    'notification_service'
]