"""
Enhanced Moderation Service for KARMABOT1
Handles card moderation, queue management, and automated rules
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_, func, desc
from sqlalchemy.orm import selectinload

from core.database import get_db
from core.logger import get_logger
from core.models.card import Card
from core.models.partner import Partner, ModerationLog
from core.common.exceptions import NotFoundError, ValidationError, BusinessLogicError

logger = get_logger(__name__)

class ModerationService:
    """Service for managing card moderation and queue"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_pending_cards(
        self, 
        limit: int = 20, 
        assigned_to: Optional[int] = None,
        priority_min: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get cards pending moderation
        
        Args:
            limit: Maximum number of cards to return
            assigned_to: Filter by assigned moderator
            priority_min: Minimum priority level
            
        Returns:
            List of pending cards with details
        """
        try:
            query = select(Card).where(
                and_(
                    Card.status == 'pending',
                    Card.priority_level >= priority_min
                )
            ).order_by(desc(Card.priority_level), Card.created_at)
            
            if assigned_to:
                # This would require a join with moderation_queue table
                # For now, we'll implement basic filtering
                pass
            
            result = await self.db.execute(query.limit(limit))
            cards = result.scalars().all()
            
            return [self._format_card_for_moderation(card) for card in cards]
            
        except Exception as e:
            logger.error(f"Error getting pending cards: {e}")
            raise
    
    async def approve_card(
        self, 
        card_id: int, 
        moderator_id: int, 
        comment: Optional[str] = None,
        mark_featured: bool = False
    ) -> Dict[str, Any]:
        """
        Approve a card for publication
        
        Args:
            card_id: ID of the card to approve
            moderator_id: ID of the moderator
            comment: Optional approval comment
            mark_featured: Whether to mark as featured
            
        Returns:
            Approval result
        """
        try:
            # Get card
            result = await self.db.execute(
                select(Card).where(Card.id == card_id)
            )
            card = result.scalar_one_or_none()
            
            if not card:
                raise NotFoundError("Card not found")
            
            if card.status != 'pending':
                raise BusinessLogicError(f"Card is not pending (status: {card.status})")
            
            # Update card status
            update_data = {
                'status': 'published',
                'updated_at': datetime.utcnow()
            }
            
            if mark_featured:
                update_data['is_featured'] = True
                update_data['priority_level'] = 100
            
            await self.db.execute(
                update(Card)
                .where(Card.id == card_id)
                .values(**update_data)
            )
            
            # Log moderation action
            moderation_log = ModerationLog(
                moderator_id=moderator_id,
                card_id=card_id,
                action='approve',
                comment=comment or 'Card approved',
                reason_code=None
            )
            self.db.add(moderation_log)
            
            # Update statistics
            await self._update_moderation_stats(moderator_id, 'approve')
            
            await self.db.commit()
            
            logger.info(f"Card {card_id} approved by moderator {moderator_id}")
            
            return {
                "success": True,
                "card_id": card_id,
                "status": "published",
                "featured": mark_featured,
                "message": "Card approved successfully"
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error approving card {card_id}: {e}")
            raise
    
    async def reject_card(
        self, 
        card_id: int, 
        moderator_id: int, 
        reason: str,
        reason_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Reject a card
        
        Args:
            card_id: ID of the card to reject
            moderator_id: ID of the moderator
            reason: Rejection reason
            reason_code: Standardized reason code
            
        Returns:
            Rejection result
        """
        try:
            # Get card
            result = await self.db.execute(
                select(Card).where(Card.id == card_id)
            )
            card = result.scalar_one_or_none()
            
            if not card:
                raise NotFoundError("Card not found")
            
            if card.status != 'pending':
                raise BusinessLogicError(f"Card is not pending (status: {card.status})")
            
            # Update card status
            await self.db.execute(
                update(Card)
                .where(Card.id == card_id)
                .values(
                    status='rejected',
                    moderation_notes=reason,
                    updated_at=datetime.utcnow()
                )
            )
            
            # Log moderation action
            moderation_log = ModerationLog(
                moderator_id=moderator_id,
                card_id=card_id,
                action='reject',
                comment=reason,
                reason_code=reason_code
            )
            self.db.add(moderation_log)
            
            # Update statistics
            await self._update_moderation_stats(moderator_id, 'reject')
            
            await self.db.commit()
            
            logger.info(f"Card {card_id} rejected by moderator {moderator_id}: {reason}")
            
            return {
                "success": True,
                "card_id": card_id,
                "status": "rejected",
                "reason": reason,
                "message": "Card rejected successfully"
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error rejecting card {card_id}: {e}")
            raise
    
    async def feature_card(
        self, 
        card_id: int, 
        moderator_id: int, 
        comment: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Mark a card as featured
        
        Args:
            card_id: ID of the card to feature
            moderator_id: ID of the moderator
            comment: Optional comment
            
        Returns:
            Feature result
        """
        try:
            # Get card
            result = await self.db.execute(
                select(Card).where(Card.id == card_id)
            )
            card = result.scalar_one_or_none()
            
            if not card:
                raise NotFoundError("Card not found")
            
            # Update card
            await self.db.execute(
                update(Card)
                .where(Card.id == card_id)
                .values(
                    is_featured=True,
                    priority_level=100,
                    status='published',
                    updated_at=datetime.utcnow()
                )
            )
            
            # Log moderation action
            moderation_log = ModerationLog(
                moderator_id=moderator_id,
                card_id=card_id,
                action='feature',
                comment=comment or 'Card featured',
                reason_code=None
            )
            self.db.add(moderation_log)
            
            # Update statistics
            await self._update_moderation_stats(moderator_id, 'feature')
            
            await self.db.commit()
            
            logger.info(f"Card {card_id} featured by moderator {moderator_id}")
            
            return {
                "success": True,
                "card_id": card_id,
                "featured": True,
                "message": "Card featured successfully"
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error featuring card {card_id}: {e}")
            raise
    
    async def archive_card(
        self, 
        card_id: int, 
        moderator_id: int, 
        comment: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Archive a card
        
        Args:
            card_id: ID of the card to archive
            moderator_id: ID of the moderator
            comment: Optional comment
            
        Returns:
            Archive result
        """
        try:
            # Get card
            result = await self.db.execute(
                select(Card).where(Card.id == card_id)
            )
            card = result.scalar_one_or_none()
            
            if not card:
                raise NotFoundError("Card not found")
            
            # Update card status
            await self.db.execute(
                update(Card)
                .where(Card.id == card_id)
                .values(
                    status='archived',
                    updated_at=datetime.utcnow()
                )
            )
            
            # Log moderation action
            moderation_log = ModerationLog(
                moderator_id=moderator_id,
                card_id=card_id,
                action='archive',
                comment=comment or 'Card archived',
                reason_code=None
            )
            self.db.add(moderation_log)
            
            # Update statistics
            await self._update_moderation_stats(moderator_id, 'archive')
            
            await self.db.commit()
            
            logger.info(f"Card {card_id} archived by moderator {moderator_id}")
            
            return {
                "success": True,
                "card_id": card_id,
                "status": "archived",
                "message": "Card archived successfully"
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error archiving card {card_id}: {e}")
            raise
    
    async def get_moderation_stats(
        self, 
        moderator_id: Optional[int] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get moderation statistics
        
        Args:
            moderator_id: Filter by specific moderator
            days: Number of days to include
            
        Returns:
            Moderation statistics
        """
        try:
            # Base query for moderation logs
            query = select(ModerationLog).where(
                ModerationLog.created_at >= datetime.utcnow() - timedelta(days=days)
            )
            
            if moderator_id:
                query = query.where(ModerationLog.moderator_id == moderator_id)
            
            result = await self.db.execute(query)
            logs = result.scalars().all()
            
            # Calculate statistics
            stats = {
                "total_actions": len(logs),
                "approvals": sum(1 for log in logs if log.action == 'approve'),
                "rejections": sum(1 for log in logs if log.action == 'reject'),
                "features": sum(1 for log in logs if log.action == 'feature'),
                "archives": sum(1 for log in logs if log.action == 'archive'),
                "period_days": days
            }
            
            # Calculate approval rate
            if stats["total_actions"] > 0:
                stats["approval_rate"] = stats["approvals"] / stats["total_actions"]
            else:
                stats["approval_rate"] = 0
            
            # Get moderator performance if specific moderator
            if moderator_id:
                moderator_result = await self.db.execute(
                    select(Partner).where(Partner.id == moderator_id)
                )
                moderator = moderator_result.scalar_one_or_none()
                if moderator:
                    stats["moderator_name"] = moderator.name
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting moderation stats: {e}")
            raise
    
    async def get_moderation_queue_status(self) -> Dict[str, Any]:
        """
        Get current moderation queue status
        
        Returns:
            Queue status information
        """
        try:
            # Count cards by status
            pending_result = await self.db.execute(
                select(func.count(Card.id)).where(Card.status == 'pending')
            )
            pending_count = pending_result.scalar()
            
            published_result = await self.db.execute(
                select(func.count(Card.id)).where(Card.status == 'published')
            )
            published_count = published_result.scalar()
            
            rejected_result = await self.db.execute(
                select(func.count(Card.id)).where(Card.status == 'rejected')
            )
            rejected_count = rejected_result.scalar()
            
            # Get recent activity
            recent_result = await self.db.execute(
                select(ModerationLog)
                .order_by(desc(ModerationLog.created_at))
                .limit(10)
            )
            recent_logs = recent_result.scalars().all()
            
            return {
                "pending_cards": pending_count,
                "published_cards": published_count,
                "rejected_cards": rejected_count,
                "recent_activity": [
                    {
                        "action": log.action,
                        "card_id": log.card_id,
                        "moderator_id": log.moderator_id,
                        "created_at": log.created_at.isoformat(),
                        "comment": log.comment
                    }
                    for log in recent_logs
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting queue status: {e}")
            raise
    
    async def apply_automated_rules(self, card_id: int) -> Dict[str, Any]:
        """
        Apply automated moderation rules to a card
        
        Args:
            card_id: ID of the card to check
            
        Returns:
            Rule application result
        """
        try:
            # Get card
            result = await self.db.execute(
                select(Card).where(Card.id == card_id)
            )
            card = result.scalar_one_or_none()
            
            if not card:
                raise NotFoundError("Card not found")
            
            # This would implement automated rule checking
            # For now, we'll return a basic result
            return {
                "success": True,
                "card_id": card_id,
                "rules_applied": [],
                "auto_action": None,
                "message": "Automated rules checked"
            }
            
        except Exception as e:
            logger.error(f"Error applying automated rules to card {card_id}: {e}")
            raise
    
    def _format_card_for_moderation(self, card: Card) -> Dict[str, Any]:
        """Format card data for moderation display"""
        return {
            "id": card.id,
            "title": card.title,
            "description": card.description,
            "status": card.status,
            "is_featured": getattr(card, 'is_featured', False),
            "priority_level": getattr(card, 'priority_level', 0),
            "created_at": card.created_at.isoformat() if card.created_at else None,
            "updated_at": card.updated_at.isoformat() if card.updated_at else None,
            "partner_id": card.partner_id,
            "category_id": card.category_id,
            "moderation_notes": getattr(card, 'moderation_notes', None)
        }
    
    async def _update_moderation_stats(self, moderator_id: int, action: str):
        """Update moderation statistics for a moderator"""
        try:
            # This would update the moderation_statistics table
            # For now, we'll just log the action
            logger.info(f"Updated stats for moderator {moderator_id}: {action}")
        except Exception as e:
            logger.error(f"Error updating moderation stats: {e}")

# Create service instance
moderation_service = ModerationService(None)  # Will be initialized with proper db session
