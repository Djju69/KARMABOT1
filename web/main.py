"""
FastAPI application for KarmaBot web interface and API endpoints.
"""
from __future__ import annotations
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from .database import check_database_health

app = FastAPI(title="KARMABOT1 WebApp")

@app.get("/health")
async def health():
    """Basic health check endpoint"""
    return {"status": "ok"}

@app.get("/healthz")
async def healthz():
    """Database health check endpoint"""
    ok, detail = check_database_health()
    if not ok:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "detail": detail}
        )
    return {"status": "ok", "detail": detail}
