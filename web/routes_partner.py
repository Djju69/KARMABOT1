"""
Partner API routes for WebApp
Handles partner-specific operations like card management, statistics, and QR codes
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, Path, Query, UploadFile, File, Form
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, case

from core.database import get_db
from core.models import User, Card, QRScan, Transaction, QRCode
from core.services.partner_service import (
    count_approved_partner_cards,
    get_partner_cards_with_filter,
    get_partner_statistics,
    register_scan
)
from core.services.qr_code_service import qr_code_service
from core.security.jwt_service import verify_partner_token
from core.logger import get_logger

router = APIRouter(prefix="/api/partner", tags=["partner"])
logger = get_logger(__name__)

# Pydantic models
class PartnerStats(BaseModel):
    total_cards: int
    active_cards: int
    total_views: int
    total_scans: int
    recent_scans: int
    conversion_rate: float
    popular_cards: List[Dict[str, Any]]

class CardResponse(BaseModel):
    id: int
    category_id: int
    subcategory_id: Optional[int] = None
    city_id: Optional[int] = None
    area_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    contact: Optional[str] = None
    address: Optional[str] = None
    google_maps_url: Optional[str] = None
    discount_text: Optional[str] = None
    status: str
    priority_level: int = 0
    views: int = 0
    scans: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class CardCreate(BaseModel):
    category_id: int
    subcategory_id: Optional[int] = Field(default=None)
    city_id: Optional[int] = Field(default=None)
    area_id: Optional[int] = Field(default=None)
    title: str = Field(min_length=2, max_length=120)
    description: Optional[str] = Field(default=None, max_length=2000)
    contact: Optional[str] = Field(default=None, max_length=200)
    address: Optional[str] = Field(default=None, max_length=300)
    google_maps_url: Optional[str] = Field(default=None, max_length=500)
    discount_text: Optional[str] = Field(default=None, max_length=200)

class CardUpdate(BaseModel):
    category_id: Optional[int] = None
    subcategory_id: Optional[int] = Field(default=None)
    city_id: Optional[int] = Field(default=None)
    area_id: Optional[int] = Field(default=None)
    title: Optional[str] = Field(default=None, min_length=2, max_length=120)
    description: Optional[str] = Field(default=None, max_length=2000)
    contact: Optional[str] = Field(default=None, max_length=200)
    address: Optional[str] = Field(default=None, max_length=300)
    google_maps_url: Optional[str] = Field(default=None, max_length=500)
    discount_text: Optional[str] = Field(default=None, max_length=200)

class CardsResponse(BaseModel):
    items: List[CardResponse]
    total: int
    total_pages: int
    current_page: int
    has_next: bool
    has_previous: bool

class QRCodeResponse(BaseModel):
    id: int
    code: str
    value: int
    expires_at: Optional[datetime] = None
    is_active: bool
    redeemed_by: Optional[int] = None
    redeemed_at: Optional[datetime] = None
    qr_code_url: Optional[str] = None
    created_at: datetime

class QRCodeCreate(BaseModel):
    card_id: int
    value: int = Field(ge=1, le=10000)
    expires_days: int = Field(default=30, ge=1, le=365)

class PartnerSettings(BaseModel):
    display_name: Optional[str] = Field(default=None, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=50)
    email: Optional[str] = Field(default=None, max_length=255)

# Dependency to get current partner
async def get_current_partner(
    authorization: Optional[str] = None,
    x_auth_token: Optional[str] = None
) -> Dict[str, Any]:
    """Get current partner from JWT token"""
    token = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]
    elif x_auth_token:
        token = x_auth_token
    
    if not token:
        raise HTTPException(status_code=401, detail="Missing authentication token")
    
    claims = verify_partner_token(token)
    if not claims:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return claims

@router.get("/statistics", response_model=PartnerStats)
async def get_partner_statistics_api(
    partner_claims: Dict[str, Any] = Depends(get_current_partner),
    db: Session = Depends(get_db)
):
    """Get partner statistics"""
    try:
        partner_id = int(partner_claims.get("sub"))
        
        # Get basic statistics
        stats = await get_partner_statistics(partner_id)
        
        # Get popular cards
        popular_cards = db.query(
            Card.title,
            Card.views,
            Card.scans
        ).filter(
            Card.partner_id == partner_id,
            Card.status == 'approved'
        ).order_by(Card.views.desc()).limit(5).all()
        
        stats["popular_cards"] = [
            {
                "title": card.title,
                "views": card.views or 0,
                "scans": card.scans or 0
            }
            for card in popular_cards
        ]
        
        return PartnerStats(**stats)
        
    except Exception as e:
        logger.error(f"Error getting partner statistics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/cards", response_model=CardsResponse)
async def get_partner_cards_api(
    status: Optional[str] = Query(default=None),
    category_id: Optional[int] = Query(default=None),
    q: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
    partner_claims: Dict[str, Any] = Depends(get_current_partner),
    db: Session = Depends(get_db)
):
    """Get partner's cards with filtering and pagination"""
    try:
        partner_id = int(partner_claims.get("sub"))
        
        # Build query
        query = db.query(Card).filter(Card.partner_id == partner_id)
        
        if status:
            query = query.filter(Card.status == status)
        
        if category_id:
            query = query.filter(Card.category_id == category_id)
        
        if q:
            query = query.filter(Card.title.ilike(f"%{q}%"))
        
        # Count total
        total = query.count()
        total_pages = (total + limit - 1) // limit
        
        # Apply pagination
        cards = (
            query.order_by(Card.created_at.desc())
            .offset((page - 1) * limit)
            .limit(limit)
            .all()
        )
        
        # Convert to response format
        card_responses = [
            CardResponse(
                id=card.id,
                category_id=card.category_id,
                subcategory_id=getattr(card, 'subcategory_id', None),
                city_id=getattr(card, 'city_id', None),
                area_id=getattr(card, 'area_id', None),
                title=card.title,
                description=card.description,
                contact=card.contact,
                address=card.address,
                google_maps_url=card.google_maps_url,
                discount_text=card.discount_text,
                status=card.status,
                priority_level=card.priority_level,
                views=card.views or 0,
                scans=card.scans or 0,
                created_at=card.created_at,
                updated_at=card.updated_at
            )
            for card in cards
        ]
        
        return CardsResponse(
            items=card_responses,
            total=total,
            total_pages=total_pages,
            current_page=page,
            has_next=page < total_pages,
            has_previous=page > 1
        )
        
    except Exception as e:
        logger.error(f"Error getting partner cards: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/cards", response_model=CardResponse)
