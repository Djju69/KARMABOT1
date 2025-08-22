from typing import Optional
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
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="missing bearer token")
    token = authorization.split(" ", 1)[1]
    data = check_jwt(token)
    if not data:
        raise HTTPException(status_code=401, detail="invalid token")
    return {"ok": True, "claims": data}


# Dev-only helper to mint a JWT without Telegram initData
if settings.environment == "development" or os.getenv("FASTAPI_ONLY") == "1":
    @router.get("/debug-token", response_model=TokenResponse)
    async def debug_token(user_id: int = 1):
        token = issue_jwt(user_id, extra={"src": "debug"})
        return TokenResponse(token=token)
