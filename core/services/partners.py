from __future__ import annotations

import os
from typing import Set, Optional

import asyncio
import asyncpg


_pool: Optional[asyncpg.Pool] = None


def _parse_ids(env_value: str | None) -> Set[int]:
    if not env_value:
        return set()
    ids: Set[int] = set()
    for part in env_value.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            ids.add(int(part))
        except ValueError:
            # ignore malformed entries
            continue
    return ids


async def _get_pool() -> Optional[asyncpg.Pool]:
    global _pool
    if _pool is not None:
        return _pool
    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        return None
    # Create pool lazily; allow failures to bubble up gracefully
    _pool = await asyncpg.create_pool(dsn, min_size=0, max_size=5)
    return _pool


async def is_partner(user_id: int) -> bool:
    """Determine if user is a partner.

    Order of checks:
    1) ENV allowlist PARTNER_USER_IDS for quick overrides/MVP.
    2) Postgres lookup in partner_cards by tg_user_id.
    """
    # 1) ENV allowlist
    allowlist = _parse_ids(os.getenv("PARTNER_USER_IDS"))
    if user_id in allowlist:
        return True

    # 2) DB lookup
    try:
        pool = await _get_pool()
        if pool is None:
            return False
        async with pool.acquire() as conn:
            # Prefer query excluding archived rows; if archived_at column doesn't exist yet, fallback
            try:
                row = await conn.fetchrow(
                    """
                    SELECT 1
                    FROM partner_cards
                    WHERE tg_user_id = $1
                      AND status IN ('pending','approved','published')
                      AND (archived_at IS NULL)
                    LIMIT 1
                    """,
                    user_id,
                )
            except Exception:
                # Column archived_at may not exist on older schema — fallback without the predicate
                row = await conn.fetchrow(
                    """
                    SELECT 1
                    FROM partner_cards
                    WHERE tg_user_id = $1
                      AND status IN ('pending','approved','published')
                    LIMIT 1
                    """,
                    user_id,
                )
            return row is not None
    except Exception:
        # If table doesn't exist or DB unreachable, fail closed (False)
        return False
