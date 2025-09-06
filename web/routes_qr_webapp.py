"""
QR WebApp API endpoints for enhanced user experience
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import logging
from datetime import datetime, timedelta

from core.database import get_db
from core.services.qr_code_service import QRCodeService
from core.services.user_profile_service import user_profile_service
from core.services.loyalty_service import loyalty_service
from core.auth import get_current_user
from core.models.qr_code import QRCode
from core.models.user_profile import UserLevel
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/qr", tags=["QR WebApp"])

class QRScanRequest(BaseModel):
    """Request model for QR code scanning"""
    qr_data: str

class QRRedeemRequest(BaseModel):
    """Request model for QR code redemption"""
    qr_id: str

class QRGenerateRequest(BaseModel):
    """Request model for QR code generation"""
    discount_type: str = "loyalty_points"
    discount_value: int = 100
    expires_in_hours: int = 24
    description: Optional[str] = None

@router.get("/scanner", response_class=HTMLResponse)
async def qr_scanner_page():
    """Serve QR scanner WebApp page"""
    try:
        with open("web/templates/qr-scanner.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="QR scanner page not found"
        )

@router.post("/scan", response_model=Dict[str, Any])
async def scan_qr_code(
    request: QRScanRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Scan and validate QR code data
    
    Args:
        request: QR scan request with qr_data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        QR code information and validation result
    """
    try:
        user_id = current_user["user_id"]
        
        # Parse QR code data
        import json
        try:
            qr_info = json.loads(request.qr_data)
            qr_id = qr_info.get("qr_id")
        except json.JSONDecodeError:
            # Try to treat as direct QR ID
            qr_id = request.qr_data.strip()
        
        if not qr_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="QR code ID not found"
            )
        
        # Get QR code from database
        result = await db.execute(
            select(QRCode).where(QRCode.qr_id == qr_id)
        )
        qr_code = result.scalar_one_or_none()
        
        if not qr_code:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="QR code not found"
            )
        
        # Check if QR code is expired
        if qr_code.is_expired():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="QR code has expired"
            )
        
        # Check if QR code is already used
        if qr_code.is_used:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="QR code has already been used"
            )
        
        # Get user profile for level-based discounts
        user_profile = await user_profile_service.get_user_profile(user_id)
        level_benefits = user_profile["level_benefits"]
        
        # Calculate final discount based on user level
        base_discount = qr_code.discount_value
        level_multiplier = level_benefits["points_multiplier"]
        final_discount = int(base_discount * level_multiplier)
        
        # Log QR scan activity
        await user_profile_service.log_user_activity(
            user_id=user_id,
            activity_type="qr_scan",
            points_earned=10,  # Base points for scanning
            activity_data={"qr_id": qr_id, "discount_type": qr_code.discount_type}
        )
        
        return {
            "qr_id": qr_code.qr_id,
            "discount_type": qr_code.discount_type,
            "discount_value": final_discount,
            "base_discount": base_discount,
            "level_multiplier": level_multiplier,
            "description": qr_code.description,
            "expires_at": qr_code.expires_at.isoformat(),
            "user_level": user_profile["level"],
            "level_benefits": level_benefits,
            "can_redeem": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scanning QR code: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to scan QR code"
        )

