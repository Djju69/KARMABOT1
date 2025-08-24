from typing import Optional, Dict, Any
import time
import hashlib

from fastapi import APIRouter, HTTPException, Header, Response, Request
from pydantic import BaseModel, EmailStr

from core.settings import settings
from core.security.jwt_service import (
    issue_access_for_partner,
    verify_partner,
)

router = APIRouter()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 0


def _hash_password(password: str) -> str:
    pepper = settings.partner_login_pepper or ""
    data = (password + pepper).encode()
    return hashlib.sha256(data).hexdigest()


def _make_refresh_token(user_id: int, ttl: int) -> str:
    # For MVP: refresh token is also a JWT signed with partner secret but marked as type=refresh
    now = int(time.time())
    exp = now + ttl
    from core.security.jwt_service import sign, DOMAIN_PARTNER
    return sign(DOMAIN_PARTNER, {"sub": str(user_id), "type": "refresh", "iat": now, "exp": exp}, ttl_sec=ttl)


def _verify_refresh(token: str) -> Optional[Dict[str, Any]]:
    data = verify_partner(token)
    if not data or data.get("type") != "refresh":
        return None
    return data


def _set_refresh_cookie(resp: Response, token: str):
    params = {
        "key": "refresh_token",
        "value": token,
        "httponly": True,
        "secure": bool(settings.cookie_secure),
        "samesite": settings.cookie_samesite or "Lax",
        "path": "/auth",
    }
    if settings.cookie_domain:
        params["domain"] = settings.cookie_domain
    resp.set_cookie(**params)


def _clear_refresh_cookie(resp: Response):
    params = {
        "key": "refresh_token",
        "value": "",
        "httponly": True,
        "secure": bool(settings.cookie_secure),
        "samesite": settings.cookie_samesite or "Lax",
        "path": "/auth",
        "max_age": 0,
    }
    if settings.cookie_domain:
        params["domain"] = settings.cookie_domain
    resp.set_cookie(**params)


@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest, response: Response):
    # MVP without DB: single partner credential via env
    if not settings.partner_login_email or not settings.partner_login_password_sha256:
        raise HTTPException(status_code=503, detail="login not configured")

    email_ok = payload.email.lower() == settings.partner_login_email.lower()
    pass_hash = _hash_password(payload.password)
    pass_ok = pass_hash == settings.partner_login_password_sha256
    if not (email_ok and pass_ok):
        raise HTTPException(status_code=401, detail="invalid_credentials")

    # For MVP use user_id=1; later bind to DB record
    user_id = 1
    access_ttl = int(settings.access_ttl_sec or 900)
    refresh_ttl = int(settings.refresh_ttl_sec or 1209600)

    access_token = issue_access_for_partner(user_id, partner_role="owner", scopes={})
    refresh_token = _make_refresh_token(user_id, refresh_ttl)

    _set_refresh_cookie(response, refresh_token)
    return LoginResponse(access_token=access_token, expires_in=access_ttl)


@router.post("/refresh", response_model=LoginResponse)
async def refresh(request: Request, response: Response, x_csrf_token: Optional[str] = Header(default=None)):
    # Optional CSRF check: if CSRF_SECRET is set, require header match of static secret (MVP)
    if settings.csrf_secret:
        if not x_csrf_token or x_csrf_token != settings.csrf_secret:
            raise HTTPException(status_code=403, detail="csrf_failed")

    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="no_refresh")
    data = _verify_refresh(refresh_token)
    if not data:
        raise HTTPException(status_code=401, detail="invalid_refresh")

    user_id = int(data.get("sub"))
    access_ttl = int(settings.access_ttl_sec or 900)
    refresh_ttl = int(settings.refresh_ttl_sec or 1209600)

    access_token = issue_access_for_partner(user_id, partner_role="owner", scopes={})
    # Rotate refresh (MVP rotation)
    new_refresh = _make_refresh_token(user_id, refresh_ttl)
    _set_refresh_cookie(response, new_refresh)

    return LoginResponse(access_token=access_token, expires_in=access_ttl)


@router.post("/logout")
async def logout(response: Response):
    # MVP: client-side invalidate. If we add session store later, revoke here.
    _clear_refresh_cookie(response)
    return {"ok": True}
