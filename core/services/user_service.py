"""
User service module for handling user-related operations.
Including karma management, level calculation, and transaction history.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncpg
import os
import logging
from core.services.gamification_service import gamification_service

logger = logging.getLogger(__name__)


class KarmaService:
    """Service for karma system operations."""
    
    def __init__(self):
        """Initialize with database connection."""
        self.database_url = os.getenv("DATABASE_URL", "")
    
    async def get_connection(self) -> asyncpg.Connection:
        """Get database connection."""
        return await asyncpg.connect(self.database_url)
    
    async def get_user_karma(self, user_id: int) -> int:
        """
        Get current user karma points.
    
    Args:
        user_id: Telegram user ID
        
    Returns:
            int: User's current karma points
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
            logger.error(f"Error getting karma for user {user_id}: {str(e)}")
            return 0
    
    async def get_user_level(self, user_id: int) -> int:
        """
        Calculate user level based on their karma according to TZ.
    
    Args:
        user_id: Telegram user ID
        
    Returns:
            int: User level (1-10 based on karma thresholds)
        """
        karma_points = await self.get_user_karma(user_id)
        return self.calculate_level(karma_points)
    
    def calculate_level(self, karma_points: int) -> int:
        """
        Calculate user level based on karma points according to TZ.
        
        Args:
            karma_points: Current karma points
            
        Returns:
            int: User level (1-10)
        """
        from core.settings import settings
        
        thresholds = settings.karma.level_thresholds
        
        for level, threshold in enumerate(thresholds, 1):
            if karma_points < threshold:
                return level
        
        return len(thresholds) + 1  # Maximum level
    
    async def get_level_progress(self, user_id: int) -> Dict[str, Any]:
        """
        Get user's progress to next level.
    
    Args:
        user_id: Telegram user ID
        
    Returns:
            dict: Progress information
        """
        karma_points = await self.get_user_karma(user_id)
        current_level = self.calculate_level(karma_points)
        
        from core.settings import settings
        thresholds = settings.karma.level_thresholds
        
        if current_level > len(thresholds):
            return {
                'current_level': current_level,
                'next_threshold': None,
                'progress_karma': 0,
                'total_needed': 0,
                'progress_percent': 100
            }
        
        next_threshold = thresholds[current_level - 1]
        prev_threshold = thresholds[current_level - 2] if current_level > 1 else 0
        
        progress_karma = karma_points - prev_threshold
        total_needed = next_threshold - prev_threshold
        progress_percent = (progress_karma / total_needed) * 100
        
        return {
            'current_level': current_level,
            'next_threshold': next_threshold,
            'progress_karma': progress_karma,
            'total_needed': total_needed,
            'progress_percent': min(progress_percent, 100)
        }
    
    async def add_karma(self, user_id: int, amount: int, reason: str = "", admin_id: int = None) -> bool:
        """
        Add karma points to user.
    
    Args:
        user_id: Telegram user ID
            amount: Amount of karma to add
            reason: Reason for adding karma
            admin_id: Admin who added karma (if manual)
        
    Returns:
            bool: Success status
        """
        try:
            conn = await self.get_connection()
            try:
                # Get current karma
                current_karma = await self.get_user_karma(user_id)
                new_karma = current_karma + amount
                
                # Update user karma
                await conn.execute(
                    "UPDATE users SET karma_points = $1 WHERE telegram_id = $2",
                    new_karma, user_id
                )
                
                # Log transaction
                await conn.execute("""
                    INSERT INTO karma_transactions 
                    (user_id, amount, reason, admin_id, created_at)
                    VALUES ($1, $2, $3, $4, NOW())
                """, user_id, amount, reason, admin_id)
                
                # Check for level up and achievements
                old_level = self.calculate_level(current_karma)
                new_level = self.calculate_level(new_karma)
                
                if new_level > old_level:
                    await self._check_level_up_achievements(user_id, new_level)
                
                await self._check_karma_milestone_achievements(user_id, new_karma)
                
                logger.info(f"Added {amount} karma to user {user_id}. New total: {new_karma}")
                return True
                
            finally:
                await conn.close()
        except Exception as e:
            logger.error(f"Error adding karma to user {user_id}: {str(e)}")
            return False
            
    async def subtract_karma(self, user_id: int, amount: int, reason: str = "", admin_id: int = None) -> bool:
        """
        Subtract karma points from user.
        
        Args:
            user_id: Telegram user ID
            amount: Amount of karma to subtract
            reason: Reason for subtracting karma
            admin_id: Admin who subtracted karma (if manual)
            
        Returns:
            bool: Success status
        """
        try:
            conn = await self.get_connection()
            # Get current karma
            current_karma = await self.get_user_karma(user_id)
            new_karma = max(0, current_karma - amount)  # Don't go below 0
            
            # Update user karma
            await conn.execute(
                "UPDATE users SET karma_points = $1 WHERE telegram_id = $2",
                new_karma, user_id
            )
            
            # Log transaction
            await conn.execute("""
                INSERT INTO karma_transactions 
                (user_id, amount, reason, admin_id, created_at)
                VALUES ($1, $2, $3, $4, NOW())
            """, user_id, -amount, reason, admin_id)
            
            logger.info(f"Subtracted {amount} karma from user {user_id}. New total: {new_karma}")
            return True

        except Exception as e:
            logger.error(f"Error subtracting karma from user {user_id}: {str(e)}")
            return False
        finally:
            await conn.close()

    async def get_karma_history(self, user_id: int, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get karma transaction history for user.
    
        Args:
            user_id: Telegram user ID
            limit: Number of transactions to return
            offset: Offset for pagination
        
    Returns:
            list: List of karma transactions
        """
        try:
            conn = await self.get_connection()
            try:
                rows = await conn.fetch("""
                    SELECT amount, reason, admin_id, created_at
                    FROM karma_transactions 
                    WHERE user_id = $1
                    ORDER BY created_at DESC
                    LIMIT $2 OFFSET $3
                """, user_id, limit, offset)
                
                transactions = []
                for row in rows:
                    transactions.append({
                        'amount': row['amount'],
                        'reason': row['reason'],
                        'admin_id': row['admin_id'],
                        'created_at': row['created_at']
                    })
                
                return transactions
                
            finally:
                await conn.close()
        except Exception as e:
            logger.error(f"Error getting karma history for user {user_id}: {str(e)}")
            return []
    
    async def convert_karma_to_dong(self, user_id: int, karma_amount: int) -> Dict[str, Any]:
        """
        Конвертировать карму в донги (1 балл = 1000 донгов).
        
        Args:
            user_id: Telegram user ID
            karma_amount: Количество кармы для конвертации
            
        Returns:
            dict: Результат конвертации
        """
        try:
            current_karma = await self.get_user_karma(user_id)
            
            if current_karma < karma_amount:
                return {
                    'success': False,
                    'message': f'Недостаточно кармы. У вас {current_karma} баллов.',
                    'error_code': 'insufficient_karma'
                }
            
            # Конвертация: 1 балл = 1000 донгов
            dong_amount = karma_amount * 1000
            
            # Списываем карму
            success = await self.subtract_karma(user_id, karma_amount, f"Конвертация в донги: {dong_amount}")
            
            if success:
                return {
                    'success': True,
                    'message': f'Успешно конвертировано {karma_amount} баллов в {dong_amount} донгов.',
                    'karma_spent': karma_amount,
                    'dong_received': dong_amount
                }
            else:
                return {
                    'success': False,
                    'message': 'Ошибка при конвертации кармы.',
                    'error_code': 'conversion_error'
                }
                
        except Exception as e:
            logger.error(f"Error converting karma to dong for user {user_id}: {str(e)}")
            return {
                'success': False,
                'message': 'Произошла ошибка при конвертации.',
                'error_code': 'database_error'
            }
    
    async def spend_karma_for_discount(self, user_id: int, discount_amount: int) -> Dict[str, Any]:
        """
        Потратить карму для увеличения скидки.
        Скидка увеличивается на 1% за каждый потраченный балл кармы.
        
        Args:
            user_id: Telegram user ID
            discount_amount: Количество баллов кармы для траты
            
        Returns:
            dict: Результат траты кармы
        """
        try:
            current_karma = await self.get_user_karma(user_id)
            
            if current_karma < discount_amount:
                return {
                    'success': False,
                    'message': f'Недостаточно кармы. У вас {current_karma} баллов.',
                    'error_code': 'insufficient_karma'
                }
            
            # Списываем карму
            success = await self.subtract_karma(user_id, discount_amount, f"Трата на увеличение скидки: +{discount_amount}%")
            
            if success:
                return {
                    'success': True,
                    'message': f'Потрачено {discount_amount} баллов кармы. Скидка увеличена на {discount_amount}%.',
                    'karma_spent': discount_amount,
                    'discount_bonus': discount_amount
                }
            else:
                return {
                    'success': False,
                    'message': 'Ошибка при трате кармы.',
                    'error_code': 'spending_error'
                }
                
        except Exception as e:
            logger.error(f"Error spending karma for discount for user {user_id}: {str(e)}")
            return {
                'success': False,
                'message': 'Произошла ошибка при трате кармы.',
                'error_code': 'database_error'
            }
    
    async def _check_level_up_achievements(self, user_id: int, level: int):
        """Check and award level up achievements"""
        try:
            conn = await self.get_connection()
            try:
                # Check if achievement already exists
                existing = await conn.fetchrow("""
                    SELECT id FROM user_achievements 
                    WHERE user_id = $1 AND achievement_type = 'level_up' 
                    AND achievement_data::json->>'level' = $2
                """, user_id, str(level))
                
                if not existing:
                    # Award achievement
                    await conn.execute("""
                        INSERT INTO user_achievements (user_id, achievement_type, achievement_data, earned_at)
                        VALUES ($1, 'level_up', $2, NOW())
                    """, user_id, f'{{"level": {level}}}')
                    
                    # Add notification
                    await conn.execute("""
                        INSERT INTO user_notifications (user_id, message, notification_type, created_at)
                        VALUES ($1, $2, 'level_up', NOW())
                    """, user_id, f"🎉 Поздравляем! Вы достигли {level} уровня!")
                    
                    logger.info(f"Level up achievement awarded to user {user_id} for level {level}")
            finally:
                await conn.close()
        except Exception as e:
            logger.error(f"Error checking level up achievements for user {user_id}: {str(e)}")
    
    async def _check_karma_milestone_achievements(self, user_id: int, karma_points: int):
        """Check and award karma milestone achievements"""
        try:
            conn = await self.get_connection()
            try:
                milestones = [1000, 2500, 5000, 10000, 25000]
                
                for milestone in milestones:
                    if karma_points >= milestone:
                        # Check if achievement already exists
                        existing = await conn.fetchrow("""
                            SELECT id FROM user_achievements 
                            WHERE user_id = $1 AND achievement_type = 'karma_milestone' 
                            AND achievement_data::json->>'karma' = $2
                        """, user_id, str(milestone))
                        
                        if not existing:
                            # Award achievement
                            await conn.execute("""
                                INSERT INTO user_achievements (user_id, achievement_type, achievement_data, earned_at)
                                VALUES ($1, 'karma_milestone', $2, NOW())
                            """, user_id, f'{{"karma": {milestone}}}')
                            
                            # Add notification
                            await conn.execute("""
                                INSERT INTO user_notifications (user_id, message, notification_type, created_at)
                                VALUES ($1, $2, 'karma_change', NOW())
                            """, user_id, f"💎 Достижение! У вас {milestone} кармы!")
                            
                            logger.info(f"Karma milestone achievement awarded to user {user_id} for {milestone} karma")
            finally:
                await conn.close()
        except Exception as e:
            logger.error(f"Error checking karma milestone achievements for user {user_id}: {str(e)}")


# Create singleton instance
karma_service = KarmaService()


# Legacy functions for backward compatibility
async def get_user_balance(user_id: int) -> int:
    """Legacy function - now returns karma points."""
    return await karma_service.get_user_karma(user_id)


async def get_user_level(user_id: int) -> str:
    """Legacy function - now returns karma level."""
    return await karma_service.get_user_level(user_id)


async def add_points(user_id: int, amount: int, description: str = "") -> bool:
    """Legacy function - now adds karma points."""
    return await karma_service.add_karma(user_id, amount, description)


async def get_user_history(user_id: int, page: int = 1, per_page: int = 5) -> Dict[str, Any]:
    """Legacy function - now returns karma history."""
    offset = (page - 1) * per_page
    transactions = await karma_service.get_karma_history(user_id, per_page, offset)
    
    return {
        'transactions': transactions,
        'page': page,
        'per_page': per_page,
        'total': len(transactions)
    }

async def get_or_create_user(telegram_id: int, username: str = None, first_name: str = None, last_name: str = None, lang_code: str = 'ru') -> Dict[str, Any]:
    """
    Получить или создать пользователя.
    
    Args:
        telegram_id: Telegram ID пользователя
        username: Имя пользователя
        first_name: Имя
        last_name: Фамилия
        lang_code: Код языка
        
    Returns:
        dict: Информация о пользователе
    """
    try:
        conn = await karma_service.get_connection()
        try:
            # Проверяем, существует ли пользователь
            user = await conn.fetchrow(
                "SELECT * FROM users WHERE telegram_id = $1",
                telegram_id
            )
            
            if user:
                return {
                    'telegram_id': user['telegram_id'],
                    'username': user['username'],
                    'first_name': user['first_name'],
                    'last_name': user['last_name'],
                    'language_code': user['language_code'],
                    'karma_points': user['karma_points'],
                    'created_at': user['created_at'],
                    'updated_at': user['updated_at']
                }
            
            # Создаем нового пользователя
            await conn.execute("""
                INSERT INTO users (telegram_id, username, first_name, last_name, language_code, karma_points)
                VALUES ($1, $2, $3, $4, $5, $6)
            """, telegram_id, username, first_name, last_name, lang_code, 0)
            
            # Получаем созданного пользователя
            user = await conn.fetchrow(
                "SELECT * FROM users WHERE telegram_id = $1",
                telegram_id
            )
            
            return {
                'telegram_id': user['telegram_id'],
                'username': user['username'],
                'first_name': user['first_name'],
                'last_name': user['last_name'],
                'language_code': user['language_code'],
                'karma_points': user['karma_points'],
                'created_at': user['created_at'],
                'updated_at': user['updated_at']
            }
            
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"Error getting or creating user {telegram_id}: {str(e)}")
        return None

async def subtract_karma(user_id: int, amount: int, reason: str = "", admin_id: int = None) -> bool:
    """Subtract karma from user"""
    return await karma_service.subtract_karma(user_id, amount, reason, admin_id)

async def add_karma(user_id: int, amount: int, reason: str = "", admin_id: int = None) -> bool:
    """Add karma to user"""
    return await karma_service.add_karma(user_id, amount, reason, admin_id)


# Export all required functions
__all__ = [
    'KarmaService',
    'karma_service',
    'get_user_balance',
    'get_user_level',
    'add_points',
    'get_user_history',
    'get_or_create_user',
    'subtract_karma',
    'add_karma'
]


# === Role and Language helpers used by help handlers ===
async def get_user_role(user_id: int) -> str:
    """Return user's role. Fallback to settings admin as super_admin, else 'user'."""
    try:
        conn = await karma_service.get_connection()
        try:
            # Try user_roles mapping first (if exists)
            try:
                row = await conn.fetchrow(
                    "SELECT role FROM user_roles WHERE user_id = $1",
                    user_id,
                )
                if row and row.get('role'):
                    return str(row['role'])
            except Exception:
                # Table might not exist; proceed with fallbacks
                pass

            # Super admin fallback from settings
            from core.settings import settings
            admin_id = getattr(settings.bots, 'admin_id', None) or getattr(settings, 'ADMIN_ID', None)
            if isinstance(admin_id, int) and admin_id == int(user_id):
                # Best-effort upsert into user_roles
                try:
                    await conn.execute(
                        """
                        INSERT INTO user_roles (user_id, role) VALUES ($1, $2)
                        ON CONFLICT (user_id) DO UPDATE SET role = EXCLUDED.role
                        """,
                        user_id, 'super_admin'
                    )
                except Exception:
                    pass
                return 'super_admin'

            # Default role
            try:
                await conn.execute(
                    """
                    INSERT INTO user_roles (user_id, role) VALUES ($1, $2)
                    ON CONFLICT (user_id) DO NOTHING
                    """,
                    user_id, 'user'
                )
            except Exception:
                pass
            return 'user'
        finally:
            await conn.close()
    except Exception as e:
        logger.warning(f"get_user_role fallback to 'user' due to error: {e}")
        return 'user'


async def get_user_language(user_id: int) -> str:
    """Return user's language_code from users table, default 'ru'."""
    try:
        conn = await karma_service.get_connection()
        try:
            row = await conn.fetchrow(
                "SELECT language_code FROM users WHERE telegram_id = $1",
                user_id,
            )
            lang = (row and row.get('language_code')) or 'ru'
            return lang or 'ru'
        finally:
            await conn.close()
    except Exception as e:
        logger.warning(f"get_user_language fallback to 'ru' due to error: {e}")
        return 'ru'


# Re-export helpers
__all__.extend(['get_user_role', 'get_user_language'])