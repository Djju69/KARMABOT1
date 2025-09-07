"""
SuperAdmin service module for handling super administrative operations.
Including card generation, data deletion, admin management, and system settings.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncpg
import os
from core.utils.logger import get_logger
from core.services.card_service import card_service
from core.services.admin_service import admin_service

logger = get_logger(__name__)


class SuperAdminService:
    """Service for super administrative operations."""
    
    def __init__(self):
        """Initialize with database connection."""
        self.database_url = os.getenv("DATABASE_URL", "")
    
    async def get_connection(self) -> asyncpg.Connection:
        """Get database connection."""
        return await asyncpg.connect(self.database_url)
    
    async def generate_cards(
        self, 
        count: int, 
        created_by: int
    ) -> Dict[str, Any]:
        """
        Generate new plastic cards (SuperAdmin only).
        
        Args:
            count: Number of cards to generate
            created_by: SuperAdmin who created the cards
            
        Returns:
            dict: Generation result
        """
        try:
            # Use card service for generation
            result = await card_service.generate_cards(count, created_by)
            
            if result['success']:
                # Log super admin action
                await self.log_superadmin_action(
                    created_by,
                    'generate_cards',
                    details=f"Создано {result['created_count']} карт, диапазон: {result['range']}"
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating cards: {str(e)}")
            return {
                'success': False,
                'message': f'Ошибка при генерации карт: {str(e)}',
                'error_code': 'generation_error'
            }
    
    async def delete_user_data(self, user_id: int, admin_id: int) -> Dict[str, Any]:
        """
        Delete user data (SuperAdmin only).
        
        Args:
            user_id: Target user ID
            admin_id: SuperAdmin who deleted the data
            
        Returns:
            dict: Deletion result
        """
        try:
            conn = await self.get_connection()
            try:
                # Check if user exists
                user = await conn.fetchrow(
                    "SELECT telegram_id, username FROM users WHERE telegram_id = $1",
                    user_id
                )
                
                if not user:
                    return {
                        'success': False,
                        'message': 'Пользователь не найден',
                        'error_code': 'user_not_found'
                    }
                
                # Delete user data in order (respecting foreign keys)
                # 1. Delete user achievements
                await conn.execute("DELETE FROM user_achievements WHERE user_id = $1", user_id)
                
                # 2. Delete user notifications
                await conn.execute("DELETE FROM user_notifications WHERE user_id = $1", user_id)
                
                # 3. Delete karma transactions
                await conn.execute("DELETE FROM karma_transactions WHERE user_id = $1", user_id)
                
                # 4. Delete card bindings
                await conn.execute("DELETE FROM cards_binding WHERE telegram_id = $1", user_id)
                
                # 5. Delete admin logs where user is target
                await conn.execute("DELETE FROM admin_logs WHERE target_user_id = $1", user_id)
                
                # 6. Delete user
                await conn.execute("DELETE FROM users WHERE telegram_id = $1", user_id)
                
                # Log super admin action
                await self.log_superadmin_action(
                    admin_id,
                    'delete_user_data',
                    target_user_id=user_id,
                    details=f"Удалены все данные пользователя {user['username'] or user_id}"
                )
                
                logger.info(f"User data deleted: {user_id} by superadmin {admin_id}")
                
                return {
                    'success': True,
                    'message': f'Данные пользователя {user_id} удалены',
                    'deleted_user': user['username'] or str(user_id)
                }
                
            finally:
                await conn.close()
        except Exception as e:
            logger.error(f"Error deleting user data for {user_id}: {str(e)}")
            return {
                'success': False,
                'message': f'Ошибка при удалении данных: {str(e)}',
                'error_code': 'deletion_error'
            }
    
    async def delete_card(self, card_id: str, admin_id: int) -> Dict[str, Any]:
        """
        Delete card (SuperAdmin only).
        
        Args:
            card_id: Card ID to delete
            admin_id: SuperAdmin who deleted the card
            
        Returns:
            dict: Deletion result
        """
        try:
            conn = await self.get_connection()
            try:
                # Check if card exists
                card = await conn.fetchrow(
                    "SELECT card_id, card_id_printable FROM cards_generated WHERE card_id = $1",
                    card_id
                )
                
                if not card:
                    return {
                        'success': False,
                        'message': 'Карта не найдена',
                        'error_code': 'card_not_found'
                    }
                
                # Delete card bindings first
                await conn.execute("DELETE FROM cards_binding WHERE card_id = $1", card_id)
                
                # Delete card
                await conn.execute("DELETE FROM cards_generated WHERE card_id = $1", card_id)
                
                # Log super admin action
                await self.log_superadmin_action(
                    admin_id,
                    'delete_card',
                    target_card_id=card_id,
                    details=f"Удалена карта {card['card_id_printable']}"
                )
                
                logger.info(f"Card deleted: {card_id} by superadmin {admin_id}")
                
                return {
                    'success': True,
                    'message': f'Карта {card["card_id_printable"]} удалена',
                    'deleted_card': card['card_id_printable']
                }
                
            finally:
                await conn.close()
        except Exception as e:
            logger.error(f"Error deleting card {card_id}: {str(e)}")
            return {
                'success': False,
                'message': f'Ошибка при удалении карты: {str(e)}',
                'error_code': 'deletion_error'
            }
    
    async def manage_admin_role(
        self, 
        user_id: int, 
        new_role: str, 
        admin_id: int
    ) -> Dict[str, Any]:
        """
        Manage admin roles (SuperAdmin only).
        
        Args:
            user_id: Target user ID
            new_role: New role (admin, superadmin, user)
            admin_id: SuperAdmin who made the change
            
        Returns:
            dict: Operation result
        """
        try:
            conn = await self.get_connection()
            try:
                # Validate role
                valid_roles = ['user', 'partner', 'admin', 'superadmin']
                if new_role not in valid_roles:
                    return {
                        'success': False,
                        'message': f'Неверная роль. Допустимые: {", ".join(valid_roles)}',
                        'error_code': 'invalid_role'
                    }
                
                # Check if user exists
                user = await conn.fetchrow(
                    "SELECT telegram_id, username, role FROM users WHERE telegram_id = $1",
                    user_id
                )
                
                if not user:
                    return {
                        'success': False,
                        'message': 'Пользователь не найден',
                        'error_code': 'user_not_found'
                    }
                
                old_role = user['role']
                
                # Update user role
                await conn.execute(
                    "UPDATE users SET role = $1 WHERE telegram_id = $2",
                    new_role, user_id
                )
                
                # Log super admin action
                await self.log_superadmin_action(
                    admin_id,
                    'change_role',
                    target_user_id=user_id,
                    details=f"Изменена роль с '{old_role}' на '{new_role}'"
                )
                
                # Add notification to user
                from core.services.notification_service import notification_service
                await notification_service.add_notification(
                    user_id,
                    f"🔧 Ваша роль изменена на: {new_role}",
                    "role_change"
                )
                
                logger.info(f"User role changed: {user_id} from {old_role} to {new_role} by superadmin {admin_id}")
                
                return {
                    'success': True,
                    'message': f'Роль пользователя изменена с {old_role} на {new_role}',
                    'old_role': old_role,
                    'new_role': new_role
                }
                
            finally:
                await conn.close()
        except Exception as e:
            logger.error(f"Error changing user role for {user_id}: {str(e)}")
            return {
                'success': False,
                'message': f'Ошибка при изменении роли: {str(e)}',
                'error_code': 'role_change_error'
            }
    
    async def get_system_settings(self) -> Dict[str, Any]:
        """
        Get system settings.
        
        Returns:
            dict: System settings
        """
        try:
            from core.settings import settings
            
            return {
                'karma_config': {
                    'level_thresholds': settings.karma.level_thresholds,
                    'daily_login_bonus': settings.karma.daily_login_bonus,
                    'card_bind_bonus': settings.karma.card_bind_bonus,
                    'referral_bonus': settings.karma.referral_bonus,
                    'admin_karma_limit': settings.karma.admin_karma_limit,
                    'card_generation_limit': settings.karma.card_generation_limit,
                    'rate_limit_per_minute': settings.karma.rate_limit_per_minute
                },
                'card_config': {
                    'prefix': settings.cards.prefix,
                    'start_number': settings.cards.start_number,
                    'format': settings.cards.format,
                    'printable_format': settings.cards.printable_format
                },
                'features': {
                    'new_menu': settings.features.new_menu,
                    'partner_fsm': settings.features.partner_fsm,
                    'moderation': settings.features.moderation,
                    'qr_webapp': settings.features.qr_webapp,
                    'listen_notify': settings.features.listen_notify
                }
            }
        except Exception as e:
            logger.error(f"Error getting system settings: {str(e)}")
            return {}
    
    async def get_superadmin_stats(self) -> Dict[str, Any]:
        """
        Get super admin panel statistics.
        
        Returns:
            dict: Super admin statistics
        """
        try:
            conn = await self.get_connection()
            try:
                # Get basic stats from admin service
                admin_stats = await admin_service.get_admin_stats()
                
                # Get additional super admin stats
                total_admin_logs = await conn.fetchval("SELECT COUNT(*) FROM admin_logs")
                
                # Get super admin actions
                superadmin_actions = await conn.fetch("""
                    SELECT action, COUNT(*) as count
                    FROM admin_logs 
                    WHERE admin_id IN (
                        SELECT telegram_id FROM users WHERE role = 'superadmin'
                    )
                    GROUP BY action
                """)
                
                # Get system health
                system_health = {
                    'database_connected': True,
                    'migrations_applied': True,  # TODO: Check actual migration status
                    'services_running': True
                }
                
                return {
                    **admin_stats,
                    'total_admin_logs': total_admin_logs or 0,
                    'superadmin_actions': {row['action']: row['count'] for row in superadmin_actions},
                    'system_health': system_health
                }
            finally:
                await conn.close()
        except Exception as e:
            logger.error(f"Error getting superadmin stats: {str(e)}")
            return {
                'total_users': 0,
                'banned_users': 0,
                'active_users': 0,
                'total_admin_logs': 0,
                'superadmin_actions': {},
                'system_health': {'database_connected': False}
            }
    
    async def log_superadmin_action(
        self, 
        admin_id: int, 
        action: str, 
        target_user_id: int = None,
        target_card_id: str = None,
        details: str = None
    ) -> bool:
        """
        Log super admin action.
        
        Args:
            admin_id: SuperAdmin who performed the action
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
                
                logger.info(f"SuperAdmin action logged: {admin_id} -> {action}")
                return True
            finally:
                await conn.close()
        except Exception as e:
            logger.error(f"Error logging superadmin action: {str(e)}")
            return False


# Create singleton instance
superadmin_service = SuperAdminService()


# Export functions
__all__ = [
    'SuperAdminService',
    'superadmin_service'
]
