import base64
import hmac
import hashlib
import json
import logging
import time
from typing import Dict, Any, Optional
from urllib.parse import parse_qsl, unquote

try:
    import jwt  # pyjwt
except Exception:
    jwt = None  # optional dependency

from ..settings import settings
from ..utils.telemetry import log_event

logger = logging.getLogger(__name__)


def verify_init_data(init_data: str) -> bool:
    """Verify Telegram WebApp initData according to TG spec.
    https://core.telegram.org/bots/webapps#validating-data-received-via-the-web-app
    Steps:
    - Parse query string to dict
    - Build data_check_string from sorted key=value pairs excluding 'hash'
    - secret_key = HMAC_SHA256(key="WebAppData", data=BOT_TOKEN)
    - calc_hash = HMAC_SHA256(key=secret_key, data=data_check_string)
    - Compare to provided 'hash' (hex)
    - Check auth_date is within settings.auth_window_sec
    """
    try:
        if not init_data:
            return False
        # Parse query string safely
        pairs = dict(parse_qsl(init_data, keep_blank_values=True))
        provided_hash = pairs.pop("hash", None)
        if not provided_hash:
            logger.warning("WebApp initData missing hash")
            try:
                # fire-and-forget telemetry
                import asyncio; asyncio.create_task(log_event("webapp_invalid_auth", reason="missing_hash"))
            except Exception:
                pass
            return False
        # Build data_check_string from sorted keys
        items = []
        for k in sorted(pairs.keys()):
            items.append(f"{k}={pairs[k]}")
        data_check_string = "\n".join(items)

        # Compute secret key and HMAC
        bot_token = settings.bots.bot_token
        secret_key = hmac.new("WebAppData".encode(), bot_token.encode(), hashlib.sha256).digest()
        calc_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        if calc_hash != provided_hash:
            logger.warning("WebApp initData hash mismatch")
            try:
                import asyncio; asyncio.create_task(log_event("webapp_invalid_auth", reason="hash_mismatch"))
            except Exception:
                pass
            return False

        # Anti-replay window
        auth_date_str = pairs.get("auth_date")
        if not auth_date_str:
            logger.warning("WebApp initData missing auth_date")
            try:
                import asyncio; asyncio.create_task(log_event("webapp_invalid_auth", reason="missing_auth_date"))
            except Exception:
                pass
            return False
        try:
            auth_date = int(auth_date_str)
        except Exception:
            logger.warning("WebApp initData invalid auth_date")
            try:
                import asyncio; asyncio.create_task(log_event("webapp_invalid_auth", reason="invalid_auth_date"))
            except Exception:
                pass
            return False
        if abs(int(time.time()) - auth_date) > settings.auth_window_sec:
            logger.warning("WebApp initData expired window")
            try:
                import asyncio; asyncio.create_task(log_event("webapp_invalid_auth", reason="expired"))
            except Exception:
                pass
            return False
        return True
    except Exception as e:
        logger.warning(f"verify_init_data error: {e}")
        try:
            import asyncio; asyncio.create_task(log_event("webapp_invalid_auth", reason="exception", error=str(e)))
        except Exception:
            pass
        return False


def issue_jwt(user_id: int, extra: Optional[Dict[str, Any]] = None, ttl_sec: int = 300) -> str:
    """Issue short-lived JWT for WebApp calls. Non-breaking: returns unsigned debug token if JWT_SECRET empty."""
    now = int(time.time())
    payload = {"sub": str(user_id), "iat": now, "exp": now + ttl_sec, "nonce": hashlib.sha256(f"{user_id}:{now}".encode()).hexdigest()}
    if extra:
        payload.update(extra)
    secret = settings.jwt_secret
    if not jwt:
        logger.warning("pyjwt not installed; returning JSON payload as debug token (development only)")
        return json.dumps(payload)
    if not secret:
        token = jwt.encode(payload, key="debug", algorithm="HS256")
        logger.warning("JWT_SECRET empty: using debug signing (development only)")
        return token
    return jwt.encode(payload, key=secret, algorithm="HS256")


def check_jwt(token: str) -> Optional[Dict[str, Any]]:
    try:
        if not jwt:
            # If pyjwt missing, accept JSON tokens from issue_jwt fallback
            return json.loads(token)
        data = jwt.decode(token, key=(settings.jwt_secret or "debug"), algorithms=["HS256"])
        return data
    except Exception as e:
        logger.warning(f"check_jwt failed: {e}")
        try:
            import asyncio; asyncio.create_task(log_event("webapp_invalid_auth", reason="invalid_jwt", error=str(e)))
        except Exception:
            pass
        return None


def build_cors_headers() -> Dict[str, str]:
    """Return minimal CORS headers based on settings. Caller should attach to HTTP responses."""
    headers = {
        "Access-Control-Allow-Origin": settings.webapp_allowed_origin or "",
        "Vary": "Origin",
        "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
        "Access-Control-Allow-Headers": "Authorization,Content-Type",
    }
    return {k: v for k, v in headers.items() if v}


def build_csp_header() -> str:
    """Return CSP header string based on settings (restrict framing and connections)."""
    frame_ancestors = "https://web.telegram.org https://web.telegram.org/* https://*.telegram.org"
    connect_src = settings.csp_allowed_origin or "'self'"
    directives = [
        f"default-src 'none'",
        f"frame-ancestors {frame_ancestors}",
        f"connect-src {connect_src}",
        f"img-src 'self' data:",
        f"style-src 'self' 'unsafe-inline'",
        f"script-src 'self' 'unsafe-inline' 'unsafe-eval'",
    ]
    return "; ".join(directives)