async def create_partner_card_api(
    card_data: CardCreate,
    partner_claims: Dict[str, Any] = Depends(get_current_partner),
    db: Session = Depends(get_db)
):
    """Create a new card for partner"""
    try:
        partner_id = int(partner_claims.get("sub"))
        
        # Create new card
        new_card = Card(
            partner_id=partner_id,
            category_id=card_data.category_id,
            subcategory_id=card_data.subcategory_id,
            city_id=card_data.city_id,
            area_id=card_data.area_id,
            title=card_data.title,
            description=card_data.description,
            contact=card_data.contact,
            address=card_data.address,
            google_maps_url=card_data.google_maps_url,
            discount_text=card_data.discount_text,
            status='pending',
            priority_level=0,
            views=0,
            scans=0,
            created_at=datetime.utcnow()
        )
        
        db.add(new_card)
        db.commit()
        db.refresh(new_card)
        
        return CardResponse(
            id=new_card.id,
            category_id=new_card.category_id,
            subcategory_id=new_card.subcategory_id,
            city_id=new_card.city_id,
            area_id=new_card.area_id,
            title=new_card.title,
            description=new_card.description,
            contact=new_card.contact,
            address=new_card.address,
            google_maps_url=new_card.google_maps_url,
            discount_text=new_card.discount_text,
            status=new_card.status,
            priority_level=new_card.priority_level,
            views=new_card.views or 0,
            scans=new_card.scans or 0,
            created_at=new_card.created_at,
            updated_at=new_card.updated_at
        )
        
    except Exception as e:
        logger.error(f"Error creating partner card: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")

