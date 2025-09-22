"""
Card service: secure user card binding with uid hashing and minimal checks.
"""
from __future__ import annotations

import os
import hashlib
from dataclasses import dataclass
from typing import Optional, Tuple

from ..database.db_v2 import db_v2


@dataclass
class BindResult:
    ok: bool
    reason: Optional[str] = None  # 'blocked' | 'taken' | 'invalid'
    last4: Optional[str] = None


def _uid_hash(uid: str, salt: Optional[str] = None) -> str:
    s = salt or os.getenv("CARD_UID_SALT", "demo-salt-please-change")
    h = hashlib.sha256()
    h.update((uid + ":" + s).encode("utf-8"))
    return h.hexdigest()


class CardService:
    def __init__(self) -> None:
        pass

    def bind_card(self, user_id: int, uid: str) -> BindResult:
        # Basic format check (12 digits enforced at handler level but double-check here)
        if not uid.isdigit() or len(uid) != 12:
            return BindResult(ok=False, reason="invalid")
        last4 = uid[-4:]
        uid_hash = _uid_hash(uid)
        with db_v2.get_connection() as conn:
            # Blocked check
            row = conn.execute(
                "SELECT is_blocked FROM user_cards WHERE uid_hash = ?",
                (uid_hash,),
            ).fetchone()
            if row:
                if int(row[0]) == 1:
                    return BindResult(ok=False, reason="blocked")
                # Already exists (bound to someone)
                return BindResult(ok=False, reason="taken")
            # Insert new
            conn.execute(
                "INSERT INTO user_cards (user_id, uid_hash, last4, is_blocked) VALUES (?, ?, ?, 0)",
                (user_id, uid_hash, last4),
            )
            return BindResult(ok=True, last4=last4)


card_service = CardService()
