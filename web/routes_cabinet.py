from typing import Optional, List, Dict, Any
import os

from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel

from core.services.webapp_auth import check_jwt
from core.security.jwt_service import verify_partner
from core.settings import settings
from core.services.partners import is_partner

router = APIRouter()


class Profile(BaseModel):
    user_id: int
    lang: str
    source: str = "tg_webapp"
    role: str = "user"  # user | partner


class OrderItem(BaseModel):
    id: str
    title: str
    status: str


class OrdersResponse(BaseModel):
    items: List[OrderItem]


def get_current_claims(authorization: Optional[str] = Header(default=None)) -> Dict[str, Any]:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="missing bearer token")
    token = authorization.split(" ", 1)[1]

    allow_partner = os.getenv("ALLOW_PARTNER_FOR_CABINET") == "1"

    # 1) Try WebApp token (JWT_SECRET domain)
    claims = check_jwt(token)
    if claims:
        # Require WebApp source unless in development
        src = str(claims.get("src", ""))
        if src != "tg_webapp" and settings.environment != "development":
            # If flagged, attempt partner verification as fallback
            if allow_partner:
                partner_claims = verify_partner(token)
                if partner_claims:
                    return partner_claims
            raise HTTPException(status_code=401, detail="invalid token source")
        return claims

    # 2) Fallback: allow partner tokens if enabled
    if allow_partner:
        partner_claims = verify_partner(token)
        if partner_claims:
            return partner_claims

    # Otherwise invalid
    raise HTTPException(status_code=401, detail="invalid token")


@router.get("/profile", response_model=Profile)
async def profile(claims: Dict[str, Any] = Depends(get_current_claims)):
    # Minimal read-only profile from JWT claims and defaults
    try:
        user_id = int(claims.get("sub"))
    except Exception:
        raise HTTPException(status_code=400, detail="invalid sub in token")
    # Language could be taken from DB/profile service later; return default for MVP
    lang = settings.default_lang or "ru"
    # Determine role:
    # 1) Partner JWTs usually carry role=partner
    role = str(claims.get("role") or "").lower()
    if role != "partner":
        # 2) For WebApp users, auto-switch to partner if they have a partner card (MVP via ENV allowlist)
        try:
            if await is_partner(user_id):
                role = "partner"
            else:
                role = "user"
        except Exception:
            role = "user"
    return Profile(user_id=user_id, lang=lang, source=str(claims.get("src", "")), role=role)


@router.get("/orders", response_model=OrdersResponse)
async def orders(limit: int = 10, claims: Dict[str, Any] = Depends(get_current_claims)):
    # MVP: return empty or mock list until DB integration is finalized
    _ = claims  # reserved for future filtering by user_id
    limit = max(1, min(limit, 50))
    items: List[OrderItem] = []
    # Example mock (commented). Uncomment if you want visible demo data.
    # items = [
    #     OrderItem(id="ord_1", title="Демонстрационный заказ", status="completed"),
    # ]
    return OrdersResponse(items=items[:limit])
