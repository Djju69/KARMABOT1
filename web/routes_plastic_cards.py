"""
API routes for plastic cards functionality.
Provides REST API endpoints for card management.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any
import logging

from core.services.plastic_cards_service import plastic_cards_service
from core.security.auth import get_current_user

router = APIRouter(prefix="/api/cards", tags=["plastic-cards"])
logger = logging.getLogger(__name__)


@router.get("/user/{telegram_id}")
async def get_user_cards(
    telegram_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get all cards bound to a specific user.
    
    Args:
        telegram_id: Telegram user ID
        current_user: Current authenticated user
        
    Returns:
        dict: User's bound cards
    """
    try:
        # Check if user is requesting their own cards or is admin
        if current_user.get('telegram_id') != telegram_id and not current_user.get('is_admin'):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You can only view your own cards."
            )
        
        cards = await plastic_cards_service.get_user_cards(telegram_id)
        
        return {
            "success": True,
            "telegram_id": telegram_id,
            "cards": cards,
            "total_cards": len(cards),
            "max_cards": 5
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting cards for user {telegram_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/bind")
async def bind_card(
    telegram_id: int,
    card_id: str,
    card_id_printable: str = None,
    qr_url: str = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Bind a card to a user.
    
    Args:
        telegram_id: Telegram user ID
        card_id: Card identifier
        card_id_printable: Human-readable card ID
        qr_url: QR code URL
        current_user: Current authenticated user
        
    Returns:
        dict: Binding result
    """
    try:
        # Check if user is binding to their own account or is admin
        if current_user.get('telegram_id') != telegram_id and not current_user.get('is_admin'):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You can only bind cards to your own account."
            )
        
        result = await plastic_cards_service.bind_card_to_user(
            telegram_id=telegram_id,
            card_id=card_id,
            card_id_printable=card_id_printable,
            qr_url=qr_url
        )
        
        if not result['success']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result['message']
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error binding card {card_id} to user {telegram_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.delete("/unbind")
async def unbind_card(
    telegram_id: int,
    card_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Unbind a card from a user.
    
    Args:
        telegram_id: Telegram user ID
        card_id: Card identifier
        current_user: Current authenticated user
        
    Returns:
        dict: Unbinding result
    """
    try:
        # Check if user is unbinding from their own account or is admin
        if current_user.get('telegram_id') != telegram_id and not current_user.get('is_admin'):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You can only unbind cards from your own account."
            )
        
        result = await plastic_cards_service.unbind_card(telegram_id, card_id)
        
        if not result['success']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result['message']
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unbinding card {card_id} from user {telegram_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/validate/{card_id}")
async def validate_card_id(card_id: str) -> Dict[str, Any]:
    """
    Validate card ID format.
    
    Args:
        card_id: Card identifier to validate
        
    Returns:
        dict: Validation result
    """
    try:
        is_valid = await plastic_cards_service.validate_card_id(card_id)
        
        return {
            "success": True,
            "card_id": card_id,
            "is_valid": is_valid,
            "message": "Card ID is valid" if is_valid else "Card ID format is invalid"
        }
        
    except Exception as e:
        logger.error(f"Error validating card ID {card_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
