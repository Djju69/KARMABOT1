"""
Partner Verification Service
Handles partner verification and approval workflow
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from enum import Enum

from core.database.db_v2 import db_v2
from core.logger import get_logger

logger = get_logger(__name__)

class VerificationStatus(Enum):
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    REQUIRES_DOCUMENTS = "requires_documents"

class VerificationResult(Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_MORE_INFO = "needs_more_info"
    DOCUMENTS_REQUIRED = "documents_required"

class PartnerVerificationService:
    """Service for partner verification and approval"""
    
    @staticmethod
    async def get_pending_verifications() -> List[Dict[str, Any]]:
        """Get all pending partner verifications"""
        try:
            with db_v2.get_session() as session:
                partners = session.query(db_v2.Partner).filter(
                    db_v2.Partner.verification_status == VerificationStatus.PENDING.value
                ).all()
                
                return [
                    {
                        "id": partner.id,
                        "user_id": partner.user_id,
                        "business_name": partner.business_name,
                        "business_type": partner.business_type,
                        "description": partner.description,
                        "contact_info": partner.contact_info,
                        "location": partner.location,
                        "created_at": partner.created_at,
                        "verification_status": partner.verification_status
                    }
                    for partner in partners
                ]
        except Exception as e:
            logger.error(f"Error getting pending verifications: {e}")
            return []
    
    @staticmethod
    async def get_verification_details(partner_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed verification information for a partner"""
        try:
            with db_v2.get_session() as session:
                partner = session.query(db_v2.Partner).filter(
                    db_v2.Partner.id == partner_id
                ).first()
                
                if not partner:
                    return None
                
                # Get additional verification data
                verification_data = {
                    "id": partner.id,
                    "user_id": partner.user_id,
                    "business_name": partner.business_name,
                    "business_type": partner.business_type,
                    "description": partner.description,
                    "contact_info": partner.contact_info,
                    "location": partner.location,
                    "verification_status": partner.verification_status,
                    "created_at": partner.created_at,
                    "terms_accepted": partner.terms_accepted,
                    "terms_accepted_at": partner.terms_accepted_at,
                    "verification_score": await PartnerVerificationService._calculate_verification_score(partner),
                    "risk_level": await PartnerVerificationService._assess_risk_level(partner)
                }
                
                return verification_data
                
        except Exception as e:
            logger.error(f"Error getting verification details: {e}")
            return None
    
    @staticmethod
    async def approve_partner(partner_id: int, moderator_id: int, notes: str = "") -> bool:
        """Approve partner verification"""
        try:
            with db_v2.get_session() as session:
                partner = session.query(db_v2.Partner).filter(
                    db_v2.Partner.id == partner_id
                ).first()
                
                if not partner:
                    return False
                
                # Update partner status
                partner.verification_status = VerificationStatus.APPROVED.value
                partner.verified_at = datetime.utcnow()
                partner.verified_by = moderator_id
                partner.verification_notes = notes
                
                session.commit()
                
                # Log verification action
                await PartnerVerificationService._log_verification_action(
                    partner_id, moderator_id, "approve", notes
                )
                
                # Send notification to partner
                await PartnerVerificationService._notify_partner(
                    partner.user_id, "approved", notes
                )
                
                logger.info(f"Partner {partner_id} approved by moderator {moderator_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error approving partner: {e}")
            return False
    
    @staticmethod
    async def reject_partner(partner_id: int, moderator_id: int, reason: str, notes: str = "") -> bool:
        """Reject partner verification"""
        try:
            with db_v2.get_session() as session:
                partner = session.query(db_v2.Partner).filter(
                    db_v2.Partner.id == partner_id
                ).first()
                
                if not partner:
                    return False
                
                # Update partner status
                partner.verification_status = VerificationStatus.REJECTED.value
                partner.verified_at = datetime.utcnow()
                partner.verified_by = moderator_id
                partner.rejection_reason = reason
                partner.verification_notes = notes
                
                session.commit()
                
                # Log verification action
                await PartnerVerificationService._log_verification_action(
                    partner_id, moderator_id, "reject", f"{reason}: {notes}"
                )
                
                # Send notification to partner
                await PartnerVerificationService._notify_partner(
                    partner.user_id, "rejected", f"{reason}: {notes}"
                )
                
                logger.info(f"Partner {partner_id} rejected by moderator {moderator_id}: {reason}")
                return True
                
        except Exception as e:
            logger.error(f"Error rejecting partner: {e}")
            return False
    
    @staticmethod
    async def request_additional_documents(partner_id: int, moderator_id: int, required_docs: List[str], notes: str = "") -> bool:
        """Request additional documents from partner"""
        try:
            with db_v2.get_session() as session:
                partner = session.query(db_v2.Partner).filter(
                    db_v2.Partner.id == partner_id
                ).first()
                
                if not partner:
                    return False
                
                # Update partner status
                partner.verification_status = VerificationStatus.REQUIRES_DOCUMENTS.value
                partner.verification_notes = notes
                partner.required_documents = ", ".join(required_docs)
                
                session.commit()
                
                # Log verification action
                await PartnerVerificationService._log_verification_action(
                    partner_id, moderator_id, "request_documents", f"Required: {', '.join(required_docs)}"
                )
                
                # Send notification to partner
                await PartnerVerificationService._notify_partner(
                    partner.user_id, "documents_required", f"Required: {', '.join(required_docs)}"
                )
                
                logger.info(f"Additional documents requested for partner {partner_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error requesting additional documents: {e}")
            return False
    
    @staticmethod
    async def _calculate_verification_score(partner) -> int:
        """Calculate verification score based on provided information"""
        score = 0
        
        # Business name (20 points)
        if partner.business_name and len(partner.business_name) > 3:
            score += 20
        
        # Description (20 points)
        if partner.description and len(partner.description) > 20:
            score += 20
        
        # Contact info (20 points)
        if partner.contact_info:
            if any(char.isdigit() for char in partner.contact_info):  # Has phone
                score += 10
            if "@" in partner.contact_info:  # Has email
                score += 10
        
        # Location (20 points)
        if partner.location and len(partner.location) > 10:
            score += 20
        
        # Terms acceptance (20 points)
        if partner.terms_accepted:
            score += 20
        
        return min(score, 100)
    
    @staticmethod
    async def _assess_risk_level(partner) -> str:
        """Assess risk level for partner verification"""
        score = await PartnerVerificationService._calculate_verification_score(partner)
        
        if score >= 80:
            return "low"
        elif score >= 60:
            return "medium"
        else:
            return "high"
    
    @staticmethod
    async def _log_verification_action(partner_id: int, moderator_id: int, action: str, notes: str):
        """Log verification action"""
        try:
            # This would log to a verification_logs table
            # For now, we'll use the existing moderation_logs
            with db_v2.get_session() as session:
                log_entry = db_v2.ModerationLog(
                    moderator_id=moderator_id,
                    card_id=None,  # No card for partner verification
                    action=f"partner_{action}",
                    comment=f"Partner {partner_id}: {notes}",
                    created_at=datetime.utcnow()
                )
                session.add(log_entry)
                session.commit()
                
        except Exception as e:
            logger.error(f"Error logging verification action: {e}")
    
    @staticmethod
    async def _notify_partner(user_id: int, status: str, message: str):
        """Send notification to partner about verification status"""
        try:
            # This would integrate with notification service
            # For now, we'll just log the notification
            logger.info(f"Notification to partner {user_id}: {status} - {message}")
            
        except Exception as e:
            logger.error(f"Error sending notification to partner: {e}")
    
    @staticmethod
    async def get_verification_statistics() -> Dict[str, Any]:
        """Get verification statistics"""
        try:
            with db_v2.get_session() as session:
                total_partners = session.query(db_v2.Partner).count()
                pending_partners = session.query(db_v2.Partner).filter(
                    db_v2.Partner.verification_status == VerificationStatus.PENDING.value
                ).count()
                approved_partners = session.query(db_v2.Partner).filter(
                    db_v2.Partner.verification_status == VerificationStatus.APPROVED.value
                ).count()
                rejected_partners = session.query(db_v2.Partner).filter(
                    db_v2.Partner.verification_status == VerificationStatus.REJECTED.value
                ).count()
                
                # Calculate approval rate
                processed_partners = approved_partners + rejected_partners
                approval_rate = (approved_partners / processed_partners * 100) if processed_partners > 0 else 0
                
                return {
                    "total_partners": total_partners,
                    "pending_partners": pending_partners,
                    "approved_partners": approved_partners,
                    "rejected_partners": rejected_partners,
                    "approval_rate": round(approval_rate, 2),
                    "processing_time_avg": await PartnerVerificationService._get_avg_processing_time()
                }
                
        except Exception as e:
            logger.error(f"Error getting verification statistics: {e}")
            return {}
    
    @staticmethod
    async def _get_avg_processing_time() -> float:
        """Get average processing time for verifications"""
        try:
            with db_v2.get_session() as session:
                # This would calculate average time from creation to verification
                # For now, return a mock value
                return 24.0  # hours
                
        except Exception as e:
            logger.error(f"Error calculating average processing time: {e}")
            return 0.0
    
    @staticmethod
    async def get_verification_history(partner_id: int) -> List[Dict[str, Any]]:
        """Get verification history for a partner"""
        try:
            with db_v2.get_session() as session:
                logs = session.query(db_v2.ModerationLog).filter(
                    db_v2.ModerationLog.comment.like(f"Partner {partner_id}:%")
                ).order_by(db_v2.ModerationLog.created_at.desc()).all()
                
                return [
                    {
                        "id": log.id,
                        "moderator_id": log.moderator_id,
                        "action": log.action,
                        "comment": log.comment,
                        "created_at": log.created_at
                    }
                    for log in logs
                ]
                
        except Exception as e:
            logger.error(f"Error getting verification history: {e}")
            return []
    
    @staticmethod
    async def auto_verify_partner(partner_id: int) -> Optional[VerificationResult]:
        """Automatically verify partner based on criteria"""
        try:
            verification_details = await PartnerVerificationService.get_verification_details(partner_id)
            
            if not verification_details:
                return None
            
            score = verification_details.get("verification_score", 0)
            risk_level = verification_details.get("risk_level", "high")
            
            # Auto-approve if score is high and risk is low
            if score >= 90 and risk_level == "low":
                await PartnerVerificationService.approve_partner(
                    partner_id, 0, "Auto-approved: High score, low risk"
                )
                return VerificationResult.APPROVED
            
            # Auto-reject if score is very low
            elif score < 40:
                await PartnerVerificationService.reject_partner(
                    partner_id, 0, "Insufficient information", "Auto-rejected: Low verification score"
                )
                return VerificationResult.REJECTED
            
            # Request more info if score is medium
            elif score < 70:
                required_docs = ["Business registration", "Photo of establishment"]
                await PartnerVerificationService.request_additional_documents(
                    partner_id, 0, required_docs, "Auto-request: Additional documents required"
                )
                return VerificationResult.DOCUMENTS_REQUIRED
            
            # Otherwise, needs manual review
            return VerificationResult.NEEDS_MORE_INFO
            
        except Exception as e:
            logger.error(f"Error in auto verification: {e}")
            return None
