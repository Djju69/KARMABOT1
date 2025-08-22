from __future__ import annotations

import os
from typing import Set


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


def is_partner(user_id: int) -> bool:
    """MVP: Determine if a TG user is a partner via ENV allowlist.

    Reads comma-separated user IDs from PARTNER_USER_IDS, e.g. "1,2,3".
    Later this will be replaced by a DB-backed check (presence of a partner card).
    """
    allowlist = _parse_ids(os.getenv("PARTNER_USER_IDS"))
    return user_id in allowlist
