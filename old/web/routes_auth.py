from typing import Optional, Dict, Any, List
from urllib.parse import parse_qsl
import os
import json
import time
import asyncio

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel

from core.services.webapp_auth import (
    verify_init_data,
    verify_init_data_with_reason,
    issue_jwt,
    check_jwt,
)
from core.settings import settings
from core.security.jwt_service import verify_partner
from core.services.partners import is_partner
from core.services.cache import get_cache_service
from core.utils.metrics import (
    AUTHME_REQUESTS,
    AUTHME_BUILD_LATENCY,
    AUTHME_AGE,
)

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
    ok, reason = verify_init_data_with_reason(payload.initData)
    if not ok:
        # Provide detailed reason to logs/clients for diagnostics (no secrets exposed)
        raise HTTPException(status_code=401, detail=f"invalid initData: {reason}")

    user_id = _extract_user_id(payload.initData)
    if not user_id:
        raise HTTPException(status_code=400, detail="user id not found in initData")

    token = issue_jwt(user_id, extra={"src": "tg_webapp"})
    return TokenResponse(token=token)


def _authme_ttls():
    ttl = int(os.getenv("AUTHME_CACHE_TTL_SEC", "8") or 8)
    soft = int(os.getenv("AUTHME_CACHE_SOFT_TTL_SEC", str(max(1, ttl // 2))))
    return ttl, soft


async def _build_authme_payload(user_id: int, source: Optional[str], claims: Dict[str, Any]):
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
    partner_can_scan_qr = bool(has_partner)
    listings_counts: Dict[str, int] = {"draft": 0, "pending": 0, "published": 0, "archived": 0}
    has_listings = False

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
            "tiers": {"loyalty": "silver"},
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
            "listings_counts": listings_counts if has_partner else None,
            "has_listings": has_listings if has_partner else None,
            "can_scan_qr": partner_can_scan_qr,
        },
        "capabilities": capabilities,
        "build": {
            "kid": os.getenv("JWT_KEY_ID", "default"),
            "trace_id": None,
        },
        "ok": True,
        "claims": claims,
        "source": source or claims.get("src"),
    }
    return resp


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

    ttl, soft_ttl = _authme_ttls()
    key = f"authme:{user_id}"
    now = int(time.time())

    cached = await cache_service.get(key)
    if cached:
        try:
            obj = json.loads(cached)
            payload = obj.get("payload")
            ts = int(obj.get("ts", now))
            age = max(0, now - ts)
            AUTHME_AGE.observe(age)
            if age >= soft_ttl:
                AUTHME_REQUESTS.labels("stale_rebuild").inc()
                # background refresh
                async def _refresh():
                    start = time.monotonic()
                    new_payload = await _build_authme_payload(user_id, source, claims)
                    AUTHME_BUILD_LATENCY.observe(max(0.0, time.monotonic() - start))
                    try:
                        await cache_service.set(key, json.dumps({"ts": int(time.time()), "payload": new_payload}), ttl)
                    except Exception:
                        pass
                asyncio.create_task(_refresh())
            else:
                AUTHME_REQUESTS.labels("hit").inc()
            if payload:
                return payload
        except Exception:
            # fallthrough to miss
            pass

    # miss
    AUTHME_REQUESTS.labels("miss").inc()
    start = time.monotonic()
    payload = await _build_authme_payload(user_id, source, claims)
    AUTHME_BUILD_LATENCY.observe(max(0.0, time.monotonic() - start))
    try:
        await cache_service.set(key, json.dumps({"ts": now, "payload": payload}), ttl)
    except Exception:
        pass
    return payload


# Dev-only helper to mint a JWT without Telegram initData
if os.getenv("ENVIRONMENT") == "development" or os.getenv("FASTAPI_ONLY") == "1":
    @router.get("/debug-token", response_model=TokenResponse)
    async def debug_token(user_id: int = 1):
        token = issue_jwt(user_id, extra={"src": "debug"})
        return TokenResponse(token=token)
