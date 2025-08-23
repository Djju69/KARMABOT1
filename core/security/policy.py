from __future__ import annotations

from typing import Dict, Any

# Action constants (examples)
PARTNERS_CRUD = "partners:crud"
ADMINS_CRUD = "admins:crud"
MODERATION_ANY = "moderation:*"
LISTINGS_UPDATE = "listings:update"
SQL_MIGRATE = "sql:migrate"
SQL_CHECK = "sql:check"


def can(claims: Dict[str, Any], action: str, resource: str) -> bool:
    """Simple policy evaluator.
    - Superadmin always allowed.
    - Otherwise check scopes based on resource prefix.
    """
    roles = set((claims.get("roles_extended") or []) + ([claims.get("role")] if claims.get("role") else []))
    if "superadmin" in roles:
        return True

    scopes = claims.get("scopes") or {}
    # partners resources
    if resource.startswith("partners"):
        return bool(scopes.get("partners"))
    if resource.startswith("cities"):
        return bool(scopes.get("cities"))
    if resource.startswith("categories"):
        return bool(scopes.get("categories"))
    # fallback deny
    return False
