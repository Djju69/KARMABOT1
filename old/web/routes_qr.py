#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QR Code routes for KARMABOT1 WebApp
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import uuid

from core.services.qr_code_service import QRCodeService
from core.database import get_db
from core.security import get_current_user, get_current_claims
from core.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/qr", tags=["qr-codes"])


@router.get("/codes")
async def get_user_qr_codes(
    limit: int = 10,
    include_used: bool = False,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Get user's QR codes
    
    Args:
        limit: Maximum number of codes to return
        include_used: Whether to include used codes
        
    Returns:
        List of user's QR codes
    """
    try:
        qr_service = QRCodeService(db)
        user_id = current_user["user_id"]
        
        qr_codes = await qr_service.get_user_qr_codes(
            user_id=user_id,
            limit=limit,
            include_used=include_used
        )
        
        return qr_codes
        
    except Exception as e:
        logger.error(f"Error getting user QR codes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get QR codes"
        )


@router.post("/codes/generate")
async def generate_qr_code(
    request: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
) -> Dict[str, Any]:
    """
    Generate a new QR code for discount redemption
    
    Request body:
        discount_type: str - Type of discount (loyalty_points, percentage, fixed_amount)
        discount_value: int - Value of the discount
        expires_in_hours: int - Hours until QR code expires (default: 24)
        description: str - Description of the discount
        
    Returns:
        QR code data with image
    """
    try:
        qr_service = QRCodeService(db)
        user_id = current_user["user_id"]
        
        # Extract parameters from request
        discount_type = request.get("discount_type", "loyalty_points")
        discount_value = request.get("discount_value", 100)
        expires_in_hours = request.get("expires_in_hours", 24)
        description = request.get("description", "Скидка за баллы лояльности")
        
        # Validate parameters
        if discount_value <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Discount value must be positive"
            )
        
        if expires_in_hours <= 0 or expires_in_hours > 168:  # Max 7 days
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Expiration must be between 1 and 168 hours"
            )
        
        # Generate QR code
        qr_code = await qr_service.generate_qr_code(
            user_id=user_id,
            discount_type=discount_type,
            discount_value=discount_value,
            expires_in_hours=expires_in_hours,
            description=description
        )
        
        return qr_code
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating QR code: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate QR code"
        )


@router.get("/codes/{qr_id}/validate")
async def validate_qr_code(
    qr_id: str,
    db = Depends(get_db)
) -> Dict[str, Any]:
    """
    Validate a QR code (public endpoint for partners)
    
    Args:
        qr_id: QR code ID to validate
        
    Returns:
        Validation result and discount information
    """
    try:
        qr_service = QRCodeService(db)
        
        validation_result = await qr_service.validate_qr_code(qr_id)
        
        return validation_result
        
    except Exception as e:
        logger.error(f"Error validating QR code: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate QR code"
        )


@router.post("/codes/{qr_id}/redeem")
async def redeem_qr_code(
    qr_id: str,
    request: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
) -> Dict[str, Any]:
    """
    Redeem a QR code for discount (partner endpoint)
    
    Args:
        qr_id: QR code ID to redeem
        request: Contains partner information
        
    Returns:
        Redemption result
    """
    try:
        qr_service = QRCodeService(db)
        
        # Extract partner information
        partner_id = request.get("partner_id")
        partner_name = request.get("partner_name", "Unknown Partner")
        
        if not partner_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Partner ID is required"
            )
        
        # Redeem QR code
        redemption_result = await qr_service.redeem_qr_code(
            qr_id=qr_id,
            partner_id=partner_id,
            partner_name=partner_name
        )
        
        return redemption_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error redeeming QR code: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to redeem QR code"
        )


@router.get("/stats")
async def get_qr_code_stats(
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get QR code statistics for current user
    
    Returns:
        QR code statistics
    """
    try:
        qr_service = QRCodeService(db)
        user_id = current_user["user_id"]
        
        stats = await qr_service.get_qr_code_stats(user_id)
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting QR code stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get QR code statistics"
        )


@router.get("/scan")
async def scan_qr_code(
    qr_data: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
) -> Dict[str, Any]:
    """
    Scan and process QR code data
    
    Args:
        qr_data: QR code data string
        
    Returns:
        QR code information and validation result
    """
    try:
        import json
        
        # Parse QR code data
        try:
            qr_info = json.loads(qr_data)
            qr_id = qr_info.get("qr_id")
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid QR code format"
            )
        
        if not qr_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="QR code ID not found"
            )
        
        # Validate QR code
        qr_service = QRCodeService(db)
        validation_result = await qr_service.validate_qr_code(qr_id)
        
        return {
            "qr_data": qr_info,
            "validation": validation_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scanning QR code: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to scan QR code"
        )