from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

# Import project settings and auth utils
try:
    from core.settings import settings
except Exception:
    # Simple fallback settings if core.settings is not available in this environment
    class _Simple:
        class _Features:
            webapp_security = True
        features = _Features()
        class _Web:
            allowed_origin = "*"
            csp_allowed_origin = "*"
        web = _Web()
    settings = _Simple()  # type: ignore

from .routes_auth import router as auth_router

# Middleware to add CSP header to responses
class CSPMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        try:
            csp_origin = getattr(getattr(settings, 'web', None), 'csp_allowed_origin', None) or getattr(settings, 'CSP_ALLOWED_ORIGIN', None)
            if csp_origin:
                # Minimal CSP allowing our origin and inline for Telegram WebApp wrapper context if needed
                response.headers["Content-Security-Policy"] = f"default-src 'self' {csp_origin}; script-src 'self' {csp_origin} 'unsafe-inline'; connect-src 'self' {csp_origin}; style-src 'self' {csp_origin} 'unsafe-inline'; img-src 'self' data: {csp_origin}; frame-ancestors 'self' https://web.telegram.org https://telegram.org;"
        except Exception:
            pass
        return response

app = FastAPI(title="KARMABOT1 WebApp API")

# CORS
try:
    allowed_origin = getattr(getattr(settings, 'web', None), 'allowed_origin', None) or getattr(settings, 'WEBAPP_ALLOWED_ORIGIN', None)
    if allowed_origin:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[allowed_origin],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
except Exception:
    pass

# CSP
app.add_middleware(CSPMiddleware)

# Routers
app.include_router(auth_router, prefix="/auth", tags=["auth"]) 

@app.get("/health")
async def health():
    return {"status": "ok"}
