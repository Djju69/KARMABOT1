"""
Favorites Service - управление избранными заведениями
"""

from typing import List, Dict, Optional
from core.database import db_v2
import logging

logger = logging.getLogger(__name__)

class FavoritesService:
    """Сервис для работы с избранными заведениями"""
    
    @staticmethod
    async def add_to_favorites(user_id: int, card_id: int) -> bool:
        """Добавить заведение в избранное"""
        try:
            # Проверяем, что карточка существует
            card = db_v2.get_card_by_id(card_id)
            if not card:
                return False
            
            # Добавляем в избранное
            db_v2.execute_query(
                "INSERT OR IGNORE INTO favorites (user_id, card_id) VALUES (?, ?)",
                (user_id, card_id)
            )
            
            logger.info(f"User {user_id} added card {card_id} to favorites")
            return True
            
        except Exception as e:
            logger.error(f"Error adding to favorites: {e}")
            return False
    
    @staticmethod
    async def remove_from_favorites(user_id: int, card_id: int) -> bool:
        """Удалить заведение из избранного"""
        try:
            db_v2.execute_query(
                "DELETE FROM favorites WHERE user_id = ? AND card_id = ?",
                (user_id, card_id)
            )
            
            logger.info(f"User {user_id} removed card {card_id} from favorites")
            return True
            
        except Exception as e:
            logger.error(f"Error removing from favorites: {e}")
            return False
    
    @staticmethod
    async def get_user_favorites(user_id: int, limit: int = 20) -> List[Dict]:
        """Получить избранные заведения пользователя"""
        try:
            query = """
                SELECT f.id, f.created_at, c.*, cat.name as category_name
                FROM favorites f
                JOIN cards_v2 c ON f.card_id = c.id
                LEFT JOIN categories_v2 cat ON c.category_id = cat.id
                WHERE f.user_id = ?
                ORDER BY f.created_at DESC
                LIMIT ?
            """
            
            favorites = db_v2.execute_query(query, (user_id, limit))
            return favorites
            
        except Exception as e:
            logger.error(f"Error getting user favorites: {e}")
            return []
    
    @staticmethod
    async def is_favorite(user_id: int, card_id: int) -> bool:
        """Проверить, есть ли заведение в избранном"""
        try:
            result = db_v2.fetch_one(
                "SELECT 1 FROM favorites WHERE user_id = ? AND card_id = ?",
                (user_id, card_id)
            )
            return result is not None
            
        except Exception as e:
            logger.error(f"Error checking favorite: {e}")
            return False
    
    @staticmethod
    async def get_favorites_count(user_id: int) -> int:
        """Получить количество избранных заведений"""
        try:
            result = db_v2.fetch_one(
                "SELECT COUNT(*) as count FROM favorites WHERE user_id = ?",
                (user_id,)
            )
            return result['count'] if result else 0
            
        except Exception as e:
            logger.error(f"Error getting favorites count: {e}")
            return 0

# Создаем экземпляр сервиса
favorites_service = FavoritesService()
