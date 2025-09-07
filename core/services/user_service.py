"""
User service module for handling user-related operations.
Including karma management, level calculation, and transaction history.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import sqlite3
from pathlib import Path
from core.utils.logger import get_logger

logger = get_logger(__name__)


class KarmaService:
    """Service for karma system operations."""
    
    def __init__(self):
        """Initialize with database connection."""
        self.db_path = Path(__file__).parent.parent / "database" / "data.db"
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    async def get_user_karma(self, user_id: int) -> int:
        """
        Get current user karma points.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            int: User's current karma points
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT karma_points FROM users WHERE user_id = ?",
                    (user_id,)
                )
                result = cursor.fetchone()
                return result['karma_points'] if result else 0
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
            with self.get_connection() as conn:
                # Get current karma
                current_karma = await self.get_user_karma(user_id)
                new_karma = current_karma + amount
                
                # Update user karma
                conn.execute(
                    "UPDATE users SET karma_points = ? WHERE user_id = ?",
                    (new_karma, user_id)
                )
                
                # Log transaction
                conn.execute("""
                    INSERT INTO karma_transactions 
                    (user_id, amount, reason, admin_id, created_at)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (user_id, amount, reason, admin_id))
                
                conn.commit()
                logger.info(f"Added {amount} karma to user {user_id}. New total: {new_karma}")
                return True
                
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
            with self.get_connection() as conn:
                # Get current karma
                current_karma = await self.get_user_karma(user_id)
                new_karma = max(0, current_karma - amount)  # Don't go below 0
                
                # Update user karma
                conn.execute(
                    "UPDATE users SET karma_points = ? WHERE user_id = ?",
                    (new_karma, user_id)
                )
                
                # Log transaction
                conn.execute("""
                    INSERT INTO karma_transactions 
                    (user_id, amount, reason, admin_id, created_at)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (user_id, -amount, reason, admin_id))
                
                conn.commit()
                logger.info(f"Subtracted {amount} karma from user {user_id}. New total: {new_karma}")
                return True
                
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
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT amount, reason, admin_id, created_at
                    FROM karma_transactions 
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                """, (user_id, limit, offset))
                
                transactions = []
                for row in cursor.fetchall():
                    transactions.append({
                        'amount': row['amount'],
                        'reason': row['reason'],
                        'admin_id': row['admin_id'],
                        'created_at': row['created_at']
                    })
                
                return transactions
                
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

async def get_or_create_user(telegram_id: int, username: str = None, first_name: str = None, last_name: str = None) -> Dict[str, Any]:
    """
    Получить или создать пользователя.
    
    Args:
        telegram_id: Telegram ID пользователя
        username: Имя пользователя
        first_name: Имя
        last_name: Фамилия
        
    Returns:
        dict: Информация о пользователе
    """
    try:
        with karma_service.get_connection() as conn:
            # Проверяем, существует ли пользователь
            cursor = conn.execute(
                "SELECT * FROM users WHERE telegram_id = ?",
                (telegram_id,)
            )
            user = cursor.fetchone()
            
            if user:
                return {
                    'telegram_id': user[1],
                    'username': user[2],
                    'first_name': user[3],
                    'last_name': user[4],
                    'language_code': user[5],
                    'karma_points': user[6],
                    'created_at': user[7],
                    'updated_at': user[8]
                }
            
            # Создаем нового пользователя
            conn.execute("""
                INSERT INTO users (telegram_id, username, first_name, last_name, language_code, karma_points)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (telegram_id, username, first_name, last_name, 'ru', 0))
            
            conn.commit()
            
            # Получаем созданного пользователя
            cursor = conn.execute(
                "SELECT * FROM users WHERE telegram_id = ?",
                (telegram_id,)
            )
            user = cursor.fetchone()
            
            return {
                'telegram_id': user[1],
                'username': user[2],
                'first_name': user[3],
                'last_name': user[4],
                'language_code': user[5],
                'karma_points': user[6],
                'created_at': user[7],
                'updated_at': user[8]
            }
            
    except Exception as e:
        logger.error(f"Error getting or creating user {telegram_id}: {str(e)}")
        return None