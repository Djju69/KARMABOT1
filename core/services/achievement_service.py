"""
Achievement service module for handling user achievements.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncpg
import os
import json
from core.utils.logger import get_logger

logger = get_logger(__name__)


class AchievementService:
    """Service for user achievements."""
    
    def __init__(self):
        """Initialize with database connection."""
        self.database_url = os.getenv("DATABASE_URL", "")
    
    async def get_connection(self) -> asyncpg.Connection:
        """Get database connection."""
        return await asyncpg.connect(self.database_url)
    
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
            conn = await self.get_connection()
            try:
                achievements = await conn.fetch("""
                    SELECT id, achievement_type, achievement_data, earned_at
                    FROM user_achievements 
                    WHERE user_id = $1
                    ORDER BY earned_at DESC
                    LIMIT $2 OFFSET $3
                """, user_id, limit, offset)
                
                result = []
                for achievement in achievements:
                    data = json.loads(achievement['achievement_data']) if achievement['achievement_data'] else {}
                    result.append({
                        'id': achievement['id'],
                        'achievement_type': achievement['achievement_type'],
                        'achievement_data': data,
                        'earned_at': achievement['earned_at']
                    })
                
                return result
            finally:
                await conn.close()
        except Exception as e:
            logger.error(f"Error getting achievements for user {user_id}: {str(e)}")
            return []
    
    async def add_achievement(
        self, 
        user_id: int, 
        achievement_type: str, 
        achievement_data: Dict[str, Any]
    ) -> bool:
        """
        Add achievement to user.
        
        Args:
            user_id: Telegram user ID
            achievement_type: Type of achievement
            achievement_data: Achievement data
            
        Returns:
            bool: Success status
        """
        try:
            conn = await self.get_connection()
            try:
                # Check if achievement already exists
                existing = await conn.fetchrow("""
                    SELECT id FROM user_achievements 
                    WHERE user_id = $1 AND achievement_type = $2 
                    AND achievement_data = $3
                """, user_id, achievement_type, json.dumps(achievement_data))
                
                if existing:
                    logger.info(f"Achievement {achievement_type} already exists for user {user_id}")
                    return False
                
                await conn.execute("""
                    INSERT INTO user_achievements 
                    (user_id, achievement_type, achievement_data, earned_at)
                    VALUES ($1, $2, $3, NOW())
                """, user_id, achievement_type, json.dumps(achievement_data))
                
                logger.info(f"Achievement {achievement_type} added for user {user_id}")
                return True
            finally:
                await conn.close()
        except Exception as e:
            logger.error(f"Error adding achievement for user {user_id}: {str(e)}")
            return False
    
    async def get_achievement_stats(self, user_id: int) -> Dict[str, Any]:
        """
        Get user achievement statistics.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            dict: Achievement statistics
        """
        try:
            conn = await self.get_connection()
            try:
                # Get total achievements count
                total_count = await conn.fetchval("""
                    SELECT COUNT(*) FROM user_achievements WHERE user_id = $1
                """, user_id)
                
                # Get achievements by type
                achievements_by_type = await conn.fetch("""
                    SELECT achievement_type, COUNT(*) as count
                    FROM user_achievements 
                    WHERE user_id = $1
                    GROUP BY achievement_type
                """, user_id)
                
                # Get recent achievements (last 5)
                recent_achievements = await conn.fetch("""
                    SELECT achievement_type, achievement_data, earned_at
                    FROM user_achievements 
                    WHERE user_id = $1
                    ORDER BY earned_at DESC
                    LIMIT 5
                """, user_id)
                
                return {
                    'total_count': total_count or 0,
                    'by_type': {row['achievement_type']: row['count'] for row in achievements_by_type},
                    'recent': [
                        {
                            'type': ach['achievement_type'],
                            'data': json.loads(ach['achievement_data']) if ach['achievement_data'] else {},
                            'earned_at': ach['earned_at']
                        }
                        for ach in recent_achievements
                    ]
                }
            finally:
                await conn.close()
        except Exception as e:
            logger.error(f"Error getting achievement stats for user {user_id}: {str(e)}")
            return {
                'total_count': 0,
                'by_type': {},
                'recent': []
            }
    
    async def check_level_up_achievements(self, user_id: int, level: int) -> bool:
        """
        Check and award level up achievements.
        
        Args:
            user_id: Telegram user ID
            level: User level
            
        Returns:
            bool: Whether achievement was awarded
        """
        try:
            # Check if this is a milestone level
            milestone_levels = [5, 10, 15, 20, 25]
            
            if level in milestone_levels:
                success = await self.add_achievement(
                    user_id, 
                    "level_milestone", 
                    {"level": level}
                )
                
                if success:
                    # Add notification
                    from core.services.notification_service import notification_service
                    await notification_service.add_notification(
                        user_id,
                        f"⭐ Достигнут {level} уровень!",
                        "achievement"
                    )
                
                return success
            
            return False
        except Exception as e:
            logger.error(f"Error checking level up achievements for user {user_id}: {str(e)}")
            return False
    
    async def check_karma_milestone_achievements(self, user_id: int, karma_points: int) -> List[str]:
        """
        Check and award karma milestone achievements.
        
        Args:
            user_id: Telegram user ID
            karma_points: Current karma points
            
        Returns:
            list: List of awarded achievement types
        """
        try:
            milestones = [1000, 2500, 5000, 10000, 25000]
            awarded = []
            
            for milestone in milestones:
                if karma_points >= milestone:
                    success = await self.add_achievement(
                        user_id, 
                        "karma_milestone", 
                        {"karma": milestone}
                    )
                    
                    if success:
                        awarded.append(f"karma_milestone_{milestone}")
                        
                        # Add notification
                        from core.services.notification_service import notification_service
                        await notification_service.add_notification(
                            user_id,
                            f"💎 Достижение! У вас {milestone} кармы!",
                            "achievement"
                        )
            
            return awarded
        except Exception as e:
            logger.error(f"Error checking karma milestone achievements for user {user_id}: {str(e)}")
            return []
    
    async def check_card_achievements(self, user_id: int, card_count: int) -> List[str]:
        """
        Check and award card-related achievements.
        
        Args:
            user_id: Telegram user ID
            card_count: Number of cards user has
            
        Returns:
            list: List of awarded achievement types
        """
        try:
            awarded = []
            
            # First card achievement
            if card_count == 1:
                success = await self.add_achievement(
                    user_id, 
                    "first_card", 
                    {"card_count": 1}
                )
                
                if success:
                    awarded.append("first_card")
                    
                    # Add notification
                    from core.services.notification_service import notification_service
                    await notification_service.add_notification(
                        user_id,
                        "🎉 Первая карта привязана!",
                        "achievement"
                    )
            
            # Multiple cards achievements
            elif card_count in [5, 10, 25]:
                success = await self.add_achievement(
                    user_id, 
                    "card_collector", 
                    {"card_count": card_count}
                )
                
                if success:
                    awarded.append(f"card_collector_{card_count}")
                    
                    # Add notification
                    from core.services.notification_service import notification_service
                    await notification_service.add_notification(
                        user_id,
                        f"🏆 Коллекционер карт: {card_count} карт!",
                        "achievement"
                    )
            
            return awarded
        except Exception as e:
            logger.error(f"Error checking card achievements for user {user_id}: {str(e)}")
            return []


# Create singleton instance
achievement_service = AchievementService()


# Export functions
__all__ = [
    'AchievementService',
    'achievement_service'
]
