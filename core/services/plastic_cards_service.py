"""
Service layer for plastic cards functionality.
Handles card binding, validation, management, and generation.
"""
from typing import Optional, Dict, Any, List
import os
import asyncpg
from datetime import datetime
import csv
import io

from core.utils.logger import get_logger

logger = get_logger(__name__)

class PlasticCardsService:
    """Service class for plastic cards operations."""
    
    def __init__(self):
        """Initialize with database connection."""
        self.database_url = os.getenv("DATABASE_URL", "")
    
    async def get_connection(self) -> asyncpg.Connection:
        """Get database connection."""
        return await asyncpg.connect(self.database_url)
    
    async def bind_card_to_user(
        self, 
        telegram_id: int, 
        card_id: str, 
        card_id_printable: str = None,
        qr_url: str = None
    ) -> Dict[str, Any]:
        """
        Bind a plastic card to a Telegram user.
        
        Args:
            telegram_id: Telegram user ID
            card_id: Unique card identifier
            card_id_printable: Human-readable card ID
            qr_url: QR code URL for the card
            
        Returns:
            dict: Result with success status and message
        """
        try:
            conn = await self.get_connection()
            try:
                # Check if card exists in generated cards
                card_exists = await conn.fetchrow(
                    "SELECT id FROM cards_generated WHERE card_id = $1 AND is_deleted = false",
                    card_id
                )
                if not card_exists:
                    return {
                        'success': False,
                        'message': 'Карта не найдена в системе.',
                        'error_code': 'card_not_found'
                    }
                
                # Check if user already has cards (ограничение до 1 карты)
                existing_cards_count = await conn.fetchval(
                    "SELECT COUNT(*) FROM cards_binding WHERE telegram_id = $1 AND status = 'active'",
                    telegram_id
                )
                
                if existing_cards_count >= 1:  # Лимит 1 карта
                    return {
                        'success': False,
                        'message': 'Вы можете привязать только одну карту к аккаунту.\n\nДля привязки новой карты сначала отвяжите текущую.',
                        'error_code': 'card_limit_reached'
                    }
                
                # Check if this specific card is already bound to someone else
                existing_binding = await conn.fetchrow(
                    "SELECT telegram_id FROM cards_binding WHERE card_id = $1 AND status = 'active'",
                    card_id
                )
                
                if existing_binding:
                    return {
                        'success': False,
                        'message': 'Эта карта уже привязана к другому пользователю.',
                        'error_code': 'bound_to_other_user'
                    }
                
                # Bind the card
                await conn.execute(
                    """
                    INSERT INTO cards_binding (telegram_id, card_id, card_id_printable, qr_url, status, created_at)
                    VALUES ($1, $2, $3, $4, 'active', $5)
                    """,
                    telegram_id, card_id, card_id_printable or card_id, qr_url, datetime.now()
                )
                
                return {
                    'success': True,
                    'message': f'Карта {card_id_printable or card_id} успешно привязана к вашему аккаунту!',
                    'card_id': card_id,
                    'card_id_printable': card_id_printable or card_id
                }
                
            finally:
                await conn.close()
                
        except Exception as e:
            logger.error(f"Error binding card {card_id} to user {telegram_id}: {str(e)}")
            return {
                'success': False,
                'message': 'Произошла ошибка при привязке карты. Попробуйте позже.',
                'error_code': 'binding_error'
            }
    
    async def get_user_cards(self, telegram_id: int) -> List[Dict[str, Any]]:
        """
        Get all cards bound to a user.
        
        Args:
            telegram_id: Telegram user ID
            
        Returns:
            list: List of bound cards
        """
        try:
            conn = await self.get_connection()
            try:
                rows = await conn.fetch("""
                    SELECT card_id, card_id_printable, qr_url, created_at, status
                    FROM cards_binding 
                    WHERE telegram_id = $1 AND status = 'active'
                    ORDER BY created_at DESC
                """, telegram_id)
                
                cards = []
                for row in rows:
                    cards.append({
                        'card_id': row['card_id'],
                        'card_id_printable': row['card_id_printable'],
                        'qr_url': row['qr_url'],
                        'bound_at': row['created_at'],
                        'status': row['status']
                    })
                
                return cards
            finally:
                await conn.close()
                
        except Exception as e:
            logger.error(f"Error getting cards for user {telegram_id}: {str(e)}")
            return []
    
    async def unbind_card(self, telegram_id: int, card_id: str) -> Dict[str, Any]:
        """
        Unbind a card from a user.
        
        Args:
            telegram_id: Telegram user ID
            card_id: Card ID to unbind
            
        Returns:
            dict: Result with success status and message
        """
        try:
            with self.get_connection() as conn:
                # Check if card is bound to this user
                cursor = conn.execute("""
                    SELECT telegram_id FROM cards_binding 
                    WHERE card_id = ? AND status = 'active'
                """, (card_id,))
                
                binding = cursor.fetchone()
                if not binding:
                    return {
                        'success': False,
                        'message': 'Карта не найдена или не привязана.',
                        'error_code': 'card_not_found'
                    }
                
                if binding['telegram_id'] != telegram_id:
                    return {
                        'success': False,
                        'message': 'Эта карта привязана к другому пользователю.',
                        'error_code': 'not_owner'
                    }
                
                # Unbind the card
                cursor = conn.execute("""
                    UPDATE cards_binding 
                    SET status = 'unbound', updated_at = CURRENT_TIMESTAMP
                    WHERE card_id = ? AND telegram_id = ?
                """, (card_id, telegram_id))
                
                conn.commit()
                
                return {
                    'success': True,
                    'message': f'Карта {card_id} успешно отвязана от вашего аккаунта.'
                }
                
        except Exception as e:
            logger.error(f"Error unbinding card {card_id} from user {telegram_id}: {str(e)}")
            return {
                'success': False,
                'message': 'Произошла ошибка при отвязке карты. Попробуйте позже.',
                'error_code': 'database_error'
            }
    
    async def validate_card_id(self, card_id: str) -> bool:
        """
        Validate card ID format.
        
        Args:
            card_id: Card ID to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not card_id or len(card_id) < 3 or len(card_id) > 20:
            return False
        
        # Check if card ID contains only alphanumeric characters
        return card_id.replace('-', '').replace('_', '').isalnum()
    
    async def generate_cards(self, count: int, created_by: int) -> Dict[str, Any]:
        """
        Generate new plastic cards (Super Admin only).
        
        Args:
            count: Number of cards to generate
            created_by: Admin who created the cards
            
        Returns:
            dict: Result with success status and CSV data
        """
        try:
            with self.get_connection() as conn:
                # Get the last card ID to continue sequence
                cursor = conn.execute(
                    "SELECT card_id FROM cards_generated ORDER BY id DESC LIMIT 1"
                )
                last_card = cursor.fetchone()
                
                if last_card:
                    # Extract number from last card ID (e.g., KS12340001 -> 12340001)
                    last_number = int(last_card['card_id'][2:])  # Remove 'KS' prefix
                    start_number = last_number + 1
                else:
                    start_number = 12340001  # Starting number
                
                generated_cards = []
                
                for i in range(count):
                    card_number = start_number + i
                    card_id = f"KS{card_number}"
                    card_id_printable = f"KS-{str(card_number)[:4]}-{str(card_number)[4:]}"
                    qr_url = f"https://t.me/KarmaQRBot?startapp=bind&cid={card_id}"
                    
                    # Insert into cards_generated table
                    conn.execute("""
                        INSERT INTO cards_generated 
                        (card_id, card_id_printable, qr_url, created_by, created_at)
                        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """, (card_id, card_id_printable, qr_url, created_by))
                    
                    generated_cards.append({
                        'card_id': card_id,
                        'card_id_printable': card_id_printable,
                        'qr_url': qr_url
                    })
                
                conn.commit()
                
                # Generate CSV content
                csv_content = self._generate_csv(generated_cards)
                
                return {
                    'success': True,
                    'message': f'Успешно сгенерировано {count} карт.',
                    'cards': generated_cards,
                    'csv_content': csv_content
                }
                
        except Exception as e:
            logger.error(f"Error generating cards: {str(e)}")
            return {
                'success': False,
                'message': 'Произошла ошибка при генерации карт.',
                'error_code': 'database_error'
            }
    
    def _generate_csv(self, cards: List[Dict[str, Any]]) -> str:
        """Generate CSV content for cards."""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['card_id', 'card_id_printable', 'qr_url'])
        
        # Write card data
        for card in cards:
            writer.writerow([
                card['card_id'],
                card['card_id_printable'],
                card['qr_url']
            ])
        
        return output.getvalue()
    
    async def block_card(self, card_id: str, admin_id: int, reason: str = "") -> Dict[str, Any]:
        """
        Block a card (Admin/Super Admin only).
        
        Args:
            card_id: Card ID to block
            admin_id: Admin who blocked the card
            reason: Reason for blocking
            
        Returns:
            dict: Result with success status and message
        """
        try:
            with self.get_connection() as conn:
                # Check if card exists
                cursor = conn.execute(
                    "SELECT id FROM cards_generated WHERE card_id = ?",
                    (card_id,)
                )
                if not cursor.fetchone():
                    return {
                        'success': False,
                        'message': 'Карта не найдена в системе.',
                        'error_code': 'card_not_found'
                    }
                
                # Block the card
                conn.execute("""
                    UPDATE cards_generated 
                    SET is_blocked = 1, updated_at = CURRENT_TIMESTAMP
                    WHERE card_id = ?
                """, (card_id,))
                
                # Log admin action
                conn.execute("""
                    INSERT INTO admin_logs 
                    (admin_id, action, target_id, reason, created_at)
                    VALUES (?, 'block_card', ?, ?, CURRENT_TIMESTAMP)
                """, (admin_id, card_id, reason))
                
                conn.commit()
                
                return {
                    'success': True,
                    'message': f'Карта {card_id} заблокирована.'
                }
                
        except Exception as e:
            logger.error(f"Error blocking card {card_id}: {str(e)}")
            return {
                'success': False,
                'message': 'Произошла ошибка при блокировке карты.',
                'error_code': 'database_error'
            }
    
    async def delete_card(self, card_id: str, admin_id: int, reason: str = "") -> Dict[str, Any]:
        """
        Delete a card (Super Admin only).
        
        Args:
            card_id: Card ID to delete
            admin_id: Admin who deleted the card
            reason: Reason for deletion
            
        Returns:
            dict: Result with success status and message
        """
        try:
            with self.get_connection() as conn:
                # Check if card exists
                cursor = conn.execute(
                    "SELECT id FROM cards_generated WHERE card_id = ?",
                    (card_id,)
                )
                if not cursor.fetchone():
                    return {
                        'success': False,
                        'message': 'Карта не найдена в системе.',
                        'error_code': 'card_not_found'
                    }
                
                # Soft delete the card
                conn.execute("""
                    UPDATE cards_generated 
                    SET is_deleted = 1, updated_at = CURRENT_TIMESTAMP
                    WHERE card_id = ?
                """, (card_id,))
                
                # Log admin action
                conn.execute("""
                    INSERT INTO admin_logs 
                    (admin_id, action, target_id, reason, created_at)
                    VALUES (?, 'delete_card', ?, ?, CURRENT_TIMESTAMP)
                """, (admin_id, card_id, reason))
                
                conn.commit()
                
                return {
                    'success': True,
                    'message': f'Карта {card_id} удалена.'
                }
                
        except Exception as e:
            logger.error(f"Error deleting card {card_id}: {str(e)}")
            return {
                'success': False,
                'message': 'Произошла ошибка при удалении карты.',
                'error_code': 'database_error'
            }

# Create a singleton instance for easy import
plastic_cards_service = PlasticCardsService()
