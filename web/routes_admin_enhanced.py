"""
Enhanced Admin Panel API routes
Comprehensive admin functionality with analytics, user management, system monitoring
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, Query, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_
import json

from core.database import get_db
from core.models import User, Card, Transaction, Partner, ModerationLog
from core.security.jwt_service import verify_admin_token
from core.logger import get_logger
from core.services.admins import AdminsService

router = APIRouter(prefix="/api/admin", tags=["admin-enhanced"])
logger = get_logger(__name__)

# Pydantic models
class DashboardStats(BaseModel):
    total_users: int
    active_partners: int
    pending_moderation: int
    today_transactions: int
    total_revenue: float
    system_uptime: str
    users_change: float
    partners_change: float
    transactions_change: float
    revenue_change: float

class UserResponse(BaseModel):
    id: int
    full_name: Optional[str] = None
    username: Optional[str] = None
    email: Optional[str] = None
    role: str
    is_active: bool
    created_at: datetime
    last_activity: Optional[datetime] = None
    total_transactions: int = 0
    total_spent: float = 0.0

class ActivityResponse(BaseModel):
    id: int
    type: str
    title: str
    description: Optional[str] = None
    user_id: Optional[int] = None
    created_at: datetime
    metadata: Optional[Dict[str, Any]] = None

class SystemHealth(BaseModel):
    status: str
    uptime: str
    memory_usage: float
    cpu_usage: float
    disk_usage: float
    database_status: str
    redis_status: str
    last_backup: Optional[datetime] = None

class AnalyticsData(BaseModel):
    period: str
    users_growth: List[Dict[str, Any]]
    transactions_trend: List[Dict[str, Any]]
    revenue_breakdown: Dict[str, float]
    top_partners: List[Dict[str, Any]]
    popular_categories: List[Dict[str, Any]]

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
async def get_enhanced_dashboard(
    admin_claims: Dict[str, Any] = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get comprehensive admin dashboard statistics"""
    try:
        # Basic stats
        total_users = db.query(User).count()
        active_partners = db.query(User).filter(
            User.role == "partner", 
            User.is_active == True
        ).count()
        pending_moderation = db.query(Card).filter(Card.status == "pending").count()
        
        # Today's transactions
        today = datetime.utcnow().date()
        today_transactions = db.query(Transaction).filter(
            func.date(Transaction.created_at) == today
        ).count()
        
        # Revenue calculation
        total_revenue = db.query(func.sum(Transaction.amount)).scalar() or 0.0
        
        # Calculate changes (mock data for now)
        users_change = 12.5  # Would calculate from historical data
        partners_change = 8.3
        transactions_change = 15.7
        revenue_change = 22.1
        
        return DashboardStats(
            total_users=total_users,
            active_partners=active_partners,
            pending_moderation=pending_moderation,
            today_transactions=today_transactions,
            total_revenue=total_revenue,
            system_uptime="99.9%",
            users_change=users_change,
            partners_change=partners_change,
            transactions_change=transactions_change,
            revenue_change=revenue_change
        )
        
    except Exception as e:
        logger.error(f"Error getting enhanced dashboard: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/users", response_model=Dict[str, Any])
