"""
Admin Panel API routes for WebApp
Handles admin panel operations like user management, moderation, analytics
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from core.database import get_db
from core.models import User, Card, Transaction
from core.security.jwt_service import verify_admin_token
from core.logger import get_logger

router = APIRouter(prefix="/api/admin", tags=["admin-panel"])
logger = get_logger(__name__)

# Pydantic models
class DashboardStats(BaseModel):
    total_users: int
    active_partners: int
    pending_moderation: int
    today_transactions: int

class UserResponse(BaseModel):
    id: int
    full_name: Optional[str] = None
    email: Optional[str] = None
    role: str
    is_active: bool
    created_at: datetime

# Dependency to get current admin
async def get_current_admin(authorization: Optional[str] = None) -> Dict[str, Any]:
    """Get current admin from JWT token"""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing authentication token")
    
    token = authorization.split(" ", 1)[1]
    claims = verify_admin_token(token)
    if not claims:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    role = claims.get("role", "").lower()
    if role not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    return claims

@router.get("/dashboard", response_model=DashboardStats)
async def get_admin_dashboard(
    admin_claims: Dict[str, Any] = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get admin dashboard statistics"""
    try:
        total_users = db.query(User).count()
        active_partners = db.query(User).filter(User.role == "partner", User.is_active == True).count()
        pending_moderation = db.query(Card).filter(Card.status == "pending").count()
        
        today = datetime.utcnow().date()
        today_transactions = db.query(Transaction).filter(func.date(Transaction.created_at) == today).count()
        
        return DashboardStats(
            total_users=total_users,
            active_partners=active_partners,
            pending_moderation=pending_moderation,
            today_transactions=today_transactions
        )
        
    except Exception as e:
        logger.error(f"Error getting admin dashboard: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/users", response_model=Dict[str, Any])
async def get_admin_users(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    admin_claims: Dict[str, Any] = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get users with pagination"""
    try:
        query = db.query(User)
        total = query.count()
        total_pages = (total + limit - 1) // limit
        
        users = query.order_by(desc(User.created_at)).offset((page - 1) * limit).limit(limit).all()
        
        user_responses = [
            UserResponse(
                id=user.id,
                full_name=user.full_name,
                email=user.email,
                role=user.role,
                is_active=user.is_active,
                created_at=user.created_at
            )
            for user in users
        ]
        
        return {
            "users": user_responses,
            "total": total,
            "total_pages": total_pages,
            "current_page": page,
            "has_next": page < total_pages,
            "has_previous": page > 1
        }
        
    except Exception as e:
        logger.error(f"Error getting admin users: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
