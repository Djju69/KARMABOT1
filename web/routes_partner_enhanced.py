"""
Enhanced Partner API routes
Comprehensive partner functionality with dashboard, analytics, and management
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, Query, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_

from core.database import get_db
from core.models import Partner, Card, Transaction, User
from core.security.jwt_service import verify_user_token
from core.logger import get_logger
from core.services.partner_verification import PartnerVerificationService

router = APIRouter(prefix="/api/partner", tags=["partner-enhanced"])
logger = get_logger(__name__)

# Pydantic models
class PartnerDashboardStats(BaseModel):
    total_cards: int
    approved_cards: int
    pending_cards: int
    rejected_cards: int
    total_views: int
    total_scans: int
    revenue: float
    verification_status: str
    verification_score: int
    risk_level: str

class CardResponse(BaseModel):
    id: int
    title: str
    description: str
    category: str
    status: str
    views: int
    scans: int
    created_at: datetime
    updated_at: Optional[datetime] = None

class ActivityResponse(BaseModel):
    id: int
    type: str
    title: str
    description: Optional[str] = None
    created_at: datetime
    metadata: Optional[Dict[str, Any]] = None

class AnalyticsData(BaseModel):
    period: str
    views_data: List[Dict[str, Any]]
    scans_data: List[Dict[str, Any]]
    revenue_data: List[Dict[str, Any]]
    top_cards: List[Dict[str, Any]]

# Dependency to get current partner
async def get_current_partner(authorization: Optional[str] = None) -> Dict[str, Any]:
    """Get current partner from JWT token"""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing authentication token")
    
    token = authorization.split(" ", 1)[1]
    claims = verify_user_token(token)
    if not claims:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_id = claims.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid user ID")
    
    return claims

@router.get("/dashboard", response_model=PartnerDashboardStats)
async def get_partner_dashboard(
    partner_claims: Dict[str, Any] = Depends(get_current_partner),
    db: Session = Depends(get_db)
):
    """Get partner dashboard statistics"""
    try:
        user_id = partner_claims["user_id"]
        
        # Get partner info
        partner = db.query(Partner).filter(Partner.user_id == user_id).first()
        if not partner:
            raise HTTPException(status_code=404, detail="Partner not found")
        
        # Get card statistics
        total_cards = db.query(Card).filter(Card.partner_id == partner.id).count()
        approved_cards = db.query(Card).filter(
            Card.partner_id == partner.id,
            Card.status == "approved"
        ).count()
        pending_cards = db.query(Card).filter(
            Card.partner_id == partner.id,
            Card.status == "pending"
        ).count()
        rejected_cards = db.query(Card).filter(
            Card.partner_id == partner.id,
            Card.status == "rejected"
        ).count()
        
        # Get views and scans (mock data for now)
        total_views = db.query(func.sum(Card.views)).filter(Card.partner_id == partner.id).scalar() or 0
        total_scans = db.query(func.sum(Card.scans)).filter(Card.partner_id == partner.id).scalar() or 0
        
        # Get revenue
        revenue = db.query(func.sum(Transaction.amount)).filter(
            Transaction.partner_id == partner.id
        ).scalar() or 0.0
        
        # Get verification details
        verification_details = await PartnerVerificationService.get_verification_details(partner.id)
        verification_status = verification_details.get("verification_status", "pending") if verification_details else "pending"
        verification_score = verification_details.get("verification_score", 0) if verification_details else 0
        risk_level = verification_details.get("risk_level", "high") if verification_details else "high"
        
        return PartnerDashboardStats(
            total_cards=total_cards,
            approved_cards=approved_cards,
            pending_cards=pending_cards,
            rejected_cards=rejected_cards,
            total_views=total_views,
            total_scans=total_scans,
            revenue=revenue,
            verification_status=verification_status,
            verification_score=verification_score,
            risk_level=risk_level
        )
        
    except Exception as e:
        logger.error(f"Error getting partner dashboard: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/cards", response_model=List[CardResponse])
async def get_partner_cards(
    status: Optional[str] = Query(default=None),
    partner_claims: Dict[str, Any] = Depends(get_current_partner),
    db: Session = Depends(get_db)
):
    """Get partner cards"""
    try:
        user_id = partner_claims["user_id"]
        
        # Get partner info
        partner = db.query(Partner).filter(Partner.user_id == user_id).first()
        if not partner:
            raise HTTPException(status_code=404, detail="Partner not found")
        
        # Build query
        query = db.query(Card).filter(Card.partner_id == partner.id)
        
        if status:
            query = query.filter(Card.status == status)
        
        cards = query.order_by(desc(Card.created_at)).all()
        
        return [
            CardResponse(
                id=card.id,
                title=card.title,
                description=card.description,
                category=card.category,
                status=card.status,
                views=getattr(card, 'views', 0),
                scans=getattr(card, 'scans', 0),
                created_at=card.created_at,
                updated_at=getattr(card, 'updated_at', None)
            )
            for card in cards
        ]
        
    except Exception as e:
        logger.error(f"Error getting partner cards: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/activity", response_model=List[ActivityResponse])
async def get_partner_activity(
    limit: int = Query(default=20, ge=1, le=100),
    partner_claims: Dict[str, Any] = Depends(get_current_partner),
    db: Session = Depends(get_db)
):
    """Get partner recent activity"""
    try:
        user_id = partner_claims["user_id"]
        
        # Get partner info
        partner = db.query(Partner).filter(Partner.user_id == user_id).first()
        if not partner:
            raise HTTPException(status_code=404, detail="Partner not found")
        
        activities = []
        
        # Recent card creations
        recent_cards = db.query(Card).filter(
            Card.partner_id == partner.id
        ).order_by(desc(Card.created_at)).limit(5).all()
        
        for card in recent_cards:
            activities.append(ActivityResponse(
                id=card.id,
                type="card",
                title=f"Создана карточка: {card.title}",
                description=f"Статус: {card.status}",
                created_at=card.created_at,
                metadata={"card_id": card.id, "status": card.status}
            ))
        
        # Recent transactions
        recent_transactions = db.query(Transaction).filter(
            Transaction.partner_id == partner.id
        ).order_by(desc(Transaction.created_at)).limit(5).all()
        
        for transaction in recent_transactions:
            activities.append(ActivityResponse(
                id=transaction.id,
                type="transaction",
                title=f"Новая транзакция: {transaction.amount} ₽",
                description=f"Тип: {transaction.transaction_type}",
                created_at=transaction.created_at,
                metadata={"amount": transaction.amount, "type": transaction.transaction_type}
            ))
        
        # Sort by creation time and limit
        activities.sort(key=lambda x: x.created_at, reverse=True)
        return activities[:limit]
        
    except Exception as e:
        logger.error(f"Error getting partner activity: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/analytics", response_model=AnalyticsData)
async def get_partner_analytics(
    period: str = Query(default="7d", regex="^(1d|7d|30d|90d)$"),
    partner_claims: Dict[str, Any] = Depends(get_current_partner),
    db: Session = Depends(get_db)
):
    """Get partner analytics data"""
    try:
        user_id = partner_claims["user_id"]
        
        # Get partner info
        partner = db.query(Partner).filter(Partner.user_id == user_id).first()
        if not partner:
            raise HTTPException(status_code=404, detail="Partner not found")
        
        # Calculate date range
        now = datetime.utcnow()
        if period == "1d":
            start_date = now - timedelta(days=1)
        elif period == "7d":
            start_date = now - timedelta(days=7)
        elif period == "30d":
            start_date = now - timedelta(days=30)
        else:  # 90d
            start_date = now - timedelta(days=90)
        
        # Views data
        views_data = []
        for i in range(7):  # Last 7 days
            date = start_date + timedelta(days=i)
            views = db.query(func.sum(Card.views)).filter(
                Card.partner_id == partner.id,
                func.date(Card.created_at) == date.date()
            ).scalar() or 0
            views_data.append({
                "date": date.strftime("%Y-%m-%d"),
                "views": views
            })
        
        # Scans data
        scans_data = []
        for i in range(7):
            date = start_date + timedelta(days=i)
            scans = db.query(func.sum(Card.scans)).filter(
                Card.partner_id == partner.id,
                func.date(Card.created_at) == date.date()
            ).scalar() or 0
            scans_data.append({
                "date": date.strftime("%Y-%m-%d"),
                "scans": scans
            })
        
        # Revenue data
        revenue_data = []
        for i in range(7):
            date = start_date + timedelta(days=i)
            revenue = db.query(func.sum(Transaction.amount)).filter(
                Transaction.partner_id == partner.id,
                func.date(Transaction.created_at) == date.date()
            ).scalar() or 0
            revenue_data.append({
                "date": date.strftime("%Y-%m-%d"),
                "revenue": revenue
            })
        
        # Top cards
        top_cards = db.query(
            Card.title,
            Card.views,
            Card.scans,
            Card.status
        ).filter(Card.partner_id == partner.id).order_by(
            desc(Card.views)
        ).limit(5).all()
        
        top_cards_data = [
            {
                "title": card.title,
                "views": card.views or 0,
                "scans": card.scans or 0,
                "status": card.status
            }
            for card in top_cards
        ]
        
        return AnalyticsData(
            period=period,
            views_data=views_data,
            scans_data=scans_data,
            revenue_data=revenue_data,
            top_cards=top_cards_data
        )
        
    except Exception as e:
        logger.error(f"Error getting partner analytics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/cards/{card_id}/update-status")
async def update_card_status(
    card_id: int,
    status: str,
    partner_claims: Dict[str, Any] = Depends(get_current_partner),
    db: Session = Depends(get_db)
):
    """Update card status (for approved cards only)"""
    try:
        user_id = partner_claims["user_id"]
        
        # Get partner info
        partner = db.query(Partner).filter(Partner.user_id == user_id).first()
        if not partner:
            raise HTTPException(status_code=404, detail="Partner not found")
        
        # Get card
        card = db.query(Card).filter(
            Card.id == card_id,
            Card.partner_id == partner.id
        ).first()
        
        if not card:
            raise HTTPException(status_code=404, detail="Card not found")
        
        # Only allow status updates for approved cards
        if card.status != "approved":
            raise HTTPException(status_code=400, detail="Can only update status of approved cards")
        
        # Update status
        card.status = status
        card.updated_at = datetime.utcnow()
        db.commit()
        
        return {
            "success": True,
            "message": f"Card status updated to {status}",
            "card_id": card_id,
            "new_status": status
        }
        
    except Exception as e:
        logger.error(f"Error updating card status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/verification-status")
async def get_verification_status(
    partner_claims: Dict[str, Any] = Depends(get_current_partner),
    db: Session = Depends(get_db)
):
    """Get partner verification status"""
    try:
        user_id = partner_claims["user_id"]
        
        # Get partner info
        partner = db.query(Partner).filter(Partner.user_id == user_id).first()
        if not partner:
            raise HTTPException(status_code=404, detail="Partner not found")
        
        # Get verification details
        verification_details = await PartnerVerificationService.get_verification_details(partner.id)
        
        if not verification_details:
            return {
                "status": "not_found",
                "message": "Verification details not found"
            }
        
        return {
            "status": verification_details.get("verification_status", "pending"),
            "score": verification_details.get("verification_score", 0),
            "risk_level": verification_details.get("risk_level", "high"),
            "created_at": verification_details.get("created_at"),
            "verified_at": verification_details.get("verified_at"),
            "notes": verification_details.get("verification_notes", "")
        }
        
    except Exception as e:
        logger.error(f"Error getting verification status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/dashboard-enhanced")
async def partner_dashboard_enhanced(request: Request):
    """Serve enhanced partner dashboard"""
    try:
        with open("web/templates/partner-dashboard-enhanced.html", "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Partner dashboard not found")
    except Exception as e:
        logger.error(f"Error serving partner dashboard: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/request-verification")
async def request_verification(
    partner_claims: Dict[str, Any] = Depends(get_current_partner),
    db: Session = Depends(get_db)
):
    """Request partner verification"""
    try:
        user_id = partner_claims["user_id"]
        
        # Get partner info
        partner = db.query(Partner).filter(Partner.user_id == user_id).first()
        if not partner:
            raise HTTPException(status_code=404, detail="Partner not found")
        
        # Check if already verified
        if partner.verification_status == "approved":
            return {
                "success": False,
                "message": "Partner is already verified"
            }
        
        # Update verification status
        partner.verification_status = "pending"
        partner.verification_requested_at = datetime.utcnow()
        db.commit()
        
        return {
            "success": True,
            "message": "Verification request submitted",
            "status": "pending"
        }
        
    except Exception as e:
        logger.error(f"Error requesting verification: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/settings")
async def get_partner_settings(
    partner_claims: Dict[str, Any] = Depends(get_current_partner),
    db: Session = Depends(get_db)
):
    """Get partner settings"""
    try:
        user_id = partner_claims["user_id"]
        
        # Get partner info
        partner = db.query(Partner).filter(Partner.user_id == user_id).first()
        if not partner:
            raise HTTPException(status_code=404, detail="Partner not found")
        
        return {
            "business_name": partner.business_name,
            "business_type": partner.business_type,
            "description": partner.description,
            "contact_info": partner.contact_info,
            "location": partner.location,
            "verification_status": partner.verification_status,
            "created_at": partner.created_at,
            "updated_at": partner.updated_at
        }
        
    except Exception as e:
        logger.error(f"Error getting partner settings: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/settings")
async def update_partner_settings(
    settings_data: Dict[str, Any],
    partner_claims: Dict[str, Any] = Depends(get_current_partner),
    db: Session = Depends(get_db)
):
    """Update partner settings"""
    try:
        user_id = partner_claims["user_id"]
        
        # Get partner info
        partner = db.query(Partner).filter(Partner.user_id == user_id).first()
        if not partner:
            raise HTTPException(status_code=404, detail="Partner not found")
        
        # Update allowed fields
        allowed_fields = ["business_name", "description", "contact_info", "location"]
        
        for field in allowed_fields:
            if field in settings_data:
                setattr(partner, field, settings_data[field])
        
        partner.updated_at = datetime.utcnow()
        db.commit()
        
        return {
            "success": True,
            "message": "Settings updated successfully"
        }
        
    except Exception as e:
        logger.error(f"Error updating partner settings: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Partner registration endpoint
class PartnerRegistrationRequest(BaseModel):
    name: str = Field(..., description="Business name")
    phone: str = Field(..., description="Contact phone")
    email: str = Field(..., description="Contact email")
    description: str = Field(..., description="Business description")
    timestamp: Optional[str] = Field(None, description="Registration timestamp")

@router.post("/register")
async def register_partner(
    request: PartnerRegistrationRequest,
    db: Session = Depends(get_db)
):
    """Register a new partner application"""
    try:
        # Get user_id from request headers or query params
        # For now, we'll use a placeholder - in real implementation, 
        # this should come from authentication
        user_id = 1  # TODO: Get from authentication
        
        # Use raw SQL for PostgreSQL
        import psycopg2
        from core.settings import settings
        
        # Connect to PostgreSQL
        conn = psycopg2.connect(settings.database.url)
        cur = conn.cursor()
        try:
            # Check if application already exists
            cur.execute("""
                SELECT id FROM partner_applications WHERE telegram_user_id = %s
            """, (user_id,))
            
            existing_app = cur.fetchone()
            
            if existing_app:
                # Update existing application
                cur.execute("""
                    UPDATE partner_applications SET
                        name = %s, phone = %s, email = %s, business_description = %s,
                        status = 'pending', created_at = NOW()
                    WHERE telegram_user_id = %s
                """, (
                    request.name,
                    request.phone,
                    request.email,
                    request.description,
                    user_id
                ))
            else:
                # Insert new application
                cur.execute("""
                    INSERT INTO partner_applications (
                        telegram_user_id, telegram_username, name, phone, email, 
                        business_description, status, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, 'pending', NOW())
                """, (
                    user_id,
                    '',  # username
                    request.name,
                    request.phone,
                    request.email,
                    request.description
                ))
            
            conn.commit()
            
        finally:
            cur.close()
            conn.close()
        
        logger.info(f"Partner application registered for user {user_id}")
        
        return {
            "success": True,
            "message": "Partner application submitted successfully"
        }
        
    except Exception as e:
        logger.error(f"Error registering partner: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
