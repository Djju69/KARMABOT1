"""
User service module for handling user-related operations.
Including karma management, level calculation, and transaction history.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncpg
import os
from core.utils.logger import get_logger

logger = get_logger(__name__)


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
    
    async def get_user_level(self, user_id: int) -> str:
        """
        Calculate user level based on their karma.
        Упрощенная версия - только один уровень для запуска.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            str: User level (всегда "Member" для упрощения)
        """
        return "Member"  # Упрощенная версия - один уровень
    
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
            try:
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
                
            finally:
                await conn.close()
        except Exception as e:
            logger.error(f"Error subtracting karma from user {user_id}: {str(e)}")
            return False
    
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