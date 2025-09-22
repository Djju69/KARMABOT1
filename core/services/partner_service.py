"""
Partner service module for handling partner-related operations.
Including card management, statistics, and QR code operations.
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_, case
from core.database import get_db
from core.models import User, Card, QRScan, Transaction, QRCode
from core.logger import get_logger

logger = get_logger(__name__)


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


class PartnerService:
    """Enhanced partner service with comprehensive functionality"""
    
    def __init__(self):
        self.db = get_db()
    
    async def get_partner_profile(self, partner_id: int) -> Dict[str, Any]:
        """Get comprehensive partner profile"""
        try:
            with self.db() as db:
                # Get partner user
                partner = db.query(User).filter(User.telegram_id == partner_id).first()
                if not partner:
                    return {}
                
                # Get card statistics
                card_stats = db.query(
                    func.count(Card.id).label("total_cards"),
                    func.sum(case([(Card.status == 'approved', 1)], else_=0)).label("active_cards"),
                    func.sum(Card.views).label("total_views"),
                    func.sum(Card.scans).label("total_scans")
                ).filter(Card.partner_id == partner_id).first()
                
                # Get recent activity (last 30 days)
                thirty_days_ago = datetime.utcnow() - timedelta(days=30)
                recent_scans = db.query(QRScan).filter(
                    QRScan.card_id.in_(
                        db.query(Card.id).filter(Card.partner_id == partner_id)
                    ),
                    QRScan.scan_time >= thirty_days_ago
                ).count()
                
                # Get QR codes count
                qr_count = db.query(QRCode).join(Card).filter(
                    Card.partner_id == partner_id
                ).count()
                
                return {
                    "partner_id": partner_id,
                    "display_name": partner.display_name or partner.full_name,
                    "phone": partner.phone,
                    "email": partner.email,
                    "is_verified": partner.is_verified,
                    "total_cards": card_stats.total_cards or 0,
                    "active_cards": card_stats.active_cards or 0,
                    "total_views": card_stats.total_views or 0,
                    "total_scans": card_stats.total_scans or 0,
                    "recent_scans": recent_scans,
                    "qr_codes_count": qr_count,
                    "conversion_rate": self._calculate_conversion_rate(
                        card_stats.total_views, card_stats.total_scans
                    ),
                    "created_at": partner.created_at,
                    "updated_at": partner.updated_at
                }
        except Exception as e:
            logger.error(f"Error getting partner profile: {e}")
            return {}
    
    async def get_partner_cards_detailed(
        self, 
        partner_id: int, 
        status: Optional[str] = None,
        category_id: Optional[int] = None,
        search: Optional[str] = None,
        page: int = 1,
        per_page: int = 10
    ) -> Dict[str, Any]:
        """Get detailed partner cards with filtering and pagination"""
        try:
            with self.db() as db:
                # Build query
                query = db.query(Card).filter(Card.partner_id == partner_id)
                
                if status:
                    query = query.filter(Card.status == status)
                
                if category_id:
                    query = query.filter(Card.category_id == category_id)
                
                if search:
                    query = query.filter(Card.title.ilike(f"%{search}%"))
                
                # Count total
                total = query.count()
                total_pages = (total + per_page - 1) // per_page
                
                # Apply pagination
                cards = (
                    query.order_by(Card.created_at.desc())
                    .offset((page - 1) * per_page)
                    .limit(per_page)
                    .all()
                )
                
                # Format cards
                formatted_cards = []
                for card in cards:
                    formatted_cards.append({
                        "id": card.id,
                        "category_id": card.category_id,
                        "subcategory_id": getattr(card, 'subcategory_id', None),
                        "city_id": getattr(card, 'city_id', None),
                        "area_id": getattr(card, 'area_id', None),
                        "title": card.title,
                        "description": card.description,
                        "contact": card.contact,
                        "address": card.address,
                        "google_maps_url": card.google_maps_url,
                        "discount_text": card.discount_text,
                        "status": card.status,
                        "priority_level": card.priority_level,
                        "views": card.views or 0,
                        "scans": card.scans or 0,
                        "created_at": card.created_at,
                        "updated_at": card.updated_at
                    })
                
                return {
                    "cards": formatted_cards,
                    "total": total,
                    "total_pages": total_pages,
                    "current_page": page,
                    "has_next": page < total_pages,
                    "has_previous": page > 1
                }
        except Exception as e:
            logger.error(f"Error getting partner cards detailed: {e}")
            return {"cards": [], "total": 0, "total_pages": 0, "current_page": 1, "has_next": False, "has_previous": False}
    
    async def get_partner_qr_codes(self, partner_id: int) -> List[Dict[str, Any]]:
        """Get partner's QR codes"""
        try:
            with self.db() as db:
                qr_codes = db.query(QRCode).join(Card).filter(
                    Card.partner_id == partner_id
                ).order_by(QRCode.created_at.desc()).all()
                
                return [
                    {
                        "id": qr.id,
                        "code": qr.code,
                        "value": qr.value,
                        "expires_at": qr.expires_at,
                        "is_active": qr.is_active,
                        "redeemed_by": qr.redeemed_by,
                        "redeemed_at": qr.redeemed_at,
                        "created_at": qr.created_at,
                        "card_title": qr.card.title if hasattr(qr, 'card') else None
                    }
                    for qr in qr_codes
                ]
        except Exception as e:
            logger.error(f"Error getting partner QR codes: {e}")
            return []
    
    async def get_partner_analytics(self, partner_id: int, days: int = 30) -> Dict[str, Any]:
        """Get detailed analytics for partner"""
        try:
            with self.db() as db:
                start_date = datetime.utcnow() - timedelta(days=days)
                
                # Daily activity
                daily_stats = db.query(
                    func.date(QRScan.scan_time).label("date"),
                    func.count(QRScan.id).label("scans")
                ).join(Card).filter(
                    Card.partner_id == partner_id,
                    QRScan.scan_time >= start_date
                ).group_by(func.date(QRScan.scan_time)).all()
                
                # Top performing cards
                top_cards = db.query(
                    Card.title,
                    Card.views,
                    Card.scans,
                    Card.id
                ).filter(
                    Card.partner_id == partner_id,
                    Card.status == 'approved'
                ).order_by(Card.scans.desc()).limit(10).all()
                
                # Category performance
                category_stats = db.query(
                    Card.category_id,
                    func.count(Card.id).label("cards_count"),
                    func.sum(Card.views).label("total_views"),
                    func.sum(Card.scans).label("total_scans")
                ).filter(
                    Card.partner_id == partner_id
                ).group_by(Card.category_id).all()
                
                return {
                    "daily_activity": [
                        {"date": str(stat.date), "scans": stat.scans}
                        for stat in daily_stats
                    ],
                    "top_cards": [
                        {
                            "id": card.id,
                            "title": card.title,
                            "views": card.views or 0,
                            "scans": card.scans or 0
                        }
                        for card in top_cards
                    ],
                    "category_performance": [
                        {
                            "category_id": stat.category_id,
                            "cards_count": stat.cards_count,
                            "total_views": stat.total_views or 0,
                            "total_scans": stat.total_scans or 0
                        }
                        for stat in category_stats
                    ]
                }
        except Exception as e:
            logger.error(f"Error getting partner analytics: {e}")
            return {"daily_activity": [], "top_cards": [], "category_performance": []}
    
    async def update_partner_settings(
        self, 
        partner_id: int, 
        settings_data: Dict[str, Any]
    ) -> bool:
        """Update partner settings"""
        try:
            with self.db() as db:
                partner = db.query(User).filter(User.telegram_id == partner_id).first()
                if not partner:
                    return False
                
                # Update allowed fields
                allowed_fields = ['display_name', 'phone', 'email']
                for field, value in settings_data.items():
                    if field in allowed_fields and value is not None:
                        setattr(partner, field, value)
                
                partner.updated_at = datetime.utcnow()
                db.commit()
                return True
        except Exception as e:
            logger.error(f"Error updating partner settings: {e}")
            return False
    
    def _calculate_conversion_rate(self, views: int, scans: int) -> float:
        """Calculate conversion rate from views to scans"""
        if not views or views == 0:
            return 0.0
        return round((scans / views) * 100, 2)


# Create service instance
partner_service = PartnerService()
