from typing import Optional, Dict, Any
import time
import os
import logging

from fastapi import APIRouter, HTTPException, Header

logger = logging.getLogger(__name__)
from pydantic import BaseModel

# Reuse existing JWT verification used by /auth endpoints
from core.services.webapp_auth import check_jwt
from core.security.jwt_service import verify_partner
from core.services.cache import cache_service
from core.services.loyalty_points import loyalty_service

router = APIRouter()


class ActivityClaimRequest(BaseModel):
    rule_code: str
    lat: Optional[float] = None
    lng: Optional[float] = None
    listing_id: Optional[int] = None


class ActivityClaimResponse(BaseModel):
    ok: bool
    points_awarded: int = 0
    code: Optional[str] = None  # cooldown_active | rule_disabled | geo_required | out_of_coverage


# Cooldown is stored via cache_service (Redis or in-memory fallback)

# Defaults (can be tuned via env)
_DEFAULT_POINTS = {
    "checkin": int(os.getenv("ACTIVITY_CHECKIN_POINTS", "5")),
    "profile": int(os.getenv("ACTIVITY_PROFILE_POINTS", "20")),
    "bindcard": int(os.getenv("ACTIVITY_BINDCARD_POINTS", "30")),
    "geocheckin": int(os.getenv("ACTIVITY_GEO_POINTS", "10")),
}
_DEFAULT_COOLDOWN = {
    "checkin": int(os.getenv("ACTIVITY_CHECKIN_COOLDOWN_SEC", "86400")),
    # one-time style activities: use huge cooldown to simulate one-off for now
    "profile": int(os.getenv("ACTIVITY_PROFILE_COOLDOWN_SEC", str(365*24*3600))),
    "bindcard": int(os.getenv("ACTIVITY_BINDCARD_COOLDOWN_SEC", str(365*24*3600))),
    "geocheckin": int(os.getenv("ACTIVITY_GEO_COOLDOWN_SEC", "86400")),
}


def _extract_user_id_from_bearer(authorization: Optional[str]) -> Optional[int]:
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    token = authorization.split(" ", 1)[1]
    claims = check_jwt(token)
    if not claims:
        partner_claims = verify_partner(token)
        claims = partner_claims
    if not claims:
        return None
    try:
        return int(claims.get("sub"))
    except Exception:
        return None


@router.post("/activity/claim", response_model=ActivityClaimResponse)
async def activity_claim(payload: ActivityClaimRequest, authorization: Optional[str] = Header(default=None)):
    # Feature flag (fail-open by default)
    enabled = str(os.getenv("ACTIVITY_ENABLED", "true")).strip().lower() in ("1", "true", "yes", "on")
    if not enabled:
        return ActivityClaimResponse(ok=False, code="rule_disabled")

    # Validate rule
    rule = (payload.rule_code or "").strip().lower()
    if rule not in ("checkin", "profile", "bindcard", "geocheckin"):
        raise HTTPException(status_code=400, detail="invalid rule_code")

    # Extract user id
    user_id = _extract_user_id_from_bearer(authorization)
    if not user_id:
        raise HTTPException(status_code=401, detail="missing/invalid token")

    # Geo-required check (minimal placeholder; real PostGIS not wired yet)
    if rule == "geocheckin":
        if payload.lat is None or payload.lng is None:
            return ActivityClaimResponse(ok=False, code="geo_required")
        # TODO: real coverage polygon check; for now accept always
        # Mockable branch for tests: allow forcing "out_of_coverage" with (0,0) when env enabled
        try:
            mock_out = str(os.getenv("ACTIVITY_GEO_MOCK_OUT", "false")).strip().lower() in ("1", "true", "yes", "on")
        except Exception:
            mock_out = False
        if mock_out:
            try:
                if abs(float(payload.lat)) < 1e-6 and abs(float(payload.lng)) < 1e-6:
                    return ActivityClaimResponse(ok=False, code="out_of_coverage")
            except Exception:
                pass

    now = time.time()
    cooldown = int(_DEFAULT_COOLDOWN.get(rule, 86400))
    cd_key = f"actv:cd:{user_id}:{rule}"
    # If key exists → on cooldown
    try:
        existing = await cache_service.get(cd_key)
    except Exception:
        existing = None
    if existing:
        return ActivityClaimResponse(ok=False, code="cooldown_active")

    # Set cooldown key with TTL
    try:
        await cache_service.set(cd_key, "1", ex=cooldown)
    except Exception:
        # fail-open: do nothing
        pass

    # Начисляем баллы через сервис
    points = int(_DEFAULT_POINTS.get(rule, 0))
    try:
        result = await loyalty_service.add_transaction(
            user_id=user_id,
            rule_code=rule,
            points=points,
            metadata={
                "lat": payload.lat,
                "lng": payload.lng,
                "listing_id": payload.listing_id,
                "source": "activity_claim"
            }
        )
        return ActivityClaimResponse(ok=True, points_awarded=points)
        
    except ValueError as e:
        logger.error(f"Invalid loyalty transaction: {e}", extra={"user_id": user_id, "rule": rule})
        return ActivityClaimResponse(ok=False, code="invalid_operation")
        
    except Exception as e:
        logger.error(
            "Failed to process loyalty transaction",
            extra={"user_id": user_id, "rule": rule, "error": str(e)}
        )
        return ActivityClaimResponse(ok=False, code="internal_error")
