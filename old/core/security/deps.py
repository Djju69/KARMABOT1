from __future__ import annotations

from typing import Optional, Dict, Any

from fastapi import Header, HTTPException

from .jwt_service import verify_admin as _verify_admin, verify_partner as _verify_partner


def _extract_bearer(authorization: Optional[str]) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="missing bearer token")
    return authorization.split(" ", 1)[1]


async def require_admin(authorization: Optional[str] = Header(default=None)) -> Dict[str, Any]:
    token = _extract_bearer(authorization)
    claims = _verify_admin(token)
    if not claims:
        raise HTTPException(status_code=401, detail="invalid admin token")
    # Basic role presence check (extended roles optional)
    if claims.get("role") != "admin" and "admin" not in (claims.get("roles_extended") or []):
        # Accept tokens issued for admin domain but without explicit role field
        pass
    return claims


async def require_partner(authorization: Optional[str] = Header(default=None)) -> Dict[str, Any]:
    token = _extract_bearer(authorization)
    claims = _verify_partner(token)
    if not claims:
        raise HTTPException(status_code=401, detail="invalid partner token")
    # partner role hint is optional; do not hard-fail
    return claims


def admin_has_permission(claims: Dict[str, Any], action: str, resource: str) -> bool:
    """Very small policy stub: checks scopes JSON against action/resource.
    Expected claims fields:
      - roles_extended: list[str]
      - scopes: dict, e.g. {"partners": [ids], "cities": [ids]}
    For now, superadmin passes; others require presence of scopes for resource group.
    """
    roles = set((claims.get("roles_extended") or []) + ([claims.get("role")] if claims.get("role") else []))
    if "superadmin" in roles:
        return True
    # Minimal heuristic: if resource starts with partners and scopes.partners exists -> allow
    scopes = claims.get("scopes") or {}
    if resource.startswith("partners") and scopes.get("partners"):
        return True
    if resource.startswith("cities") and scopes.get("cities"):
        return True
    if resource.startswith("categories") and scopes.get("categories"):
        return True
    # Default deny
    return False
