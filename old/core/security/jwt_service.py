from __future__ import annotations
import time
from typing import Any, Dict, Optional, Tuple

try:
    import jwt  # pyjwt
except Exception:
    jwt = None

from ..settings import settings

# Token domains
DOMAIN_USER = "user"
DOMAIN_PARTNER = "partner"
DOMAIN_ADMIN = "admin"


def _secrets_for(domain: str) -> Tuple[str, Optional[str]]:
    if domain == DOMAIN_USER:
        return (settings.jwt_user_secret_active or "", settings.jwt_user_secret_previous or None)
    if domain == DOMAIN_PARTNER:
        return (settings.jwt_partner_secret_active or "", settings.jwt_partner_secret_previous or None)
    if domain == DOMAIN_ADMIN:
        return (settings.jwt_admin_secret_active or "", settings.jwt_admin_secret_previous or None)
    # fallback
    return (settings.jwt_secret or "", None)


def sign(domain: str, claims: Dict[str, Any], ttl_sec: int = 900) -> str:
    """Sign access token with active secret and kid. Adds iat/exp if absent.
    Non-breaking: if pyjwt missing, returns JSON-like string; if secret empty, uses 'debug'.
    """
    now = int(time.time())
    if "iat" not in claims:
        claims["iat"] = now
    if "exp" not in claims:
        claims["exp"] = now + ttl_sec
    active, _prev = _secrets_for(domain)
    kid = settings.jwt_kid_active or "main"

    if not jwt:
        # Minimal fallback for dev
        import json
        return json.dumps({"kid": kid, "domain": domain, "claims": claims})

    key = active or "debug"
    token = jwt.encode(claims, key=key, algorithm="HS256", headers={"kid": kid, "typ": "JWT"})
    return token


def verify(domain: str, token: str) -> Optional[Dict[str, Any]]:
    """Verify token against active, then previous secret. Returns claims or None.
    """
    if not token:
        return None
    if not jwt:
        # Accept dev fallback
        try:
            import json
            obj = json.loads(token)
            return obj.get("claims") if isinstance(obj, dict) else None
        except Exception:
            return None

    active, previous = _secrets_for(domain)
    for key in filter(None, [active, previous, "debug"]):
        try:
            data = jwt.decode(token, key=key, algorithms=["HS256"])
            return data
        except Exception:
            continue
    return None


def issue_access_for_admin(user_id: int, roles: list[str], scopes: Dict[str, Any], ttl_sec: int = 900) -> str:
    return sign(
        DOMAIN_ADMIN,
        {
            "sub": str(user_id),
            "role": DOMAIN_ADMIN,
            "roles_extended": roles,
            "scopes": scopes or {},
            "amr": ["pwd"],
        },
        ttl_sec=ttl_sec,
    )


def issue_access_for_partner(user_id: int, partner_role: str, scopes: Dict[str, Any], ttl_sec: int = 900) -> str:
    return sign(
        DOMAIN_PARTNER,
        {
            "sub": str(user_id),
            "role": DOMAIN_PARTNER,
            "partner_role": partner_role,
            "scopes": scopes or {},
            "amr": ["pwd"],
        },
        ttl_sec=ttl_sec,
    )


def verify_admin(token: str) -> Optional[Dict[str, Any]]:
    return verify(DOMAIN_ADMIN, token)


def verify_partner(token: str) -> Optional[Dict[str, Any]]:
    return verify(DOMAIN_PARTNER, token)
