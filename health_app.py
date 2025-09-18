from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from datetime import datetime
import os

app = FastAPI()

@app.get("/")
def read_root():
    return {"status": "ok"}


@app.get("/health")
def health() -> JSONResponse:
    """Lightweight healthcheck for Railway."""
    return JSONResponse(
        content={
            "status": "healthy",
            "version": os.getenv("APP_VERSION", "1.0.0"),
            "environment": os.getenv("ENVIRONMENT", "production"),
            "timestamp": datetime.now().isoformat(),
            "services": {"web": "running", "health_check": "ok"},
        },
        status_code=status.HTTP_200_OK,
    )