async def get_admin_users(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    search: Optional[str] = Query(default=None),
    role: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    admin_claims: Dict[str, Any] = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get users with advanced filtering and pagination"""
    try:
        query = db.query(User)
        
        # Apply filters
        if search:
            query = query.filter(
                or_(
                    User.full_name.ilike(f"%{search}%"),
                    User.username.ilike(f"%{search}%"),
                    User.email.ilike(f"%{search}%")
                )
            )
        
        if role:
            query = query.filter(User.role == role)
        
        if status:
            if status == "active":
                query = query.filter(User.is_active == True)
            elif status == "inactive":
                query = query.filter(User.is_active == False)
        
        # Get total count
        total = query.count()
        total_pages = (total + limit - 1) // limit
        
        # Get paginated results
        users = query.order_by(desc(User.created_at)).offset(
            (page - 1) * limit
        ).limit(limit).all()
        
        # Calculate additional stats for each user
        user_responses = []
        for user in users:
            # Get user transaction stats
            user_transactions = db.query(Transaction).filter(
                Transaction.user_id == user.id
            ).all()
            
            total_transactions = len(user_transactions)
            total_spent = sum(t.amount for t in user_transactions)
            
            user_responses.append(UserResponse(
                id=user.id,
                full_name=user.full_name,
                username=user.username,
                email=user.email,
                role=user.role,
                is_active=user.is_active,
                created_at=user.created_at,
                last_activity=getattr(user, 'last_activity', None),
                total_transactions=total_transactions,
                total_spent=total_spent
            ))
        
        return {
            "users": user_responses,
            "total": total,
            "total_pages": total_pages,
            "current_page": page,
            "has_next": page < total_pages,
            "has_previous": page > 1,
            "filters": {
                "search": search,
                "role": role,
                "status": status
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting admin users: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/activity", response_model=List[ActivityResponse])
async def get_recent_activity(
    limit: int = Query(default=20, ge=1, le=100),
    admin_claims: Dict[str, Any] = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get recent system activity"""
    try:
        activities = []
        
        # Recent user registrations
        recent_users = db.query(User).order_by(desc(User.created_at)).limit(5).all()
        for user in recent_users:
            activities.append(ActivityResponse(
                id=user.id,
                type="user",
                title=f"Новый пользователь: {user.full_name or user.username or 'Аноним'}",
                description=f"Роль: {user.role}",
                user_id=user.id,
                created_at=user.created_at,
                metadata={"role": user.role}
            ))
        
        # Recent transactions
        recent_transactions = db.query(Transaction).order_by(
            desc(Transaction.created_at)
        ).limit(5).all()
        for transaction in recent_transactions:
            activities.append(ActivityResponse(
                id=transaction.id,
                type="transaction",
                title=f"Новая транзакция: {transaction.amount} ₽",
                description=f"Тип: {transaction.transaction_type}",
                user_id=transaction.user_id,
                created_at=transaction.created_at,
                metadata={"amount": transaction.amount, "type": transaction.transaction_type}
            ))
        
        # Recent moderation actions
        recent_moderation = db.query(ModerationLog).order_by(
            desc(ModerationLog.created_at)
        ).limit(5).all()
        for log in recent_moderation:
            activities.append(ActivityResponse(
                id=log.id,
                type="moderation",
                title=f"Модерация: {log.action}",
                description=log.comment or "Без комментария",
                user_id=log.moderator_id,
                created_at=log.created_at,
                metadata={"action": log.action, "card_id": log.card_id}
            ))
        
        # Sort by creation time and limit
        activities.sort(key=lambda x: x.created_at, reverse=True)
        return activities[:limit]
        
    except Exception as e:
        logger.error(f"Error getting recent activity: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/analytics", response_model=AnalyticsData)
async def get_analytics_data(
    period: str = Query(default="7d", regex="^(1d|7d|30d|90d|1y)$"),
    admin_claims: Dict[str, Any] = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get comprehensive analytics data"""
    try:
        # Calculate date range
        now = datetime.utcnow()
        if period == "1d":
            start_date = now - timedelta(days=1)
        elif period == "7d":
            start_date = now - timedelta(days=7)
        elif period == "30d":
            start_date = now - timedelta(days=30)
        elif period == "90d":
            start_date = now - timedelta(days=90)
        else:  # 1y
            start_date = now - timedelta(days=365)
        
        # Users growth
        users_growth = []
        for i in range(7):  # Last 7 days
            date = start_date + timedelta(days=i)
            count = db.query(User).filter(
                func.date(User.created_at) == date.date()
            ).count()
            users_growth.append({
                "date": date.strftime("%Y-%m-%d"),
                "count": count
            })
        
        # Transactions trend
        transactions_trend = []
        for i in range(7):
            date = start_date + timedelta(days=i)
            count = db.query(Transaction).filter(
                func.date(Transaction.created_at) == date.date()
            ).count()
            amount = db.query(func.sum(Transaction.amount)).filter(
                func.date(Transaction.created_at) == date.date()
            ).scalar() or 0
            transactions_trend.append({
                "date": date.strftime("%Y-%m-%d"),
                "count": count,
                "amount": amount
            })
        
        # Revenue breakdown (mock data)
        revenue_breakdown = {
            "partners": 60.0,
            "commission": 25.0,
            "advertising": 15.0
        }
        
        # Top partners
        top_partners = db.query(
            Partner.name,
            func.count(Transaction.id).label('transaction_count'),
            func.sum(Transaction.amount).label('total_amount')
        ).join(Transaction, Partner.id == Transaction.partner_id).filter(
            Transaction.created_at >= start_date
        ).group_by(Partner.id).order_by(
            desc('total_amount')
        ).limit(10).all()
        
        top_partners_data = [
            {
                "name": partner.name,
                "transactions": partner.transaction_count,
                "revenue": partner.total_amount
            }
            for partner in top_partners
        ]
        
        # Popular categories (mock data)
        popular_categories = [
            {"name": "Рестораны", "count": 45, "revenue": 125000},
            {"name": "Кафе", "count": 32, "revenue": 89000},
            {"name": "Магазины", "count": 28, "revenue": 67000},
            {"name": "Спорт", "count": 15, "revenue": 45000},
            {"name": "Красота", "count": 12, "revenue": 32000}
        ]
        
        return AnalyticsData(
            period=period,
            users_growth=users_growth,
            transactions_trend=transactions_trend,
            revenue_breakdown=revenue_breakdown,
            top_partners=top_partners_data,
            popular_categories=popular_categories
        )
        
    except Exception as e:
        logger.error(f"Error getting analytics data: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/health", response_model=SystemHealth)
async def get_system_health(
    admin_claims: Dict[str, Any] = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get system health status"""
    try:
        # Test database connection
        db.query(User).limit(1).first()
        database_status = "healthy"
        
        # Mock system metrics (in production, these would come from monitoring)
        memory_usage = 65.2
        cpu_usage = 23.8
        disk_usage = 45.7
        
        # Determine overall status
        if memory_usage > 90 or cpu_usage > 90 or disk_usage > 90:
            status = "warning"
        elif memory_usage > 95 or cpu_usage > 95 or disk_usage > 95:
            status = "critical"
        else:
            status = "healthy"
        
        return SystemHealth(
            status=status,
            uptime="99.9%",
            memory_usage=memory_usage,
            cpu_usage=cpu_usage,
            disk_usage=disk_usage,
            database_status=database_status,
            redis_status="healthy",  # Mock
            last_backup=datetime.utcnow() - timedelta(hours=6)
        )
        
    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        return SystemHealth(
            status="critical",
            uptime="0%",
            memory_usage=0,
            cpu_usage=0,
            disk_usage=0,
            database_status="error",
            redis_status="error"
        )

@router.post("/users/{user_id}/toggle-status")
async def toggle_user_status(
    user_id: int,
    admin_claims: Dict[str, Any] = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Toggle user active status"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user.is_active = not user.is_active
        db.commit()
        
        return {
            "success": True,
            "message": f"User status changed to {'active' if user.is_active else 'inactive'}",
            "user_id": user_id,
            "is_active": user.is_active
        }
        
    except Exception as e:
        logger.error(f"Error toggling user status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/users/{user_id}/change-role")
async def change_user_role(
    user_id: int,
    new_role: str,
    admin_claims: Dict[str, Any] = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Change user role"""
    try:
        if new_role not in ["user", "partner", "admin", "moderator"]:
            raise HTTPException(status_code=400, detail="Invalid role")
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        old_role = user.role
        user.role = new_role
        db.commit()
        
        return {
            "success": True,
            "message": f"User role changed from {old_role} to {new_role}",
            "user_id": user_id,
            "old_role": old_role,
            "new_role": new_role
        }
        
    except Exception as e:
        logger.error(f"Error changing user role: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/dashboard-enhanced")
async def admin_dashboard_enhanced(request: Request):
    """Serve enhanced admin dashboard"""
    try:
        with open("web/templates/admin-dashboard-enhanced.html", "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Admin dashboard not found")
    except Exception as e:
        logger.error(f"Error serving admin dashboard: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/export/users")
async def export_users(
    format: str = Query(default="json", regex="^(json|csv)$"),
    admin_claims: Dict[str, Any] = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Export users data"""
    try:
        users = db.query(User).all()
        
        if format == "json":
            user_data = [
                {
                    "id": user.id,
                    "full_name": user.full_name,
                    "username": user.username,
                    "email": user.email,
                    "role": user.role,
                    "is_active": user.is_active,
                    "created_at": user.created_at.isoformat()
                }
                for user in users
            ]
            return {"users": user_data, "total": len(users)}
        
        elif format == "csv":
            # In production, return CSV file
            return {"message": "CSV export not implemented yet"}
        
    except Exception as e:
        logger.error(f"Error exporting users: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/logs")
async def get_system_logs(
    level: Optional[str] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
    admin_claims: Dict[str, Any] = Depends(get_current_admin)
):
    """Get system logs (mock implementation)"""
    try:
        # In production, this would read from actual log files
        mock_logs = [
            {
                "timestamp": datetime.utcnow().isoformat(),
                "level": "INFO",
                "message": "Admin dashboard accessed",
                "user_id": admin_claims.get("user_id"),
                "module": "admin_panel"
            },
            {
                "timestamp": (datetime.utcnow() - timedelta(minutes=5)).isoformat(),
                "level": "WARNING",
                "message": "High memory usage detected",
                "user_id": None,
                "module": "system_monitor"
            },
            {
                "timestamp": (datetime.utcnow() - timedelta(minutes=10)).isoformat(),
                "level": "ERROR",
                "message": "Database connection timeout",
                "user_id": None,
                "module": "database"
            }
        ]
        
        if level:
            mock_logs = [log for log in mock_logs if log["level"] == level.upper()]
        
        return {"logs": mock_logs[:limit], "total": len(mock_logs)}
        
    except Exception as e:
        logger.error(f"Error getting system logs: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
