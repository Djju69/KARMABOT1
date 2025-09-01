from fastapi import APIRouter
from . import categories, places

# Create a main router for all API v1 routes
router = APIRouter(prefix="/api/v1")

# Include all routers
router.include_router(categories.router)
router.include_router(places.router)

# This makes it possible to import all routers at once
__all__ = ["router", "categories", "places"]
