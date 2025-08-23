from typing import Optional, Dict, Any
import os

from fastapi import APIRouter, HTTPException, Header

import asyncpg

router = APIRouter()

MIGRATION_SQL = """
ALTER TABLE partner_cards
    ADD COLUMN IF NOT EXISTS archived_at TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS idx_partner_cards_archived_at ON partner_cards (archived_at);
"""


async def _run_sql(sql: str) -> Dict[str, Any]:
    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        raise HTTPException(status_code=500, detail="DATABASE_URL not configured")
    conn: Optional[asyncpg.Connection] = None
    try:
        conn = await asyncpg.connect(dsn)
        await conn.execute(sql)
        return {"ok": True}
    finally:
        if conn:
            await conn.close()


# Temporary secured endpoint to archive all rows for a given tg_user_id
@router.post("/admin/debug/archive-all")
async def debug_archive_all(tg_user_id: int, x_admin_token: Optional[str] = Header(default=None)):
    _require_admin(x_admin_token)
    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        raise HTTPException(status_code=500, detail="DATABASE_URL not configured")
    conn: Optional[asyncpg.Connection] = None
    try:
        conn = await asyncpg.connect(dsn)
        result = await conn.execute(
            """
            UPDATE partner_cards
            SET archived_at = NOW()
            WHERE tg_user_id = $1
              AND archived_at IS NULL
            """,
            tg_user_id,
        )
        # asyncpg returns strings like "UPDATE <count>"
        try:
            affected = int(result.split()[-1])
        except Exception:
            affected = 0
        return {"ok": True, "updated": affected}
    finally:
        if conn:
            await conn.close()


def _require_admin(header_token: Optional[str]):
    if os.getenv("ALLOW_ADMIN_MIGRATIONS") not in ("1", "true", "yes", "on"):
        raise HTTPException(status_code=403, detail="admin migrations disabled")
    expected = os.getenv("ADMIN_SQL_TOKEN")
    if not expected or not header_token or header_token != expected:
        raise HTTPException(status_code=401, detail="invalid admin token")


@router.post("/admin/migrate/partner-archived")
async def migrate_partner_archived(x_admin_token: Optional[str] = Header(default=None)):
    _require_admin(x_admin_token)
    res = await _run_sql(MIGRATION_SQL)
    return {"ok": True, "applied": True}


@router.get("/admin/check/partner-archived")
async def check_partner_archived(x_admin_token: Optional[str] = Header(default=None)):
    _require_admin(x_admin_token)
    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        raise HTTPException(status_code=500, detail="DATABASE_URL not configured")
    conn: Optional[asyncpg.Connection] = None
    try:
        conn = await asyncpg.connect(dsn)
        row = await conn.fetchrow(
            """
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name='partner_cards' AND column_name='archived_at'
            """
        )
        exists = row is not None
        return {"ok": True, "exists": exists, "column": dict(row) if row else None}
    finally:
        if conn:
            await conn.close()


# Temporary debug endpoint to inspect rows as seen by the running app's DATABASE_URL.
# Protected by the same admin token/flag gate as migrations.
@router.get("/admin/debug/partner-cards")
async def debug_partner_cards(tg_user_id: int, x_admin_token: Optional[str] = Header(default=None)):
    _require_admin(x_admin_token)
    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        raise HTTPException(status_code=500, detail="DATABASE_URL not configured")
    conn: Optional[asyncpg.Connection] = None
    try:
        conn = await asyncpg.connect(dsn)
        rows = await conn.fetch(
            """
            SELECT id, tg_user_id, status, archived_at
            FROM partner_cards
            WHERE tg_user_id = $1
            ORDER BY id
            """,
            tg_user_id,
        )
        data = [dict(r) for r in rows]
        return {"ok": True, "count": len(data), "rows": data}
    finally:
        if conn:
            await conn.close()
