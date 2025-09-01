"""
QR Code API endpoints for generating and validating QR codes.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse, Response
from typing import Optional, Dict, Any
import segno
import json
from datetime import datetime, timedelta, timezone
import io
import base64
from pydantic import BaseModel, Field
from uuid import UUID, uuid4

router = APIRouter(prefix="/api/qr", tags=["qr"])

# In-memory storage for demo (replace with database in production)
qr_codes_db: Dict[str, Dict[str, Any]] = {}

class QRCodeRequest(BaseModel):
    """Request model for generating a new QR code"""
    partner_id: UUID
    discount_percent: int = Field(..., ge=1, le=100, description="Discount percentage (1-100)")
    expires_in_hours: Optional[int] = Field(24, ge=1, le=168, description="Expiration time in hours (1-168, default 24)")
    max_uses: Optional[int] = Field(1, ge=1, description="Maximum number of uses (default 1)")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")

class QRCodeResponse(BaseModel):
    """Response model for QR code generation"""
    qr_id: str
    qr_data_url: str
    expires_at: datetime
    remaining_uses: int

@router.post("/generate", response_model=QRCodeResponse)
async def generate_qr_code(request: QRCodeRequest):
    """
    Generate a new QR code for discounts.
    
    The QR code contains a unique ID that can be validated later.
    """
    # Generate a unique ID for this QR code
    qr_id = f"qr_{uuid4().hex[:12]}"
    
    # Calculate expiration time
    expires_at = datetime.now(timezone.utc) + timedelta(hours=request.expires_in_hours)
    
    # Create QR code data
    qr_data = {
        "qr_id": qr_id,
        "partner_id": str(request.partner_id),
        "discount_percent": request.discount_percent,
        "expires_at": expires_at.isoformat(),
        "max_uses": request.max_uses,
        "metadata": request.metadata
    }
    
    # Store in database (in-memory for demo)
    qr_codes_db[qr_id] = {
        **qr_data,
        "remaining_uses": request.max_uses,
        "is_active": True
    }
    
    # Generate QR code image
    qr = segno.make(json.dumps(qr_data), error='h')
    
    # Convert to data URL
    buffer = io.BytesIO()
    qr.save(buffer, kind="png", scale=5)
    qr_data_url = f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"
    
    return {
        "qr_id": qr_id,
        "qr_data_url": qr_data_url,
        "expires_at": expires_at,
        "remaining_uses": request.max_uses
    }

class QRCodeValidationRequest(BaseModel):
    """Request model for validating a QR code"""
    qr_data: str

@router.post("/validate")
async def validate_qr_code(request: QRCodeValidationRequest):
    """
    Validate a scanned QR code and apply discount if valid.
    """
    try:
        # Parse QR code data
        try:
            qr_data = json.loads(request.qr_data)
            qr_id = qr_data.get("qr_id")
        except (json.JSONDecodeError, AttributeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid QR code format"
            )
        
        # Check if QR code exists and is active
        qr_info = qr_codes_db.get(qr_id)
        if not qr_info or not qr_info.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="QR code not found or inactive"
            )
        
        # Check expiration
        expires_at = datetime.fromisoformat(qr_info["expires_at"])
        if datetime.now(timezone.utc) > expires_at:
            qr_info["is_active"] = False  # Mark as expired
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="QR code has expired"
            )
        
        # Check remaining uses
        if qr_info["remaining_uses"] <= 0:
            qr_info["is_active"] = False  # Mark as used up
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="QR code has been used up"
            )
        
        # Decrement remaining uses
        qr_info["remaining_uses"] -= 1
        if qr_info["remaining_uses"] <= 0:
            qr_info["is_active"] = False
        
        # Return success response with discount info
        return {
            "valid": True,
            "discount_percent": qr_info["discount_percent"],
            "partner_id": qr_info["partner_id"],
            "remaining_uses": qr_info["remaining_uses"],
            "metadata": qr_info.get("metadata", {})
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error validating QR code: {str(e)}"
        )

@router.get("/{qr_id}/status")
async def get_qr_status(qr_id: str):
    """
    Get the status of a QR code by ID
    """
    qr_info = qr_codes_db.get(qr_id)
    if not qr_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="QR code not found"
        )
    
    return {
        "qr_id": qr_id,
        "is_active": qr_info.get("is_active", False),
        "remaining_uses": qr_info.get("remaining_uses", 0),
        "expires_at": qr_info.get("expires_at"),
        "discount_percent": qr_info.get("discount_percent"),
        "partner_id": qr_info.get("partner_id")
    }
