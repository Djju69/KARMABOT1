"""Health check endpoints for monitoring."""
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from typing import Dict, Any
import os
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get(
    "/health",
    summary="Health check endpoint",
    description="Returns the current health status of the service",
    response_model=Dict[str, Any]
)
async def health_check() -> JSONResponse:
    """Health check endpoint for monitoring."""
    try:
        # Add your health check logic here
        # For example, check database connection, external services, etc.
        
        status_info = {
            "status": "healthy",
            "version": os.getenv("APP_VERSION", "1.0.0"),
            "environment": os.getenv("ENVIRONMENT", "development"),
            "services": {
                "database": "connected",  # Add actual check
                # Add other services as needed
            }
        }
        
        return JSONResponse(
            content=status_info,
            status_code=status.HTTP_200_OK
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        return JSONResponse(
            content={"status": "unhealthy", "error": str(e)},
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )
