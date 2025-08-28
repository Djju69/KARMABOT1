"""
Main router for API v1 endpoints.
"""
from fastapi import APIRouter
from . import partner, bonuses

# Create main router for all v1 endpoints
router = APIRouter()

# Include all routers
router.include_router(partner.router, prefix="/partner", tags=["partner"])
router.include_router(bonuses.router, prefix="/bonuses", tags=["bonuses"])
