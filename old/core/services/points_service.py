"""
Points Service - система бонусных баллов
"""

from typing import List, Dict, Optional
from core.database import db_v2
import logging

logger = logging.getLogger(__name__)

class PointsService:
    """Сервис для работы с бонусными баллами"""
    
    @staticmethod
    async def add_points(user_id: int, points: int, operation: str, description: str = "") -> bool:
        """Добавить баллы пользователю"""
        try:
            # Добавляем запись в лог
            db_v2.execute_query(
                """INSERT INTO points_log (user_id, points, operation, description) 
                   VALUES (?, ?, ?, ?)""",
                (user_id, points, operation, description)
            )
            
            # Обновляем баланс пользователя
            db_v2.execute_query(
                """UPDATE users SET points = COALESCE(points, 0) + ? WHERE id = ?""",
                (points, user_id)
            )
            
            logger.info(f"Added {points} points to user {user_id} for {operation}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding points: {e}")
            return False
    
    @staticmethod
    async def spend_points(user_id: int, points: int, operation: str, description: str = "") -> bool:
        """Потратить баллы пользователя"""
        try:
            # Проверяем баланс
            current_balance = await PointsService.get_user_balance(user_id)
            if current_balance < points:
                return False
            
            # Добавляем запись в лог (с отрицательным значением)
            db_v2.execute_query(
                """INSERT INTO points_log (user_id, points, operation, description) 
                   VALUES (?, ?, ?, ?)""",
                (user_id, -points, operation, description)
            )
            
            # Обновляем баланс пользователя
            db_v2.execute_query(
                """UPDATE users SET points = COALESCE(points, 0) - ? WHERE id = ?""",
                (points, user_id)
            )
            
            logger.info(f"Spent {points} points from user {user_id} for {operation}")
            return True
            
        except Exception as e:
            logger.error(f"Error spending points: {e}")
            return False
    
    @staticmethod
    async def get_user_balance(user_id: int) -> int:
        """Получить текущий баланс баллов пользователя"""
        try:
            result = db_v2.fetch_one(
                "SELECT COALESCE(points, 0) as balance FROM users WHERE id = ?",
                (user_id,)
            )
            return result['balance'] if result else 0
            
        except Exception as e:
            logger.error(f"Error getting user balance: {e}")
            return 0
    
    @staticmethod
    async def get_user_points_history(user_id: int, limit: int = 20) -> List[Dict]:
        """Получить историю операций с баллами"""
        try:
            query = """
                SELECT points, operation, description, created_at
                FROM points_log
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            """
            
            history = db_v2.fetch_all(query, (user_id, limit))
            return history
            
        except Exception as e:
            logger.error(f"Error getting points history: {e}")
            return []
    
    @staticmethod
    async def get_points_leaderboard(limit: int = 10) -> List[Dict]:
        """Получить таблицу лидеров по баллам"""
        try:
            query = """
                SELECT id, username, first_name, last_name, COALESCE(points, 0) as balance
                FROM users
                WHERE COALESCE(points, 0) > 0
                ORDER BY balance DESC
                LIMIT ?
            """
            
            leaderboard = db_v2.fetch_all(query, (limit,))
            return leaderboard
            
        except Exception as e:
            logger.error(f"Error getting points leaderboard: {e}")
            return []

# Создаем экземпляр сервиса
points_service = PointsService()
