from typing import Optional, Dict, Any, List
from urllib.parse import parse_qsl
import os

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel

from core.services.webapp_auth import (
    verify_init_data,
    issue_jwt,
    check_jwt,
)
from core.settings import settings
from core.security.jwt_service import verify_partner
from core.services.partners import is_partner

router = APIRouter()


class WebAppAuthRequest(BaseModel):
    initData: str


class TokenResponse(BaseModel):
    token: str


def _extract_user_id(init_data: str) -> Optional[int]:
    try:
        pairs = dict(parse_qsl(init_data, keep_blank_values=True))
        raw_user = pairs.get("user")
        if not raw_user:
            return None
        import json
        user_obj = json.loads(raw_user)
        uid = user_obj.get("id")
        if isinstance(uid, int):
            return uid
        try:
            return int(uid)
        except Exception:
            return None
    except Exception:
        return None


@router.post("/webapp", response_model=TokenResponse)
async def auth_webapp(payload: WebAppAuthRequest):
    # Validate Telegram initData signature and freshness
    if not verify_init_data(payload.initData):
        raise HTTPException(status_code=401, detail="invalid initData")

    user_id = _extract_user_id(payload.initData)
    if not user_id:
        raise HTTPException(status_code=400, detail="user id not found in initData")

    token = issue_jwt(user_id, extra={"src": "tg_webapp"})
    return TokenResponse(token=token)


@router.get("/me")
async def me(authorization: Optional[str] = Header(default=None)):
    """Unified identity endpoint with role fallback and enriched payload.

    Priority: admin > partner > user, with special-case "blocked" if ever supported.
    Accepts both WebApp JWT (primary) and partner-domain JWT (fallback).
    """
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="missing bearer token")
    token = authorization.split(" ", 1)[1]

    # 1) Try WebApp JWT
    claims: Optional[Dict[str, Any]] = check_jwt(token)
    source = (claims or {}).get("src") if claims else None

    # 2) Fallback to partner token if enabled and webapp-jwt not valid
    if not claims:
        partner_claims = verify_partner(token)
        if partner_claims:
            claims = partner_claims
            source = (partner_claims or {}).get("src", "partner")

    if not claims:
        raise HTTPException(status_code=401, detail="invalid token")

    # Extract user id
    try:
        user_id = int(claims.get("sub"))
    except Exception:
        raise HTTPException(status_code=400, detail="invalid sub in token")

    # Blocked flag – we don't have a users table yet; default False
    blocked = False

    # Admin context – not implemented; placeholder flags
    has_admin = False
    admin_roles: List[str] = []
    admin_scopes: Dict[str, Any] = {}
    is_impersonating = False
    impersonated_by = None

    # Partner context – check via DB helper
    has_partner = await is_partner(user_id)
    partner_profile_id = None  # unknown in current schema
    # Minimal capability: allow QR scan when partner is active in DB
    partner_can_scan_qr = bool(has_partner)

    # Determine effective role
    if blocked:
        effective_role = "blocked"
    elif has_admin:
        effective_role = "admin"
    elif has_partner:
        effective_role = "partner"
    else:
        effective_role = "user"

    roles: List[str] = ["user"]
    if has_partner:
        roles.append("partner")
    if has_admin:
        roles.append("admin")

    # Capabilities
    capabilities: List[str] = [
        "cabinet:view",
    ]
    if partner_can_scan_qr:
        capabilities.append("qr:scan")

    resp = {
        "user": {
            "id": user_id,
            "lang": "ru",
            "tz": os.getenv("DEFAULT_TZ", "UTC"),
            "blocked": blocked,
            "tiers": {"loyalty": "silver"},  # placeholder
        },
        "effective_role": effective_role,
        "roles": roles,
        "admin": {
            "has_admin": has_admin,
            "roles": admin_roles,
            "scopes": admin_scopes,
            "is_impersonating": is_impersonating,
            "impersonated_by": impersonated_by,
        },
        "partner": {
            "has_partner": has_partner,
            "partner_profile_id": partner_profile_id,
            "listings_counts": None,
            "has_listings": None,
            "can_scan_qr": partner_can_scan_qr,
        },
        "capabilities": capabilities,
        "build": {
            "kid": os.getenv("JWT_KEY_ID", "default"),
            "trace_id": None,
        },
        "ok": True,
        "claims": claims,  # keep for debugging/compatibility
        "source": source or claims.get("src"),
    }
    return resp


# Dev-only helper to mint a JWT without Telegram initData
if settings.environment == "development" or os.getenv("FASTAPI_ONLY") == "1":
    @router.get("/debug-token", response_model=TokenResponse)
    async def debug_token(user_id: int = 1):
        token = issue_jwt(user_id, extra={"src": "debug"})
        return TokenResponse(token=token)
