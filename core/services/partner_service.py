"""
Partner service module for handling partner-related operations.
Including card management, statistics, and QR code operations.
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session, joinedload
Feedback submitted


from sqlalchemy import func, and_, or_
from core.database.db_v2 import get_db
from core.models import User, Card, QRScan, Transaction


async def count_approved_partner_cards(partner_id: int) -> int:
    """
    Count the number of approved cards for a partner.
    
    Args:
        partner_id: Telegram user ID of the partner
        
    Returns:
        int: Number of approved cards
    """
    with get_db() as db:
        count = db.query(Card).filter(
            Card.partner_id == partner_id,
            Card.status == 'approved'
        ).count()
        return count


async def get_partner_cards_with_filter(
    partner_id: int,
    filter_type: str = "all",
    page: int = 1,
    per_page: int = 10
) -> Dict[str, Any]:
    """
    Get partner's cards with optional filtering and pagination.
    
    Args:
        partner_id: Telegram user ID of the partner
        filter_type: Type of cards to filter ('all', 'restaurant', 'spa', 'car', 'hotel', 'tour')
        page: Page number (1-based)
        per_page: Items per page
        
    Returns:
        Dict containing cards and pagination info
    """
    with get_db() as db:
        query = db.query(Card).filter(Card.partner_id == partner_id)
        
        # Apply filters
        if filter_type != "all":
            query = query.filter(Card.card_type == filter_type)
        
        # Count total items
        total = query.count()
        total_pages = (total + per_page - 1) // per_page
        
        # Apply pagination
        cards = (
            query.order_by(Card.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        
        return {
            "cards": cards,
            "total": total,
            "total_pages": total_pages,
            "current_page": page,
            "has_next": page < total_pages,
            "has_previous": page > 1
        }


async def get_partner_statistics(partner_id: int) -> Dict[str, Any]:
    """
    Get partner statistics including cards, views, and scans.
    
    Args:
        partner_id: Telegram user ID of the partner
        
    Returns:
        Dict containing various statistics
    """
    with get_db() as db:
        # Card statistics
        card_stats = db.query(
            func.count(Card.id).label("total_cards"),
            func.sum(case([(Card.status == 'approved', 1)], else_=0)).label("active_cards"),
            func.sum(Card.views).label("total_views"),
            func.sum(Card.scans).label("total_scans")
        ).filter(Card.partner_id == partner_id).first()
        
        # Recent scans (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_scans = db.query(QRScan).filter(
            QRScan.card_id.in_(
                db.query(Card.id).filter(Card.partner_id == partner_id)
            ),
            QRScan.scan_time >= thirty_days_ago
        ).count()
        
        # Popular cards
        popular_cards = db.query(
            Card.title,
            Card.views,
            Card.scans
        ).filter(
            Card.partner_id == partner_id,
            Card.status == 'approved'
        ).order_by(Card.views.desc()).limit(5).all()
        
        # Calculate conversion rate (scans/views)
        conversion_rate = 0.0
        if card_stats.total_views and card_stats.total_scans:
            conversion_rate = (card_stats.total_scans / card_stats.total_views) * 100
        
        return {
            "total_cards": card_stats.total_cards or 0,
            "active_cards": card_stats.active_cards or 0,
            "total_views": card_stats.total_views or 0,
            "total_scans": card_stats.total_scans or 0,
            "recent_scans": recent_scans,
            "conversion_rate": round(conversion_rate, 2),
            "popular_cards": [
                {
                    "title": card.title,
                    "views": card.views,
                    "scans": card.scans
                }
                for card in popular_cards
            ]
        }


async def register_scan(card_id: int, user_id: int) -> bool:
    """
    Register a QR code scan event.
    
    Args:
        card_id: ID of the scanned card
        user_id: Telegram user ID who scanned the code
        
    Returns:
        bool: True if scan was registered successfully
    """
    with get_db() as db:
        try:
            # Update card stats
            db.query(Card).filter(Card.id == card_id).update({
                'scans': Card.scans + 1,
                'last_scan': datetime.utcnow()
            })
            
            # Record the scan
            scan = QRScan(
                card_id=card_id,
                user_id=user_id,
                scan_time=datetime.utcnow(),
                is_used=False
            )
            db.add(scan)
            db.commit()
            return True
            
        except Exception as e:
            db.rollback()
            return False


async def get_card_by_qr(qr_data: str) -> Optional[Card]:
    """
    Get card by QR code data.
    
    Args:
        qr_data: Data from the QR code
        
    Returns:
        Optional[Card]: The card if found, None otherwise
    """
    with get_db() as db:
        try:
            # Assuming QR data contains card ID in some format
            # This is a simplified example - adjust according to your QR format
            card_id = int(qr_data)
            return db.query(Card).filter(
                Card.id == card_id,
                Card.status == 'approved'
            ).first()
        except (ValueError, TypeError):
            return None


def case(conditions, else_=None):
    """
    Helper function for SQL CASE expressions.
    
    Args:
        conditions: List of (condition, value) tuples
        else_: Default value if no conditions match
        
    Returns:
        SQL CASE expression
    """
    return func.coalesce(func.case(conditions, else_=else_), 0)
