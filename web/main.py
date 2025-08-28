"""
FastAPI application for KarmaBot web interface and API endpoints.
"""
from __future__ import annotations
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import os

from .database import check_database_health, init_db, Base, engine
from .routes_cabinet import get_current_claims
from .api.v1.router import router as api_v1_router

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="KARMABOT1 WebApp",
    description="API for KarmaBot partner cabinet",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(api_v1_router, prefix="/api")

# Mount static files
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.on_event("startup")
async def startup_event():
    """Initialize application services."""
    # Initialize database
    init_db()

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Welcome to KarmaBot API"}

@app.get("/health")
async def health():
    """Basic health check endpoint."""
    return {"status": "ok"}

@app.get("/healthz")
async def healthz():
    """Database health check endpoint."""
    ok, detail = check_database_health()
    if not ok:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "detail": detail}
        )
    return {"status": "ok", "detail": detail}

# Example protected route
@app.get("/api/me")
async def read_users_me(claims: dict = Depends(get_current_claims)):
    """Get current user information."""
    return claims