@router.post("/redeem", response_model=Dict[str, Any])
async def redeem_qr_code(
    request: QRRedeemRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Redeem QR code for discount
    
    Args:
        request: QR redeem request with qr_id
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Redemption result
    """
    try:
        user_id = current_user["user_id"]
        
        # Get QR code from database
        result = await db.execute(
            select(QRCode).where(QRCode.qr_id == request.qr_id)
        )
        qr_code = result.scalar_one_or_none()
        
        if not qr_code:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="QR code not found"
            )
        
        # Validate QR code
        if qr_code.is_expired():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="QR code has expired"
            )
        
        if qr_code.is_used:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="QR code has already been used"
            )
        
        # Get user profile for level-based benefits
        user_profile = await user_profile_service.get_user_profile(user_id)
        level_benefits = user_profile["level_benefits"]
        
        # Calculate final discount
        base_discount = qr_code.discount_value
        level_multiplier = level_benefits["points_multiplier"]
        final_discount = int(base_discount * level_multiplier)
        
        # Apply discount based on type
        if qr_code.discount_type == "loyalty_points":
            # Add loyalty points
            await loyalty_service.add_points(
                user_id=user_id,
                points=final_discount,
                transaction_type="qr_redeem",
                description=f"QR код: {qr_code.description or 'Скидка'}"
            )
            
        elif qr_code.discount_type == "percentage":
            # Store percentage discount for later use
            # This would typically be used at checkout
            pass
            
        elif qr_code.discount_type == "fixed_amount":
            # Store fixed amount discount
            pass
        
        # Mark QR code as used
        qr_code.is_used = True
        qr_code.used_at = datetime.utcnow()
        qr_code.used_by_partner_id = None  # User redemption
        await db.commit()
        
        # Log redemption activity
        await user_profile_service.log_user_activity(
            user_id=user_id,
            activity_type="qr_redeem",
            points_earned=final_discount,
            activity_data={
                "qr_id": qr_code.qr_id,
                "discount_type": qr_code.discount_type,
                "discount_value": final_discount
            }
        )
        
        # Check for achievements
        await check_qr_achievements(user_id, db)
        
        return {
            "success": True,
            "qr_id": qr_code.qr_id,
            "discount_type": qr_code.discount_type,
            "discount_value": final_discount,
            "level_multiplier": level_multiplier,
            "user_level": user_profile["level"],
            "message": "QR код успешно использован!"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error redeeming QR code: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to redeem QR code"
        )

@router.post("/generate", response_model=Dict[str, Any])
async def generate_qr_code(
    request: QRGenerateRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Generate new QR code for user
    
    Args:
        request: QR generation request
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Generated QR code information
    """
    try:
        user_id = current_user["user_id"]
        
        # Get user profile to check level benefits
        user_profile = await user_profile_service.get_user_profile(user_id)
        level_benefits = user_profile["level_benefits"]
        
        # Apply level multiplier to discount value
        level_multiplier = level_benefits["points_multiplier"]
        enhanced_discount = int(request.discount_value * level_multiplier)
        
        # Create QR code service instance
        qr_service = QRCodeService(db)
        
        # Generate QR code
        qr_result = await qr_service.generate_qr_code(
            user_id=user_id,
            discount_type=request.discount_type,
            discount_value=enhanced_discount,
            expires_in_hours=request.expires_in_hours,
            description=request.description or f"Скидка {enhanced_discount} очков"
        )
        
        # Log QR generation activity
        await user_profile_service.log_user_activity(
            user_id=user_id,
            activity_type="qr_generate",
            points_earned=5,  # Small reward for generating QR
            activity_data={
                "qr_id": qr_result["qr_id"],
                "discount_type": request.discount_type,
                "discount_value": enhanced_discount
            }
        )
        
        return {
            "qr_id": qr_result["qr_id"],
            "qr_image": qr_result["qr_image"],
            "discount_type": request.discount_type,
            "discount_value": enhanced_discount,
            "base_discount": request.discount_value,
            "level_multiplier": level_multiplier,
            "description": qr_result["description"],
            "expires_at": qr_result["expires_at"],
            "expires_in_hours": request.expires_in_hours,
            "user_level": user_profile["level"]
        }
        
    except Exception as e:
        logger.error(f"Error generating QR code: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate QR code"
        )

@router.get("/history")
async def get_qr_history(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 20
) -> List[Dict[str, Any]]:
    """
    Get user's QR code history
    
    Args:
        current_user: Current authenticated user
        db: Database session
        limit: Maximum number of records to return
        
    Returns:
        List of QR code history records
    """
    try:
        user_id = current_user["user_id"]
        
        # Get QR codes created by user
        result = await db.execute(
            select(QRCode)
            .where(QRCode.user_id == user_id)
            .order_by(QRCode.created_at.desc())
            .limit(limit)
        )
        qr_codes = result.scalars().all()
        
        history = []
        for qr in qr_codes:
            history.append({
                "qr_id": qr.qr_id,
                "discount_type": qr.discount_type,
                "discount_value": qr.discount_value,
                "description": qr.description,
                "is_used": qr.is_used,
                "used_at": qr.used_at.isoformat() if qr.used_at else None,
                "expires_at": qr.expires_at.isoformat(),
                "created_at": qr.created_at.isoformat(),
                "is_expired": qr.is_expired()
            })
        
        return history
        
    except Exception as e:
        logger.error(f"Error getting QR history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get QR history"
        )

@router.get("/stats")
async def get_qr_stats(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get user's QR code statistics
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        QR code statistics
    """
    try:
        user_id = current_user["user_id"]
        
        # Get user profile for QR scan stats
        user_profile = await user_profile_service.get_user_profile(user_id)
        
        # Get QR codes created by user
        result = await db.execute(
            select(QRCode).where(QRCode.user_id == user_id)
        )
        user_qr_codes = result.scalars().all()
        
        # Calculate statistics
        total_generated = len(user_qr_codes)
        total_used = sum(1 for qr in user_qr_codes if qr.is_used)
        total_expired = sum(1 for qr in user_qr_codes if qr.is_expired() and not qr.is_used)
        total_scans = user_profile["total_qr_scans"]
        
        return {
            "total_generated": total_generated,
            "total_used": total_used,
            "total_expired": total_expired,
            "total_scans": total_scans,
            "usage_rate": (total_used / total_generated * 100) if total_generated > 0 else 0,
            "user_level": user_profile["level"],
            "level_benefits": user_profile["level_benefits"]
        }
        
    except Exception as e:
        logger.error(f"Error getting QR stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get QR statistics"
        )

async def check_qr_achievements(user_id: int, db: AsyncSession):
    """Check and unlock QR-related achievements"""
    try:
        # Get user profile
        user_profile = await user_profile_service.get_user_profile(user_id)
        
        # Check for QR scan achievements
        total_scans = user_profile["total_qr_scans"]
        
        if total_scans == 1:
            await user_profile_service.unlock_achievement(
                user_id=user_id,
                achievement_type="qr_scanner",
                achievement_name="Первый QR",
                achievement_description="Отсканировали первый QR-код",
                points_reward=50
            )
        elif total_scans == 10:
            await user_profile_service.unlock_achievement(
                user_id=user_id,
                achievement_type="qr_scanner",
                achievement_name="QR Мастер",
                achievement_description="Отсканировали 10 QR-кодов",
                points_reward=200
            )
        elif total_scans == 50:
            await user_profile_service.unlock_achievement(
                user_id=user_id,
                achievement_type="qr_scanner",
                achievement_name="QR Эксперт",
                achievement_description="Отсканировали 50 QR-кодов",
                points_reward=500
            )
        
    except Exception as e:
        logger.error(f"Error checking QR achievements: {e}")
