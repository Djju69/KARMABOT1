"""
Card service module for handling plastic cards operations.
Including card generation, QR codes, and card binding.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncpg
import os
import qrcode
import io
import base64
from core.utils.logger import get_logger
from core.settings import settings

logger = get_logger(__name__)


class CardService:
    """Service for plastic cards operations."""
    
    def __init__(self):
        """Initialize with database connection."""
        self.database_url = os.getenv("DATABASE_URL", "")
        self.bot_username = os.getenv("BOT_USERNAME", "KarmaQRBot")
    
    async def get_connection(self) -> asyncpg.Connection:
        """Get database connection."""
        return await asyncpg.connect(self.database_url)
    
    def generate_card_id(self, card_number: int) -> str:
        """
        Generate card ID according to TZ format.
        
        Args:
            card_number: Sequential card number
            
        Returns:
            str: Card ID in format KS12340001
        """
        return settings.cards.format.format(
            prefix=settings.cards.prefix,
            number=card_number
        )
    
    def generate_card_id_printable(self, card_number: int) -> str:
        """
        Generate printable card ID according to TZ format.
        
        Args:
            card_number: Sequential card number
            
        Returns:
            str: Printable card ID in format KS-1234-0001
        """
        id_str = str(card_number)
        group1 = id_str[:-4] if len(id_str) > 4 else "0000"
        group2 = id_str[-4:] if len(id_str) >= 4 else id_str.zfill(4)
        
        return settings.cards.printable_format.format(
            prefix=settings.cards.prefix,
            group1=group1,
            group2=group2
        )
    
    def generate_qr_url(self, card_id: str) -> str:
        """
        Generate QR URL for card binding.
        
        Args:
            card_id: Card ID
            
        Returns:
            str: QR URL for binding
        """
        return f"https://t.me/{self.bot_username}?start=bind&cid={card_id}"
    
    async def get_next_card_number(self) -> int:
        """
        Get next available card number.
        
        Returns:
            int: Next card number
        """
        try:
            conn = await self.get_connection()
            try:
                # Get the highest card number
                result = await conn.fetchval("""
                    SELECT MAX(CAST(SUBSTRING(card_id FROM 3) AS INTEGER))
                    FROM cards_generated 
                    WHERE card_id LIKE $1
                """, f"{settings.cards.prefix}%")
                
                if result is None:
                    return settings.cards.start_number
                
                return result + 1
            finally:
                await conn.close()
        except Exception as e:
            logger.error(f"Error getting next card number: {str(e)}")
            return settings.cards.start_number
    
    async def generate_cards(self, count: int, created_by: int) -> Dict[str, Any]:
        """
        Generate new plastic cards according to TZ.
        
        Args:
            count: Number of cards to generate (1-10000)
            created_by: Admin who created the cards
            
        Returns:
            dict: Generation result
        """
        try:
            # Validate count
            if not 1 <= count <= settings.karma.card_generation_limit:
                return {
                    'success': False,
                    'message': f'Неверное количество карт. Допустимо: 1-{settings.karma.card_generation_limit}',
                    'error_code': 'invalid_count'
                }
            
            conn = await self.get_connection()
            try:
                # Get starting card number
                start_number = await self.get_next_card_number()
                
                cards_data = []
                created_count = 0
                
                for i in range(count):
                    card_number = start_number + i
                    card_id = self.generate_card_id(card_number)
                    card_id_printable = self.generate_card_id_printable(card_number)
                    qr_url = self.generate_qr_url(card_id)
                    
                    # Check if card already exists
                    existing = await conn.fetchrow(
                        "SELECT id FROM cards_generated WHERE card_id = $1",
                        card_id
                    )
                    
                    if existing:
                        logger.warning(f"Card {card_id} already exists, skipping")
                        continue
                    
                    # Create card
                    await conn.execute("""
                        INSERT INTO cards_generated 
                        (card_id, card_id_printable, qr_url, created_by, created_at)
                        VALUES ($1, $2, $3, $4, NOW())
                    """, card_id, card_id_printable, qr_url, created_by)
                    
                    cards_data.append({
                        'card_id': card_id,
                        'card_id_printable': card_id_printable,
                        'qr_url': qr_url
                    })
                    
                    created_count += 1
                
                # Log admin action
                await conn.execute("""
                    INSERT INTO admin_logs 
                    (admin_id, action, details, created_at)
                    VALUES ($1, 'generate_cards', $2, NOW())
                """, created_by, f"Создано {created_count} карт, диапазон: {cards_data[0]['card_id']}-{cards_data[-1]['card_id']}")
                
                logger.info(f"Generated {created_count} cards for admin {created_by}")
                
                return {
                    'success': True,
                    'message': f'Успешно создано {created_count} карт',
                    'created_count': created_count,
                    'cards_data': cards_data,
                    'range': f"{cards_data[0]['card_id_printable']} - {cards_data[-1]['card_id_printable']}" if cards_data else "Нет карт"
                }
                
            finally:
                await conn.close()
        except Exception as e:
            logger.error(f"Error generating cards: {str(e)}")
            return {
                'success': False,
                'message': f'Ошибка при генерации карт: {str(e)}',
                'error_code': 'generation_error'
            }
    
    async def get_card(self, card_id: str) -> Optional[Dict[str, Any]]:
        """
        Get card information by ID.
        
        Args:
            card_id: Card ID
            
        Returns:
            dict: Card information or None
        """
        try:
            conn = await self.get_connection()
            try:
                card = await conn.fetchrow("""
                    SELECT * FROM cards_generated WHERE card_id = $1
                """, card_id)
                
                if not card:
                    return None
                
                return dict(card)
            finally:
                await conn.close()
        except Exception as e:
            logger.error(f"Error getting card {card_id}: {str(e)}")
            return None
    
    async def bind_card_to_user(self, user_id: int, card_id: str) -> Dict[str, Any]:
        """
        Bind card to user according to TZ.
        
        Args:
            user_id: Telegram user ID
            card_id: Card ID
            
        Returns:
            dict: Binding result
        """
        try:
            conn = await self.get_connection()
            try:
                # Check if card exists
                card = await self.get_card(card_id)
                if not card:
                    return {
                        'success': False,
                        'message': 'Карта не найдена в системе',
                        'error_code': 'card_not_found'
                    }
                
                # Check if card is blocked
                if card.get('is_blocked'):
                    return {
                        'success': False,
                        'message': 'Карта заблокирована',
                        'error_code': 'card_blocked'
                    }
                
                # Check if card is deleted
                if card.get('is_deleted'):
                    return {
                        'success': False,
                        'message': 'Карта удалена',
                        'error_code': 'card_deleted'
                    }
                
                # Check if card is already bound
                existing_binding = await conn.fetchrow("""
                    SELECT telegram_id FROM cards_binding WHERE card_id = $1
                """, card_id)
                
                if existing_binding:
                    if existing_binding['telegram_id'] == user_id:
                        return {
                            'success': False,
                            'message': 'Эта карта уже привязана к вашему аккаунту',
                            'error_code': 'already_bound_to_user'
                        }
                    else:
                        return {
                            'success': False,
                            'message': 'Карта уже привязана к другому аккаунту',
                            'error_code': 'bound_to_other_user'
                        }
                
                # Bind card to user
                await conn.execute("""
                    INSERT INTO cards_binding 
                    (telegram_id, card_id, card_id_printable, qr_url, bound_at, status, created_at)
                    VALUES ($1, $2, $3, $4, NOW(), 'active', NOW())
                """, user_id, card_id, card['card_id_printable'], card['qr_url'])
                
                # Award karma bonus for card binding
                from core.services.user_service import karma_service
                await karma_service.add_karma(
                    user_id, 
                    settings.karma.card_bind_bonus, 
                    f"Привязка карты {card['card_id_printable']}", 
                    "bonus"
                )
                
                # Add notification
                await conn.execute("""
                    INSERT INTO user_notifications 
                    (user_id, message, notification_type, created_at)
                    VALUES ($1, $2, 'card_bound', NOW())
                """, user_id, f"💳 Карта {card['card_id_printable']} успешно привязана! Получено {settings.karma.card_bind_bonus} кармы")
                
                # Check achievements
                await self._check_card_achievements(user_id)
                
                logger.info(f"Card {card_id} bound to user {user_id}")
                
                return {
                    'success': True,
                    'message': f'Карта {card["card_id_printable"]} успешно привязана!',
                    'card_id_printable': card['card_id_printable'],
                    'karma_bonus': settings.karma.card_bind_bonus
                }
                
            finally:
                await conn.close()
        except Exception as e:
            logger.error(f"Error binding card {card_id} to user {user_id}: {str(e)}")
            return {
                'success': False,
                'message': f'Ошибка при привязке карты: {str(e)}',
                'error_code': 'binding_error'
            }
    
    async def get_user_cards(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get all cards bound to user.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            list: List of user's cards
        """
        try:
            conn = await self.get_connection()
            try:
                cards = await conn.fetch("""
                    SELECT cb.*, cg.is_blocked, cg.is_deleted
                    FROM cards_binding cb
                    LEFT JOIN cards_generated cg ON cb.card_id = cg.card_id
                    WHERE cb.telegram_id = $1 AND cb.status = 'active'
                    ORDER BY cb.bound_at DESC
                """, user_id)
                
                return [dict(card) for card in cards]
            finally:
                await conn.close()
        except Exception as e:
            logger.error(f"Error getting cards for user {user_id}: {str(e)}")
            return []
    
    async def block_card(self, card_id: str, reason: str, blocked_by: int) -> Dict[str, Any]:
        """
        Block card according to TZ.
        
        Args:
            card_id: Card ID
            reason: Block reason
            blocked_by: Admin who blocked the card
            
        Returns:
            dict: Blocking result
        """
        try:
            conn = await self.get_connection()
            try:
                # Check if card exists
                card = await self.get_card(card_id)
                if not card:
                    return {
                        'success': False,
                        'message': 'Карта не найдена',
                        'error_code': 'card_not_found'
                    }
                
                # Check if already blocked
                if card.get('is_blocked'):
                    return {
                        'success': False,
                        'message': 'Карта уже заблокирована',
                        'error_code': 'already_blocked'
                    }
                
                # Block card
                await conn.execute("""
                    UPDATE cards_generated 
                    SET is_blocked = TRUE, block_reason = $1, blocked_by = $2, blocked_at = NOW()
                    WHERE card_id = $3
                """, reason, blocked_by, card_id)
                
                # Log admin action
                await conn.execute("""
                    INSERT INTO admin_logs 
                    (admin_id, action, target_card_id, details, created_at)
                    VALUES ($1, 'block_card', $2, $3, NOW())
                """, blocked_by, card_id, f"Блокировка карты, причина: {reason}")
                
                # Notify card owner if bound
                card_binding = await conn.fetchrow("""
                    SELECT telegram_id FROM cards_binding WHERE card_id = $1
                """, card_id)
                
                if card_binding:
                    await conn.execute("""
                        INSERT INTO user_notifications 
                        (user_id, message, notification_type, created_at)
                        VALUES ($1, $2, 'system', NOW())
                    """, card_binding['telegram_id'], f"🔒 Карта {card['card_id_printable']} заблокирована. Причина: {reason}")
                
                logger.info(f"Card {card_id} blocked by admin {blocked_by}")
                
                return {
                    'success': True,
                    'message': f'Карта {card["card_id_printable"]} заблокирована',
                    'card_id_printable': card['card_id_printable']
                }
                
            finally:
                await conn.close()
        except Exception as e:
            logger.error(f"Error blocking card {card_id}: {str(e)}")
            return {
                'success': False,
                'message': f'Ошибка при блокировке карты: {str(e)}',
                'error_code': 'blocking_error'
            }
    
    async def _check_card_achievements(self, user_id: int):
        """Check and award card-related achievements"""
        try:
            conn = await self.get_connection()
            try:
                # Get user's card count
                card_count = await conn.fetchval("""
                    SELECT COUNT(*) FROM cards_binding 
                    WHERE telegram_id = $1 AND status = 'active'
                """, user_id)
                
                # First card achievement
                if card_count == 1:
                    existing = await conn.fetchrow("""
                        SELECT id FROM user_achievements 
                        WHERE user_id = $1 AND achievement_type = 'first_card'
                    """, user_id)
                    
                    if not existing:
                        await conn.execute("""
                            INSERT INTO user_achievements (user_id, achievement_type, achievement_data, earned_at)
                            VALUES ($1, 'first_card', $2, NOW())
                        """, user_id, '{"card_count": 1}')
                        
                        await conn.execute("""
                            INSERT INTO user_notifications (user_id, message, notification_type, created_at)
                            VALUES ($1, $2, 'achievement', NOW())
                        """, user_id, "🎉 Первая карта привязана!")
                        
                        logger.info(f"First card achievement awarded to user {user_id}")
                
                # Multiple cards achievements
                elif card_count in [5, 10, 25]:
                    existing = await conn.fetchrow("""
                        SELECT id FROM user_achievements 
                        WHERE user_id = $1 AND achievement_type = 'card_collector' 
                        AND achievement_data::json->>'card_count' = $2
                    """, user_id, str(card_count))
                    
                    if not existing:
                        await conn.execute("""
                            INSERT INTO user_achievements (user_id, achievement_type, achievement_data, earned_at)
                            VALUES ($1, 'card_collector', $2, NOW())
                        """, user_id, f'{{"card_count": {card_count}}}')
                        
                        await conn.execute("""
                            INSERT INTO user_notifications (user_id, message, notification_type, created_at)
                            VALUES ($1, $2, 'achievement', NOW())
                        """, user_id, f"🏆 Коллекционер карт: {card_count} карт!")
                        
                        logger.info(f"Card collector achievement awarded to user {user_id} for {card_count} cards")
            finally:
                await conn.close()
        except Exception as e:
            logger.error(f"Error checking card achievements for user {user_id}: {str(e)}")


# Create singleton instance
card_service = CardService()


# Export functions
__all__ = [
    'CardService',
    'card_service',
    'generate_card_id',
    'generate_card_id_printable',
    'generate_qr_url'
]
