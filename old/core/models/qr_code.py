#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QR Code model for KARMABOT1
"""

from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from core.database import Base


class QRCode(Base):
    """QR Code model for discount redemption"""
    
    __tablename__ = "qr_codes"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # QR code identifier
    qr_id = Column(String(36), unique=True, index=True, nullable=False)
    
    # User who generated the QR code
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    
    # Discount information
    discount_type = Column(String(50), nullable=False)  # loyalty_points, percentage, fixed_amount
    discount_value = Column(Integer, nullable=False)  # Value of the discount
    description = Column(Text, nullable=True)  # Description of the discount
    
    # Expiration
    expires_at = Column(DateTime, nullable=False)
    
    # Usage tracking
    is_used = Column(Boolean, default=False, nullable=False)
    used_at = Column(DateTime, nullable=True)
    used_by_partner_id = Column(Integer, ForeignKey("partners_v2.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="qr_codes")
    partner = relationship("PartnerV2", back_populates="redeemed_qr_codes")
    
    def __repr__(self):
        return f"<QRCode(id={self.id}, qr_id={self.qr_id}, user_id={self.user_id}, discount_type={self.discount_type})>"
    
    def is_expired(self) -> bool:
        """Check if QR code is expired"""
        return datetime.utcnow() > self.expires_at
    
    def can_be_used(self) -> bool:
        """Check if QR code can be used"""
        return not self.is_used and not self.is_expired()
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "qr_id": self.qr_id,
            "user_id": self.user_id,
            "discount_type": self.discount_type,
            "discount_value": self.discount_value,
            "description": self.description,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "is_used": self.is_used,
            "used_at": self.used_at.isoformat() if self.used_at else None,
            "used_by_partner_id": self.used_by_partner_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
