"""
Admin service module for handling administrative operations.
Including user search, karma management, ban/unban, and admin logs.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncpg
import os
from core.utils.logger import get_logger
from core.services.user_service import karma_service
from core.services.notification_service import notification_service

logger = get_logger(__name__)


class AdminService:
    """Service for administrative operations."""
    
    def __init__(self):
        """Initialize with database connection."""
        self.database_url = os.getenv("DATABASE_URL", "")
    
    async def get_connection(self) -> asyncpg.Connection:
        """Get database connection."""
        return await asyncpg.connect(self.database_url)
    
    async def search_users(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search users by username, first_name, last_name, or telegram_id.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            list: List of matching users
        """
        try:
            conn = await self.get_connection()
            try:
                # Try to parse as telegram_id first
                try:
                    telegram_id = int(query)
                    users = await conn.fetch("""
                        SELECT telegram_id, username, first_name, last_name, 
                               karma_points, level, role, is_banned, created_at
                        FROM users 
                        WHERE telegram_id = $1
                        LIMIT $2
                    """, telegram_id, limit)
                except ValueError:
                    # Search by text fields
                    search_pattern = f"%{query}%"
                    users = await conn.fetch("""
                        SELECT telegram_id, username, first_name, last_name, 
                               karma_points, level, role, is_banned, created_at
                        FROM users 
                        WHERE username ILIKE $1 
                           OR first_name ILIKE $1 
                           OR last_name ILIKE $1
                        ORDER BY karma_points DESC
                        LIMIT $2
                    """, search_pattern, limit)
                
                result = []
                for user in users:
                    result.append({
                        'telegram_id': user['telegram_id'],
                        'username': user['username'],
                        'first_name': user['first_name'],
                        'last_name': user['last_name'],
                        'full_name': f"{user['first_name'] or ''} {user['last_name'] or ''}".strip(),
                        'karma_points': user['karma_points'],
                        'level': user['level'],
                        'role': user['role'],
                        'is_banned': user['is_banned'],
                        'created_at': user['created_at']
                    })
                
                return result
            finally:
                await conn.close()
        except Exception as e:
            logger.error(f"Error searching users: {str(e)}")
            return []
    
    async def get_user_details(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get detailed user information for admin panel.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            dict: Detailed user information or None
        """
        try:
            conn = await self.get_connection()
            try:
                user = await conn.fetchrow("""
                    SELECT * FROM users WHERE telegram_id = $1
                """, user_id)
                
                if not user:
                    return None
                
                # Get user's cards
                cards = await conn.fetch("""
                    SELECT cb.*, cg.is_blocked, cg.is_deleted
                    FROM cards_binding cb
                    LEFT JOIN cards_generated cg ON cb.card_id = cg.card_id
                    WHERE cb.telegram_id = $1
                    ORDER BY cb.bound_at DESC
                """, user_id)
                
                # Get recent karma transactions
                karma_history = await conn.fetch("""
                    SELECT amount, reason, admin_id, created_at
                    FROM karma_transactions 
                    WHERE user_id = $1
                    ORDER BY created_at DESC
                    LIMIT 10
                """, user_id)
                
                # Get recent notifications
                notifications = await conn.fetch("""
                    SELECT message, notification_type, is_read, created_at
                    FROM user_notifications 
                    WHERE user_id = $1
                    ORDER BY created_at DESC
                    LIMIT 5
                """, user_id)
                
                # Get achievements
                achievements = await conn.fetch("""
                    SELECT achievement_type, achievement_data, earned_at
                    FROM user_achievements 
                    WHERE user_id = $1
                    ORDER BY earned_at DESC
                    LIMIT 10
                """, user_id)
                
                return {
                    'user': dict(user),
                    'cards': [dict(card) for card in cards],
                    'karma_history': [dict(txn) for txn in karma_history],
                    'notifications': [dict(notif) for notif in notifications],
                    'achievements': [dict(ach) for ach in achievements]
                }
            finally:
                await conn.close()
        except Exception as e:
            logger.error(f"Error getting user details for {user_id}: {str(e)}")
            return None
    
    async def modify_user_karma(
        self, 
        user_id: int, 
        amount: int, 
        reason: str, 
        admin_id: int
    ) -> Dict[str, Any]:
        """
        Modify user karma (add or subtract).
        
        Args:
            user_id: Target user ID
            amount: Amount to add (positive) or subtract (negative)
            reason: Reason for modification
            admin_id: Admin who made the change
            
        Returns:
            dict: Operation result
        """
        try:
            from core.settings import settings
            
            # Check admin karma limit
            if abs(amount) > settings.karma.admin_karma_limit:
                return {
                    'success': False,
                    'message': f'Превышен лимит изменения кармы ({settings.karma.admin_karma_limit})',
                    'error_code': 'limit_exceeded'
                }
            
            # Get current karma
            current_karma = await karma_service.get_user_karma(user_id)
            
            if amount > 0:
                success = await karma_service.add_karma(user_id, amount, reason, admin_id)
            else:
                success = await karma_service.subtract_karma(user_id, abs(amount), reason, admin_id)
            
            if success:
                new_karma = await karma_service.get_user_karma(user_id)
                
                # Log admin action
                await self.log_admin_action(
                    admin_id, 
                    'modify_karma', 
                    target_user_id=user_id,
                    details=f"Изменение кармы: {amount:+d}, причина: {reason}"
                )
                
                # Add notification to user
                await notification_service.add_notification(
                    user_id,
                    f"🔧 Администратор изменил вашу карму на {amount:+d}. Причина: {reason}",
                    "admin_action"
                )
                
                return {
                    'success': True,
                    'message': f'Карма пользователя изменена на {amount:+d}',
                    'old_karma': current_karma,
                    'new_karma': new_karma,
                    'change': amount
                }
            else:
                return {
                    'success': False,
                    'message': 'Ошибка при изменении кармы',
                    'error_code': 'modification_error'
                }
                
        except Exception as e:
            logger.error(f"Error modifying karma for user {user_id}: {str(e)}")
            return {
                'success': False,
                'message': f'Ошибка при изменении кармы: {str(e)}',
                'error_code': 'database_error'
            }
    
    async def ban_user(
        self, 
        user_id: int, 
        reason: str, 
        admin_id: int
    ) -> Dict[str, Any]:
        """
        Ban user according to TZ.
        
        Args:
            user_id: Target user ID
            reason: Ban reason
            admin_id: Admin who banned the user
            
        Returns:
            dict: Operation result
        """
        try:
            conn = await self.get_connection()
            try:
                # Check if user exists
                user = await conn.fetchrow(
                    "SELECT telegram_id, is_banned FROM users WHERE telegram_id = $1",
                    user_id
                )
                
                if not user:
                    return {
                        'success': False,
                        'message': 'Пользователь не найден',
                        'error_code': 'user_not_found'
                    }
                
                if user['is_banned']:
                    return {
                        'success': False,
                        'message': 'Пользователь уже заблокирован',
                        'error_code': 'already_banned'
                    }
                
                # Ban user
                await conn.execute("""
                    UPDATE users 
                    SET is_banned = TRUE, ban_reason = $1, banned_by = $2, banned_at = NOW()
                    WHERE telegram_id = $3
                """, reason, admin_id, user_id)
                
                # Log admin action
                await self.log_admin_action(
                    admin_id, 
                    'ban_user', 
                    target_user_id=user_id,
                    details=f"Блокировка пользователя, причина: {reason}"
                )
                
                # Add notification to user
                await notification_service.add_notification(
                    user_id,
                    f"🚫 Ваш аккаунт заблокирован. Причина: {reason}",
                    "ban"
                )
                
                logger.info(f"User {user_id} banned by admin {admin_id}")
                
                return {
                    'success': True,
                    'message': 'Пользователь заблокирован',
                    'reason': reason
                }
                
            finally:
                await conn.close()
        except Exception as e:
            logger.error(f"Error banning user {user_id}: {str(e)}")
            return {
                'success': False,
                'message': f'Ошибка при блокировке: {str(e)}',
                'error_code': 'ban_error'
            }
    
    async def unban_user(
        self, 
        user_id: int, 
        admin_id: int
    ) -> Dict[str, Any]:
        """
        Unban user according to TZ.
        
        Args:
            user_id: Target user ID
            admin_id: Admin who unbanned the user
            
        Returns:
            dict: Operation result
        """
        try:
            conn = await self.get_connection()
            try:
                # Check if user exists and is banned
                user = await conn.fetchrow(
                    "SELECT telegram_id, is_banned FROM users WHERE telegram_id = $1",
                    user_id
                )
                
                if not user:
                    return {
                        'success': False,
                        'message': 'Пользователь не найден',
                        'error_code': 'user_not_found'
                    }
                
                if not user['is_banned']:
                    return {
                        'success': False,
                        'message': 'Пользователь не заблокирован',
                        'error_code': 'not_banned'
                    }
                
                # Unban user
                await conn.execute("""
                    UPDATE users 
                    SET is_banned = FALSE, ban_reason = NULL, banned_by = NULL, banned_at = NULL
                    WHERE telegram_id = $1
                """, user_id)
                
                # Log admin action
                await self.log_admin_action(
                    admin_id, 
                    'unban_user', 
                    target_user_id=user_id,
                    details="Разблокировка пользователя"
                )
                
                # Add notification to user
                await notification_service.add_notification(
                    user_id,
                    "✅ Ваш аккаунт разблокирован!",
                    "unban"
                )
                
                logger.info(f"User {user_id} unbanned by admin {admin_id}")
                
                return {
                    'success': True,
                    'message': 'Пользователь разблокирован'
                }
                
            finally:
                await conn.close()
        except Exception as e:
            logger.error(f"Error unbanning user {user_id}: {str(e)}")
            return {
                'success': False,
                'message': f'Ошибка при разблокировке: {str(e)}',
                'error_code': 'unban_error'
            }
    
    async def log_admin_action(
        self, 
        admin_id: int, 
        action: str, 
        target_user_id: int = None,
        target_card_id: str = None,
        details: str = None
    ) -> bool:
        """
        Log admin action according to TZ.
        
        Args:
            admin_id: Admin who performed the action
            action: Action performed
            target_user_id: Target user ID (if applicable)
            target_card_id: Target card ID (if applicable)
            details: Additional details
            
        Returns:
            bool: Success status
        """
        try:
            conn = await self.get_connection()
            try:
                await conn.execute("""
                    INSERT INTO admin_logs 
                    (admin_id, action, target_user_id, target_card_id, details, created_at)
                    VALUES ($1, $2, $3, $4, $5, NOW())
                """, admin_id, action, target_user_id, target_card_id, details)
                
                logger.info(f"Admin action logged: {admin_id} -> {action}")
                return True
            finally:
                await conn.close()
        except Exception as e:
            logger.error(f"Error logging admin action: {str(e)}")
            return False
    
    async def get_admin_logs(
        self, 
        admin_id: int = None, 
        limit: int = 50, 
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get admin action logs.
        
        Args:
            admin_id: Filter by admin ID (optional)
            limit: Number of logs to return
            offset: Offset for pagination
            
        Returns:
            list: List of admin logs
        """
        try:
            conn = await self.get_connection()
            try:
                if admin_id:
                    logs = await conn.fetch("""
                        SELECT al.*, u.username, u.first_name, u.last_name
                        FROM admin_logs al
                        LEFT JOIN users u ON al.target_user_id = u.telegram_id
                        WHERE al.admin_id = $1
                        ORDER BY al.created_at DESC
                        LIMIT $2 OFFSET $3
                    """, admin_id, limit, offset)
                else:
                    logs = await conn.fetch("""
                        SELECT al.*, u.username, u.first_name, u.last_name
                        FROM admin_logs al
                        LEFT JOIN users u ON al.target_user_id = u.telegram_id
                        ORDER BY al.created_at DESC
                        LIMIT $1 OFFSET $2
                    """, limit, offset)
                
                result = []
                for log in logs:
                    result.append({
                        'id': log['id'],
                        'admin_id': log['admin_id'],
                        'action': log['action'],
                        'target_user_id': log['target_user_id'],
                        'target_card_id': log['target_card_id'],
                        'details': log['details'],
                        'created_at': log['created_at'],
                        'target_username': log['username'],
                        'target_full_name': f"{log['first_name'] or ''} {log['last_name'] or ''}".strip()
                    })
                
                return result
            finally:
                await conn.close()
        except Exception as e:
            logger.error(f"Error getting admin logs: {str(e)}")
            return []
    
    async def get_admin_stats(self) -> Dict[str, Any]:
        """
        Get admin panel statistics.
        
        Returns:
            dict: Admin statistics
        """
        try:
            conn = await self.get_connection()
            try:
                # Get total users
                total_users = await conn.fetchval("SELECT COUNT(*) FROM users")
                
                # Get banned users
                banned_users = await conn.fetchval("SELECT COUNT(*) FROM users WHERE is_banned = TRUE")
                
                # Get users by role
                users_by_role = await conn.fetch("""
                    SELECT role, COUNT(*) as count
                    FROM users 
                    GROUP BY role
                """)
                
                # Get recent registrations (last 7 days)
                recent_registrations = await conn.fetchval("""
                    SELECT COUNT(*) FROM users 
                    WHERE created_at >= NOW() - INTERVAL '7 days'
                """)
                
                # Get total karma
                total_karma = await conn.fetchval("SELECT SUM(karma_points) FROM users")
                
                # Get total cards
                total_cards = await conn.fetchval("SELECT COUNT(*) FROM cards_generated")
                
                # Get bound cards
                bound_cards = await conn.fetchval("SELECT COUNT(*) FROM cards_binding")
                
                return {
                    'total_users': total_users or 0,
                    'banned_users': banned_users or 0,
                    'active_users': (total_users or 0) - (banned_users or 0),
                    'users_by_role': {row['role']: row['count'] for row in users_by_role},
                    'recent_registrations': recent_registrations or 0,
                    'total_karma': total_karma or 0,
                    'total_cards': total_cards or 0,
                    'bound_cards': bound_cards or 0,
                    'unbound_cards': (total_cards or 0) - (bound_cards or 0)
                }
            finally:
                await conn.close()
        except Exception as e:
            logger.error(f"Error getting admin stats: {str(e)}")
            return {
                'total_users': 0,
                'banned_users': 0,
                'active_users': 0,
                'users_by_role': {},
                'recent_registrations': 0,
                'total_karma': 0,
                'total_cards': 0,
                'bound_cards': 0,
                'unbound_cards': 0
            }


# Create singleton instance
admin_service = AdminService()


# Export functions
__all__ = [
    'AdminService',
    'admin_service'
]
