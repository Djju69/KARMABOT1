"""
Compatibility layer for legacy imports.
New code should import from core.services.loyalty instead.
"""
from .loyalty import loyalty_service, LoyaltyService

__all__ = ['loyalty_service', 'LoyaltyService']
