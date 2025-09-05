"""
Moderation API endpoints for WebApp
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import HTMLResponse
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime, timedelta

from core.database import get_db
from core.services.moderation_service import ModerationService
from core.services.admins import admins_service
from core.auth import get_current_user
from core.models.card import Card
from core.models.partner import ModerationLog
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/moderation", tags=["Moderation"])

class ModerationActionRequest:
    """Request model for moderation actions"""
    reason: Optional[str] = None
    comment: Optional[str] = None

class ModerationStatsResponse:
    """Response model for moderation statistics"""
    pending_cards: int
    published_cards: int
    rejected_cards: int
    approval_rate: float
    recent_activity: List[Dict[str, Any]]

@router.get("/dashboard", response_class=HTMLResponse)
async def moderation_dashboard():
    """Serve moderation dashboard WebApp page"""
    try:
        with open("web/templates/moderation-dashboard.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Moderation dashboard page not found"
        )

@router.get("/stats")
async def get_moderation_stats(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ModerationStatsResponse:
    """
    Get moderation statistics
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Moderation statistics
    """
    try:
        # Check if user is admin
        if not await admins_service.is_admin(current_user["user_id"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Admin privileges required."
            )
        
        moderation_service = ModerationService(db)
        
        # Get overall stats
        stats = await moderation_service.get_moderation_stats(days=30)
        queue_status = await moderation_service.get_moderation_queue_status()
        
        return ModerationStatsResponse(
            pending_cards=queue_status["pending_cards"],
            published_cards=queue_status["published_cards"],
            rejected_cards=queue_status["rejected_cards"],
            approval_rate=stats["approval_rate"],
            recent_activity=queue_status["recent_activity"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting moderation stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get moderation statistics"
        )

@router.get("/cards")
async def get_moderation_cards(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    filter: str = Query("all", regex="^(all|pending|published|rejected|featured)$"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get cards for moderation
    
    Args:
        page: Page number
        limit: Number of cards per page
        filter: Filter by status
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of cards with pagination info
    """
    try:
        # Check if user is admin
        if not await admins_service.is_admin(current_user["user_id"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Admin privileges required."
            )
        
        moderation_service = ModerationService(db)
        
        # Calculate offset
        offset = (page - 1) * limit
        
        # Get cards based on filter
        if filter == "all":
            cards = await moderation_service.get_pending_cards(limit=limit)
        else:
            # This would implement filtering by status
            cards = await moderation_service.get_pending_cards(limit=limit)
        
        # Get total count for pagination
        total_result = await db.execute(
            select(func.count(Card.id)).where(Card.status == 'pending')
        )
        total = total_result.scalar()
        
        return {
            "cards": cards,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting moderation cards: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get moderation cards"
        )

@router.post("/approve/{card_id}")
async def approve_card(
    card_id: int,
    request: ModerationActionRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Approve a card for publication
    
    Args:
        card_id: ID of the card to approve
        request: Approval request with optional comment
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Approval result
    """
    try:
        # Check if user is admin
        if not await admins_service.is_admin(current_user["user_id"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Admin privileges required."
            )
        
        moderation_service = ModerationService(db)
        
        result = await moderation_service.approve_card(
            card_id=card_id,
            moderator_id=current_user["user_id"],
            comment=request.comment or "Approved via WebApp"
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving card {card_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to approve card"
        )

@router.post("/reject/{card_id}")
async def reject_card(
    card_id: int,
    request: ModerationActionRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Reject a card
    
    Args:
        card_id: ID of the card to reject
        request: Rejection request with reason
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Rejection result
    """
    try:
        # Check if user is admin
        if not await admins_service.is_admin(current_user["user_id"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Admin privileges required."
            )
        
        if not request.reason:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Rejection reason is required"
            )
        
        moderation_service = ModerationService(db)
        
        result = await moderation_service.reject_card(
            card_id=card_id,
            moderator_id=current_user["user_id"],
            reason=request.reason,
            reason_code="custom"
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rejecting card {card_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reject card"
        )

@router.post("/feature/{card_id}")
async def feature_card(
    card_id: int,
    request: ModerationActionRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Mark a card as featured
    
    Args:
        card_id: ID of the card to feature
        request: Feature request with optional comment
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Feature result
    """
    try:
        # Check if user is admin
        if not await admins_service.is_admin(current_user["user_id"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Admin privileges required."
            )
        
        moderation_service = ModerationService(db)
        
        result = await moderation_service.feature_card(
            card_id=card_id,
            moderator_id=current_user["user_id"],
            comment=request.comment or "Featured via WebApp"
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error featuring card {card_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to feature card"
        )

@router.post("/archive/{card_id}")
async def archive_card(
    card_id: int,
    request: ModerationActionRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Archive a card
    
    Args:
        card_id: ID of the card to archive
        request: Archive request with optional comment
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Archive result
    """
    try:
        # Check if user is admin
        if not await admins_service.is_admin(current_user["user_id"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Admin privileges required."
            )
        
        moderation_service = ModerationService(db)
        
        result = await moderation_service.archive_card(
            card_id=card_id,
            moderator_id=current_user["user_id"],
            comment=request.comment or "Archived via WebApp"
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error archiving card {card_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to archive card"
        )

@router.get("/logs")
async def get_moderation_logs(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    moderator_id: Optional[int] = Query(None),
    action: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get moderation logs
    
    Args:
        page: Page number
        limit: Number of logs per page
        moderator_id: Filter by moderator
        action: Filter by action type
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of moderation logs with pagination
    """
    try:
        # Check if user is admin
        if not await admins_service.is_admin(current_user["user_id"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Admin privileges required."
            )
        
        # Build query
        query = select(ModerationLog).order_by(desc(ModerationLog.created_at))
        
        if moderator_id:
            query = query.where(ModerationLog.moderator_id == moderator_id)
        
        if action:
            query = query.where(ModerationLog.action == action)
        
        # Apply pagination
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)
        
        result = await db.execute(query)
        logs = result.scalars().all()
        
        # Get total count
        count_query = select(func.count(ModerationLog.id))
        if moderator_id:
            count_query = count_query.where(ModerationLog.moderator_id == moderator_id)
        if action:
            count_query = count_query.where(ModerationLog.action == action)
        
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        return {
            "logs": [
                {
                    "id": log.id,
                    "moderator_id": log.moderator_id,
                    "card_id": log.card_id,
                    "action": log.action,
                    "comment": log.comment,
                    "reason_code": log.reason_code,
                    "created_at": log.created_at.isoformat()
                }
                for log in logs
            ],
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting moderation logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get moderation logs"
        )

@router.get("/queue/status")
async def get_queue_status(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get moderation queue status
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Queue status information
    """
    try:
        # Check if user is admin
        if not await admins_service.is_admin(current_user["user_id"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Admin privileges required."
            )
        
        moderation_service = ModerationService(db)
        queue_status = await moderation_service.get_moderation_queue_status()
        
        return queue_status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting queue status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get queue status"
        )

@router.post("/bulk/approve")
async def bulk_approve_cards(
    card_ids: List[int],
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Bulk approve multiple cards
    
    Args:
        card_ids: List of card IDs to approve
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Bulk approval result
    """
    try:
        # Check if user is admin
        if not await admins_service.is_admin(current_user["user_id"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Admin privileges required."
            )
        
        moderation_service = ModerationService(db)
        
        results = []
        for card_id in card_ids:
            try:
                result = await moderation_service.approve_card(
                    card_id=card_id,
                    moderator_id=current_user["user_id"],
                    comment="Bulk approved via WebApp"
                )
                results.append({"card_id": card_id, "success": True, "result": result})
            except Exception as e:
                results.append({"card_id": card_id, "success": False, "error": str(e)})
        
        successful = sum(1 for r in results if r["success"])
        
        return {
            "total": len(card_ids),
            "successful": successful,
            "failed": len(card_ids) - successful,
            "results": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in bulk approve: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to bulk approve cards"
        )

@router.post("/rules/apply/{card_id}")
async def apply_moderation_rules(
    card_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Apply automated moderation rules to a card
    
    Args:
        card_id: ID of the card to check
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Rule application result
    """
    try:
        # Check if user is admin
        if not await admins_service.is_admin(current_user["user_id"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Admin privileges required."
            )
        
        moderation_service = ModerationService(db)
        result = await moderation_service.apply_automated_rules(card_id)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error applying rules to card {card_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to apply moderation rules"
        )
