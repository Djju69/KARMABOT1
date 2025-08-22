from typing import Optional, List, Dict, Any

from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel

from core.services.webapp_auth import check_jwt
from core.settings import settings

router = APIRouter()


class Profile(BaseModel):
    user_id: int
    lang: str
    source: str = "tg_webapp"


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
    claims = check_jwt(token)
    if not claims:
        raise HTTPException(status_code=401, detail="invalid token")
    # Require WebApp token by default; allow debug in development/FASTAPI_ONLY
    src = str(claims.get("src", ""))
    if src != "tg_webapp":
        if not (settings.environment == "development"):
            raise HTTPException(status_code=401, detail="invalid token source")
    return claims


@router.get("/profile", response_model=Profile)
async def profile(claims: Dict[str, Any] = Depends(get_current_claims)):
    # Minimal read-only profile from JWT claims and defaults
    try:
        user_id = int(claims.get("sub"))
    except Exception:
        raise HTTPException(status_code=400, detail="invalid sub in token")
    # Language could be taken from DB/profile service later; return default for MVP
    lang = settings.default_lang or "ru"
    return Profile(user_id=user_id, lang=lang, source=str(claims.get("src", "")))


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
