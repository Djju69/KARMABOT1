"""
API v1 package for KarmaBot web application.
"""
from fastapi import APIRouter
from . import partner, bonuses

# Create a main router for all v1 endpoints
router = APIRouter(prefix="/v1")

# Include all routers
router.include_router(partner.router)
router.include_router(bonuses.router)

__all__ = ["router"]
