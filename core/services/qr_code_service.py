#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QR Code Service for KARMABOT1
Handles QR code generation, validation, and redemption
"""

import qrcode
import qrcode.image.svg
from io import BytesIO
import base64
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_
from sqlalchemy.orm import selectinload

from core.database import get_db
from core.logger import get_logger
from core.models import QRCode, User, LoyaltyTransaction, LoyaltyTransactionType
from core.exceptions import NotFoundError, ValidationError, BusinessLogicError

logger = get_logger(__name__)


class QRCodeService:
    """Service for managing QR codes and discounts"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def generate_qr_code(
        self, 
        user_id: int, 
        discount_type: str = "loyalty_points",
        discount_value: int = 100,
        expires_in_hours: int = 24,
        description: str = "Скидка за баллы лояльности"
    ) -> Dict[str, Any]:
        """
        Generate a new QR code for discount redemption
        
        Args:
            user_id: ID of the user generating the QR code
            discount_type: Type of discount (loyalty_points, percentage, fixed_amount)
            discount_value: Value of the discount
            expires_in_hours: Hours until QR code expires
            description: Description of the discount
            
        Returns:
            Dict containing QR code data and image
        """
        try:
            # Validate user exists
            user_result = await self.db.execute(
                select(User).where(User.user_id == user_id)
            )
            user = user_result.scalar_one_or_none()
            if not user:
                raise NotFoundError("User not found")
            
            # Generate unique QR code
            qr_id = str(uuid.uuid4())
            qr_data = {
                "qr_id": qr_id,
                "user_id": user_id,
                "discount_type": discount_type,
                "discount_value": discount_value,
                "expires_at": datetime.utcnow() + timedelta(hours=expires_in_hours),
                "created_at": datetime.utcnow()
            }
            
            # Create QR code record in database
            qr_record = QRCode(
                qr_id=qr_id,
                user_id=user_id,
                discount_type=discount_type,
                discount_value=discount_value,
                description=description,
                expires_at=qr_data["expires_at"],
                is_used=False,
                used_at=None,
                used_by_partner_id=None
            )
            
            self.db.add(qr_record)
            await self.db.commit()
            
            # Generate QR code image
            qr_image = await self._generate_qr_image(qr_data)
            
            return {
                "qr_id": qr_id,
                "qr_image": qr_image,
                "discount_type": discount_type,
                "discount_value": discount_value,
                "description": description,
                "expires_at": qr_data["expires_at"].isoformat(),
                "expires_in_hours": expires_in_hours
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error generating QR code: {e}")
            raise BusinessLogicError(f"Failed to generate QR code: {str(e)}")
    
    async def _generate_qr_image(self, qr_data: Dict[str, Any]) -> str:
        """Generate QR code image as base64 string"""
        try:
            # Create QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            
            # Encode QR data as JSON string
            import json
            qr_string = json.dumps(qr_data, default=str)
            qr.add_data(qr_string)
            qr.make(fit=True)
            
            # Create image
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to base64
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            
            img_base64 = base64.b64encode(buffer.getvalue()).decode()
            return f"data:image/png;base64,{img_base64}"
            
        except Exception as e:
            logger.error(f"Error generating QR image: {e}")
            raise BusinessLogicError(f"Failed to generate QR image: {str(e)}")
    
    async def validate_qr_code(self, qr_id: str) -> Dict[str, Any]:
        """
        Validate QR code and return discount information
        
        Args:
            qr_id: QR code ID to validate
            
        Returns:
            Dict containing validation result and discount info
        """
        try:
            # Find QR code in database
            result = await self.db.execute(
                select(QRCode).where(QRCode.qr_id == qr_id)
            )
            qr_code = result.scalar_one_or_none()
            
            if not qr_code:
                return {
                    "valid": False,
                    "error": "QR code not found"
                }
            
            # Check if already used
            if qr_code.is_used:
                return {
                    "valid": False,
                    "error": "QR code already used",
                    "used_at": qr_code.used_at.isoformat() if qr_code.used_at else None
                }
            
            # Check if expired
            if qr_code.expires_at < datetime.utcnow():
                return {
                    "valid": False,
                    "error": "QR code expired",
                    "expires_at": qr_code.expires_at.isoformat()
                }
            
            # Get user info
            user_result = await self.db.execute(
                select(User).where(User.user_id == qr_code.user_id)
            )
            user = user_result.scalar_one_or_none()
            
            return {
                "valid": True,
                "qr_id": qr_id,
                "user_id": qr_code.user_id,
                "user_name": user.first_name if user else "Unknown",
                "discount_type": qr_code.discount_type,
                "discount_value": qr_code.discount_value,
                "description": qr_code.description,
                "expires_at": qr_code.expires_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error validating QR code: {e}")
            return {
                "valid": False,
                "error": f"Validation error: {str(e)}"
            }
    
    async def redeem_qr_code(
        self, 
        qr_id: str, 
        partner_id: int,
        partner_name: str = "Unknown Partner"
    ) -> Dict[str, Any]:
        """
        Redeem QR code for discount
        
        Args:
            qr_id: QR code ID to redeem
            partner_id: ID of the partner redeeming the code
            partner_name: Name of the partner
            
        Returns:
            Dict containing redemption result
        """
        try:
            # Validate QR code first
            validation = await self.validate_qr_code(qr_id)
            if not validation["valid"]:
                return {
                    "success": False,
                    "error": validation["error"]
                }
            
            # Get QR code record
            result = await self.db.execute(
                select(QRCode).where(QRCode.qr_id == qr_id)
            )
            qr_code = result.scalar_one()
            
            # Mark as used
            qr_code.is_used = True
            qr_code.used_at = datetime.utcnow()
            qr_code.used_by_partner_id = partner_id
            
            await self.db.commit()
            
            # Log the redemption
            logger.info(f"QR code {qr_id} redeemed by partner {partner_id} ({partner_name})")
            
            return {
                "success": True,
                "qr_id": qr_id,
                "user_id": qr_code.user_id,
                "discount_type": qr_code.discount_type,
                "discount_value": qr_code.discount_value,
                "description": qr_code.description,
                "redeemed_at": qr_code.used_at.isoformat(),
                "partner_id": partner_id,
                "partner_name": partner_name
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error redeeming QR code: {e}")
            return {
                "success": False,
                "error": f"Redemption error: {str(e)}"
            }
    
    async def get_user_qr_codes(
        self, 
        user_id: int, 
        limit: int = 10,
        include_used: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get user's QR codes
        
        Args:
            user_id: User ID
            limit: Maximum number of codes to return
            include_used: Whether to include used codes
            
        Returns:
            List of QR code records
        """
        try:
            query = select(QRCode).where(QRCode.user_id == user_id)
            
            if not include_used:
                query = query.where(QRCode.is_used == False)
            
            query = query.order_by(QRCode.created_at.desc()).limit(limit)
            
            result = await self.db.execute(query)
            qr_codes = result.scalars().all()
            
            return [
                {
                    "qr_id": qr.qr_id,
                    "discount_type": qr.discount_type,
                    "discount_value": qr.discount_value,
                    "description": qr.description,
                    "created_at": qr.created_at.isoformat(),
                    "expires_at": qr.expires_at.isoformat(),
                    "is_used": qr.is_used,
                    "used_at": qr.used_at.isoformat() if qr.used_at else None,
                    "used_by_partner_id": qr.used_by_partner_id
                }
                for qr in qr_codes
            ]
            
        except Exception as e:
            logger.error(f"Error getting user QR codes: {e}")
            return []
    
    async def get_qr_code_stats(self, user_id: int) -> Dict[str, Any]:
        """
        Get QR code statistics for user
        
        Args:
            user_id: User ID
            
        Returns:
            Dict containing QR code statistics
        """
        try:
            # Get total codes generated
            total_result = await self.db.execute(
                select(QRCode).where(QRCode.user_id == user_id)
            )
            total_codes = len(total_result.scalars().all())
            
            # Get used codes
            used_result = await self.db.execute(
                select(QRCode).where(
                    and_(QRCode.user_id == user_id, QRCode.is_used == True)
                )
            )
            used_codes = len(used_result.scalars().all())
            
            # Get active codes
            active_result = await self.db.execute(
                select(QRCode).where(
                    and_(
                        QRCode.user_id == user_id,
                        QRCode.is_used == False,
                        QRCode.expires_at > datetime.utcnow()
                    )
                )
            )
            active_codes = len(active_result.scalars().all())
            
            # Get expired codes
            expired_result = await self.db.execute(
                select(QRCode).where(
                    and_(
                        QRCode.user_id == user_id,
                        QRCode.is_used == False,
                        QRCode.expires_at <= datetime.utcnow()
                    )
                )
            )
            expired_codes = len(expired_result.scalars().all())
            
            return {
                "total_codes": total_codes,
                "used_codes": used_codes,
                "active_codes": active_codes,
                "expired_codes": expired_codes,
                "usage_rate": (used_codes / total_codes * 100) if total_codes > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting QR code stats: {e}")
            return {
                "total_codes": 0,
                "used_codes": 0,
                "active_codes": 0,
                "expired_codes": 0,
                "usage_rate": 0
            }


# Singleton instance
qr_code_service = QRCodeService(get_db())