@router.patch("/cards/{card_id}", response_model=CardResponse)
async def update_partner_card_api(
    card_id: int,
    card_data: CardUpdate,
    partner_claims: Dict[str, Any] = Depends(get_current_partner),
    db: Session = Depends(get_db)
):
    """Update partner's card"""
    try:
        partner_id = int(partner_claims.get("sub"))
        
        # Find card and verify ownership
        card = db.query(Card).filter(
            Card.id == card_id,
            Card.partner_id == partner_id
        ).first()
        
        if not card:
            raise HTTPException(status_code=404, detail="Card not found")
        
        # Update fields
        update_data = card_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(card, field, value)
        
        card.updated_at = datetime.utcnow()
        
        # If category changed, set status to pending for moderation
        if 'category_id' in update_data:
            card.status = 'pending'
        
        db.commit()
        db.refresh(card)
        
        return CardResponse(
            id=card.id,
            category_id=card.category_id,
            subcategory_id=card.subcategory_id,
            city_id=card.city_id,
            area_id=card.area_id,
            title=card.title,
            description=card.description,
            contact=card.contact,
            address=card.address,
            google_maps_url=card.google_maps_url,
            discount_text=card.discount_text,
            status=card.status,
            priority_level=card.priority_level,
            views=card.views or 0,
            scans=card.scans or 0,
            created_at=card.created_at,
            updated_at=card.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating partner card: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/cards/{card_id}/hide", response_model=CardResponse)
async def hide_partner_card_api(
    card_id: int,
    partner_claims: Dict[str, Any] = Depends(get_current_partner),
    db: Session = Depends(get_db)
):
    """Hide partner's card"""
    try:
        partner_id = int(partner_claims.get("sub"))
        
        # Find card and verify ownership
        card = db.query(Card).filter(
            Card.id == card_id,
            Card.partner_id == partner_id
        ).first()
        
        if not card:
            raise HTTPException(status_code=404, detail="Card not found")
        
        # Hide card
        card.status = 'archived'
        card.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(card)
        
        return CardResponse(
            id=card.id,
            category_id=card.category_id,
            subcategory_id=card.subcategory_id,
            city_id=card.city_id,
            area_id=card.area_id,
            title=card.title,
            description=card.description,
            contact=card.contact,
            address=card.address,
            google_maps_url=card.google_maps_url,
            discount_text=card.discount_text,
            status=card.status,
            priority_level=card.priority_level,
            views=card.views or 0,
            scans=card.scans or 0,
            created_at=card.created_at,
            updated_at=card.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error hiding partner card: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/cards/{card_id}/unhide", response_model=CardResponse)
async def unhide_partner_card_api(
    card_id: int,
    partner_claims: Dict[str, Any] = Depends(get_current_partner),
    db: Session = Depends(get_db)
):
    """Unhide partner's card"""
    try:
        partner_id = int(partner_claims.get("sub"))
        
        # Find card and verify ownership
        card = db.query(Card).filter(
            Card.id == card_id,
            Card.partner_id == partner_id
        ).first()
        
        if not card:
            raise HTTPException(status_code=404, detail="Card not found")
        
        # Unhide card
        card.status = 'approved'
        card.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(card)
        
        return CardResponse(
            id=card.id,
            category_id=card.category_id,
            subcategory_id=card.subcategory_id,
            city_id=card.city_id,
            area_id=card.area_id,
            title=card.title,
            description=card.description,
            contact=card.contact,
            address=card.address,
            google_maps_url=card.google_maps_url,
            discount_text=card.discount_text,
            status=card.status,
            priority_level=card.priority_level,
            views=card.views or 0,
            scans=card.scans or 0,
            created_at=card.created_at,
            updated_at=card.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unhiding partner card: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/qr-codes", response_model=List[QRCodeResponse])
async def get_partner_qr_codes_api(
    partner_claims: Dict[str, Any] = Depends(get_current_partner),
    db: Session = Depends(get_db)
):
    """Get partner's QR codes"""
    try:
        partner_id = int(partner_claims.get("sub"))
        
        # Get QR codes for partner's cards
        qr_codes = db.query(QRCode).join(Card).filter(
            Card.partner_id == partner_id
        ).order_by(QRCode.created_at.desc()).all()
        
        return [
            QRCodeResponse(
                id=qr.id,
                code=qr.code,
                value=qr.value,
                expires_at=qr.expires_at,
                is_active=qr.is_active,
                redeemed_by=qr.redeemed_by,
                redeemed_at=qr.redeemed_at,
                qr_code_url=f"/api/qr-codes/{qr.id}/image",
                created_at=qr.created_at
            )
            for qr in qr_codes
        ]
        
    except Exception as e:
        logger.error(f"Error getting partner QR codes: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/qr-codes", response_model=QRCodeResponse)
async def create_partner_qr_code_api(
    qr_data: QRCodeCreate,
    partner_claims: Dict[str, Any] = Depends(get_current_partner),
    db: Session = Depends(get_db)
):
    """Create QR code for partner's card"""
    try:
        partner_id = int(partner_claims.get("sub"))
        
        # Verify card ownership
        card = db.query(Card).filter(
            Card.id == qr_data.card_id,
            Card.partner_id == partner_id
        ).first()
        
        if not card:
            raise HTTPException(status_code=404, detail="Card not found")
        
        # Create QR code
        qr_code = await qr_code_service.create_qr_code(
            user_id=partner_id,
            card_id=qr_data.card_id,
            value=qr_data.value,
            expires_days=qr_data.expires_days
        )
        
        return QRCodeResponse(
            id=qr_code.id,
            code=qr_code.code,
            value=qr_code.value,
            expires_at=qr_code.expires_at,
            is_active=qr_code.is_active,
            redeemed_by=qr_code.redeemed_by,
            redeemed_at=qr_code.redeemed_at,
            qr_code_url=f"/api/qr-codes/{qr_code.id}/image",
            created_at=qr_code.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating partner QR code: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/settings", response_model=Dict[str, str])
async def update_partner_settings_api(
    settings_data: PartnerSettings,
    partner_claims: Dict[str, Any] = Depends(get_current_partner),
    db: Session = Depends(get_db)
):
    """Update partner settings"""
    try:
        partner_id = int(partner_claims.get("sub"))
        
        # Find or create partner record
        partner = db.query(User).filter(User.telegram_id == partner_id).first()
        
        if not partner:
            raise HTTPException(status_code=404, detail="Partner not found")
        
        # Update settings
        update_data = settings_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(partner, field, value)
        
        partner.updated_at = datetime.utcnow()
        
        db.commit()
        
        return {"message": "Settings updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating partner settings: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/cards/{card_id}/images")
async def upload_card_images_api(
    card_id: int,
    files: List[UploadFile] = File(...),
    partner_claims: Dict[str, Any] = Depends(get_current_partner),
    db: Session = Depends(get_db)
):
    """Upload images for partner's card"""
    try:
        partner_id = int(partner_claims.get("sub"))
        
        # Verify card ownership
        card = db.query(Card).filter(
            Card.id == card_id,
            Card.partner_id == partner_id
        ).first()
        
        if not card:
            raise HTTPException(status_code=404, detail="Card not found")
        
        # TODO: Implement image upload logic
        # This would involve saving files to disk/storage and updating database
        
        return {"message": "Images uploaded successfully", "count": len(files)}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading card images: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/cards/{card_id}/images")
async def get_card_images_api(
    card_id: int,
    partner_claims: Dict[str, Any] = Depends(get_current_partner),
    db: Session = Depends(get_db)
):
    """Get images for partner's card"""
    try:
        partner_id = int(partner_claims.get("sub"))
        
        # Verify card ownership
        card = db.query(Card).filter(
            Card.id == card_id,
            Card.partner_id == partner_id
        ).first()
        
        if not card:
            raise HTTPException(status_code=404, detail="Card not found")
        
        # TODO: Implement image retrieval logic
        # This would return list of image URLs
        
        return {"images": []}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting card images: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
