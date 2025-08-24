"""
Loyalty service: wallets, transactions, spend intents (SQLite via db_v2)
"""
from __future__ import annotations

import os
import secrets
from dataclasses import dataclass
from typing import Optional
from datetime import datetime, timedelta

from ..database.db_v2 import db_v2


@dataclass
class SpendIntent:
    id: int
    user_id: int
    intent_token: str
    amount_pts: int
    status: str
    created_at: str
    expires_at: Optional[str]
    consumed_at: Optional[str]


class LoyaltyService:
    def __init__(self, default_ttl_minutes: int = 15):
        self.default_ttl = default_ttl_minutes

    # Wallets
    def get_balance(self, user_id: int) -> int:
        with db_v2.get_connection() as conn:
            row = conn.execute(
                "SELECT balance_pts FROM loyalty_wallets WHERE user_id = ?",
                (user_id,),
            ).fetchone()
            return int(row[0]) if row else 0

    def ensure_wallet(self, user_id: int) -> None:
        with db_v2.get_connection() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO loyalty_wallets (user_id, balance_pts) VALUES (?, 0)",
                (user_id,),
            )

    def adjust_balance(self, user_id: int, delta_pts: int, note: str = "", ref: Optional[int] = None) -> int:
        """Atomically adjust balance and record transaction. Returns new balance."""
        with db_v2.get_connection() as conn:
            # Ensure wallet row exists
            conn.execute(
                "INSERT OR IGNORE INTO loyalty_wallets (user_id, balance_pts) VALUES (?, 0)",
                (user_id,),
            )
            cur = conn.execute(
                "UPDATE loyalty_wallets SET balance_pts = balance_pts + ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ? RETURNING balance_pts",
                (delta_pts, user_id),
            )
            row = cur.fetchone()
            new_bal = int(row[0]) if row else 0
            kind = "accrual" if delta_pts > 0 else ("redeem" if delta_pts < 0 else "adjust")
            conn.execute(
                """
                INSERT INTO loyalty_transactions (user_id, kind, delta_pts, balance_after, ref, note)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (user_id, kind, delta_pts, new_bal, ref, note),
            )
            return new_bal

    # Spend intents
    def _gen_token(self) -> str:
        return secrets.token_urlsafe(24)

    def create_spend_intent(self, user_id: int, amount_pts: int, ttl_minutes: Optional[int] = None) -> Optional[SpendIntent]:
        """Create single active intent per user. Returns intent or None if existing active one."""
        ttl = ttl_minutes or self.default_ttl
        expires = datetime.utcnow() + timedelta(minutes=ttl)
        token = self._gen_token()
        with db_v2.get_connection() as conn:
            # Check existing active
            existing = conn.execute(
                "SELECT id FROM loy_spend_intents WHERE user_id = ? AND status = 'active'",
                (user_id,),
            ).fetchone()
            if existing:
                return None
            cur = conn.execute(
                """
                INSERT INTO loy_spend_intents (user_id, intent_token, amount_pts, status, expires_at)
                VALUES (?, ?, ?, 'active', ?)
                RETURNING id, user_id, intent_token, amount_pts, status, created_at, expires_at, consumed_at
                """,
                (user_id, token, amount_pts, expires.strftime("%Y-%m-%d %H:%M:%S")),
            )
            row = cur.fetchone()
            return SpendIntent(**dict(row)) if row else None

    def consume_spend_intent(self, user_id: int, token: str) -> bool:
        """Consume active intent: deduct balance and mark consumed atomically if enough balance and not expired."""
        with db_v2.get_connection() as conn:
            # Get intent
            intent = conn.execute(
                """
                SELECT id, amount_pts FROM loy_spend_intents
                WHERE user_id = ? AND intent_token = ? AND status = 'active'
                  AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
                """,
                (user_id, token),
            ).fetchone()
            if not intent:
                return False
            amount = int(intent[1])
            # Check balance
            bal_row = conn.execute(
                "SELECT balance_pts FROM loyalty_wallets WHERE user_id = ?",
                (user_id,),
            ).fetchone()
            balance = int(bal_row[0]) if bal_row else 0
            if balance < amount:
                return False
            # Deduct and mark consumed
            conn.execute(
                "UPDATE loyalty_wallets SET balance_pts = balance_pts - ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
                (amount, user_id),
            )
            conn.execute(
                "UPDATE loy_spend_intents SET status = 'consumed', consumed_at = CURRENT_TIMESTAMP WHERE id = ?",
                (int(intent[0]),),
            )
            # Log transaction
            new_bal = balance - amount
            conn.execute(
                """
                INSERT INTO loyalty_transactions (user_id, kind, delta_pts, balance_after, ref, note)
                VALUES (?, 'redeem', ?, ?, ?, ?)
                """,
                (user_id, -amount, new_bal, int(intent[0]), "redeem via intent"),
            )
            return True


loyalty_service = LoyaltyService()
