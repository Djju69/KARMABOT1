"""
Entry point for running the web server directly.
Example: python -m web
"""
import uvicorn
from .main import app

if __name__ == "__main__":
    uvicorn.run(
        "web.main:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    )
