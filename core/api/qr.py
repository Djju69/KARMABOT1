"""
API endpoints for QR code functionality including discount and loyalty points.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from fastapi.responses import JSONResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db_session
from core.services.qr_code_service import qr_code_service
from core.settings import settings
from core.utils.telemetry import log_event
from core.utils.i18n import gettext as _

router = APIRouter(prefix="/api/qr", tags=["qr"])


class QRCodeRedeemRequest(BaseModel):
    """Request model for redeeming a QR code."""
    token: str
    bill_amount: int = Field(..., gt=0, description="Bill amount in kopeks (1/100 of RUB)")
    partner_id: int = Field(..., gt=0, description="ID of the partner redeeming the code")


@router.post("/redeem", response_model=dict)
async def redeem_qr(
    request: QRCodeRedeemRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Redeem a discount QR code.
    
    Validates and processes the QR code redemption, applying the discount to the bill.
    
    Returns:
        dict: {
            "success": bool,
            "discount_amount": int,  # in kopeks
            "final_amount": int,     # in kopeks
            "listing_title": str
        }
    """
    try:
        result = await qr_code_service.redeem_qr_code(
            token=request.token,
            partner_id=request.partner_id,
            bill_amount=request.bill_amount
        )
        
        await log_event(
            actor_id=request.partner_id,
            entity_type="qr_redemption",
            entity_id=request.token[:8] + "...",
            action="success",
            details={
                "discount_amount": result["discount_amount"],
                "final_amount": result["final_amount"]
            }
        )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "discount_amount": result["discount_amount"],
                "final_amount": result["final_amount"],
                "listing_title": result["listing_title"]
            }
        )
        
    except ValueError as e:
        error_code = str(e)
        error_details = {
            "success": False,
            "error": error_code,
            "message": ""
        }
        
        if error_code == "invalid_token":
            error_details["message"] = _("Invalid QR code")
            status_code = status.HTTP_400_BAD_REQUEST
        elif error_code == "not_found":
            error_details["message"] = _("QR code not found")
            status_code = status.HTTP_404_NOT_FOUND
        elif error_code == "already_redeemed":
            error_details["message"] = _("This QR code has already been used")
            status_code = status.HTTP_400_BAD_REQUEST
        elif error_code == "expired":
            error_details["message"] = _("QR code has expired")
            status_code = status.HTTP_400_BAD_REQUEST
        elif error_code == "invalid_status":
            error_details["message"] = _("Invalid QR code status")
            status_code = status.HTTP_400_BAD_REQUEST
        elif error_code == "listing_not_found":
            error_details["message"] = _("Associated offer not found")
            status_code = status.HTTP_404_NOT_FOUND
        else:
            error_details["message"] = _("An error occurred while processing the QR code")
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        
        await log_event(
            actor_id=request.partner_id,
            entity_type="qr_redemption",
            entity_id=request.token[:8] + "...",
            action="error",
            details={
                "error": error_code,
                "message": error_details["message"]
            }
        )
        
        return JSONResponse(
            status_code=status_code,
            content=error_details
        )


@router.get("/generate/discount/{listing_id}")
async def generate_discount_qr(
    listing_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Generate a discount QR code for a listing.
    
    Args:
        listing_id: ID of the listing
        user_id: ID of the user generating the QR code
        
    Returns:
        Response: PNG image of the QR code
    """
    qr_service = QRService(db)
    qr_image, _ = await qr_service.create_qr(user_id, listing_id=listing_id)
    
    return Response(
        content=qr_image,
        media_type="image/png",
        headers={"Content-Disposition": f"inline; filename=discount_{listing_id}.png"}
    )


@router.get("/generate/points/{points}")
async def generate_points_qr(
    points: int,
    user_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Generate a points spending QR code.
    
    Args:
        points: Number of points to spend
        user_id: ID of the user generating the QR code
        
    Returns:
        Response: PNG image of the QR code
    """
    qr_service = QRService(db)
    qr_image, _ = await qr_service.create_qr(user_id, points=points)
    
    return Response(
        content=qr_image,
        media_type="image/png",
        headers={"Content-Disposition": f"inline; filename=points_{points}.png"}
    )


@router.get("/info/{token}")
async def get_qr_info(
    token: str,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get information about a QR code.
    
    Args:
        token: QR code token
        
    Returns:
        dict: QR code information
    """
    qr_service = QRService(db)
    info = await qr_service.get_qr_info(token)
    
    if not info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="QR code not found"
        )
    
    return info
