from typing import Optional, Dict, Any
import os

from fastapi import APIRouter, HTTPException, Header, Depends, Body
from fastapi.responses import HTMLResponse

import asyncpg
from core.security.deps import require_admin
from core.security import policy
from core.services.cache import cache_service
import pyotp

TFA_PREFIX = "admin2fa"

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

def _require_admin(header_token: Optional[str]):
    if os.getenv("ALLOW_ADMIN_MIGRATIONS") not in ("1", "true", "yes", "on"):
        raise HTTPException(status_code=403, detail="admin migrations disabled")
    expected = os.getenv("ADMIN_SQL_TOKEN")
    if not expected or not header_token or header_token != expected:
        raise HTTPException(status_code=401, detail="invalid admin token")


"""
NOTE: Миграционные эндпоинты ниже оставлены временно для безопасного применения миграции в проде.
Их можно удалить после того, как:
  1) в прод-БД подтверждено наличие колонки `archived_at` в `partner_cards`;
  2) все необходимые данные заархивированы/бэкфил сделан;
  3) отключены переменные окружения `ALLOW_ADMIN_MIGRATIONS` и `ADMIN_SQL_TOKEN`;
  4) принято решение больше не выполнять эти операции через HTTP.

Рекомендуется держать их только в dev-среде под флагами.
"""
@router.post("/admin/migrate/partner-archived")
async def migrate_partner_archived(
    x_admin_token: Optional[str] = Header(default=None),
    admin_claims: Dict[str, Any] = Depends(require_admin),
    x_mfa_code: Optional[str] = Header(default=None),
):
    _require_admin(x_admin_token)
    # Centralized RBAC policy
    if not policy.can(admin_claims, action=policy.SQL_MIGRATE, resource="partners:migrate"):
        raise HTTPException(status_code=403, detail="forbidden")
    await _enforce_mfa(admin_claims, x_mfa_code)
    res = await _run_sql(MIGRATION_SQL)
    return {"ok": True, "applied": True}


@router.get("/admin/check/partner-archived")
async def check_partner_archived(
    x_admin_token: Optional[str] = Header(default=None),
    admin_claims: Dict[str, Any] = Depends(require_admin),
    x_mfa_code: Optional[str] = Header(default=None),
):
    _require_admin(x_admin_token)
    if not policy.can(admin_claims, action=policy.SQL_CHECK, resource="partners:migrate"):
        raise HTTPException(status_code=403, detail="forbidden")
    await _enforce_mfa(admin_claims, x_mfa_code)
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


# ============ Admin 2FA (TOTP) ============

async def _load_secret(admin_id: str) -> Optional[str]:
    key = f"{TFA_PREFIX}:{admin_id}:secret"
    return await cache_service.get(key)


async def _save_secret(admin_id: str, secret: str):
    # Store with long TTL (~365 days) in Redis or memory fallback
    ttl = 365 * 24 * 60 * 60
    key = f"{TFA_PREFIX}:{admin_id}:secret"
    await cache_service.set(key, secret, ttl)


async def _delete_secret(admin_id: str):
    # Use mask delete helper (memory fallback supported)
    await cache_service.delete_by_mask(f"{TFA_PREFIX}:{admin_id}:*")


def _admin_id_from_claims(claims: Dict[str, Any]) -> str:
    sub = str(claims.get("sub") or "").strip()
    if not sub:
        raise HTTPException(status_code=401, detail="invalid admin sub")
    return sub


async def _enforce_mfa(claims: Dict[str, Any], code: Optional[str]):
    admin_id = _admin_id_from_claims(claims)
    secret = await _load_secret(admin_id)
    if not secret:
        # 2FA mandatory for admins: require enrollment before sensitive ops
        raise HTTPException(status_code=403, detail="mfa_required")
    if not code:
        raise HTTPException(status_code=401, detail="missing_mfa_code")
    totp = pyotp.TOTP(secret)
    if not totp.verify(code, valid_window=1):
        raise HTTPException(status_code=401, detail="invalid_mfa_code")


@router.post("/admin/2fa/enroll")
async def admin_2fa_enroll(admin_claims: Dict[str, Any] = Depends(require_admin)):
    admin_id = _admin_id_from_claims(admin_claims)
    # Generate new base32 secret and return otpauth URL
    secret = pyotp.random_base32()
    await _save_secret(admin_id, secret)
    issuer = os.getenv("PROJECT_NAME", "KARMABOT1")
    label = f"{issuer}:admin:{admin_id}"
    uri = pyotp.totp.TOTP(secret).provisioning_uri(name=label, issuer_name=issuer)
    return {"secret": secret, "otpauth_url": uri}


@router.post("/admin/2fa/verify")
async def admin_2fa_verify(payload: Dict[str, Any] = Body(...), admin_claims: Dict[str, Any] = Depends(require_admin)):
    admin_id = _admin_id_from_claims(admin_claims)
    code = (payload or {}).get("code") if isinstance(payload, dict) else None
    secret = await _load_secret(admin_id)
    if not secret:
        raise HTTPException(status_code=404, detail="mfa_not_enrolled")
    totp = pyotp.TOTP(secret)
    if not totp.verify(code, valid_window=1):
        raise HTTPException(status_code=401, detail="invalid_mfa_code")
    return {"ok": True}


@router.delete("/admin/2fa")
async def admin_2fa_disable(payload: Dict[str, Any] = Body(...), admin_claims: Dict[str, Any] = Depends(require_admin)):
    admin_id = _admin_id_from_claims(admin_claims)
    code = (payload or {}).get("code") if isinstance(payload, dict) else None
    secret = await _load_secret(admin_id)
    if not secret:
        return {"ok": True}
    totp = pyotp.TOTP(secret)
    if not totp.verify(code, valid_window=1):
        raise HTTPException(status_code=401, detail="invalid_mfa_code")
    await _delete_secret(admin_id)
    return {"ok": True}


# ======== Minimal Admin UI: Disable 2FA (optional) ========
# Exposed only when ADMIN_UI_2FA is enabled in environment
if os.getenv("ADMIN_UI_2FA") in ("1", "true", "yes", "on"):
    @router.get("/admin/2fa/ui", response_class=HTMLResponse)
    async def admin_2fa_ui():
        # Simple client page to disable 2FA by providing Bearer token and current TOTP code.
        # Intended for local/admin use only.
        html = """
    <!doctype html>
    <html lang=\"en\">
    <head>
      <meta charset=\"utf-8\" />
      <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
      <title>KARMABOT1 Admin 2FA</title>
      <style>
        body { font-family: system-ui, Arial, sans-serif; margin: 24px; color: #1f2937; }
        .card { max-width: 560px; border: 1px solid #e5e7eb; border-radius: 10px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,.04); }
        label { display: block; font-weight: 600; margin-top: 12px; }
        input, textarea { width: 100%; box-sizing: border-box; padding: 10px; margin-top: 6px; border: 1px solid #d1d5db; border-radius: 8px; font-size: 14px; }
        button { margin-top: 16px; padding: 10px 14px; background: #ef4444; color: white; border: none; border-radius: 8px; font-weight: 700; cursor: pointer; }
        button:hover { background: #dc2626; }
        .note { font-size: 12px; color: #6b7280; margin-top: 4px; }
        .ok { color: #16a34a; font-weight: 700; }
        .err { color: #b91c1c; font-weight: 700; white-space: pre-wrap; }
      </style>
    </head>
    <body>
      <div class=\"card\">
        <h2>Disable Admin 2FA</h2>
        <p class=\"note\">Вставьте ваш Bearer токен администратора и текущий 6-значный код из аутентификатора.</p>
        <label for=\"token\">Bearer token</label>
        <textarea id=\"token\" rows=\"3\" placeholder=\"eyJhbGciOi...\"></textarea>

        <label for=\"code\">TOTP code</label>
        <input id=\"code\" type=\"text\" inputmode=\"numeric\" maxlength=\"6\" placeholder=\"123456\" />

        <button id=\"btn\">Disable 2FA</button>
        <div id=\"out\" style=\"margin-top:12px\"></div>
      </div>

      <script>
        const btn = document.getElementById('btn');
        const out = document.getElementById('out');
        btn.addEventListener('click', async () => {
          out.textContent = '...'; out.className='';
          const token = document.getElementById('token').value.trim();
          const code = document.getElementById('code').value.trim();
          if (!token) { out.textContent = 'Введите Bearer токен'; out.className='err'; return; }
          if (!code) { out.textContent = 'Введите 6-значный код'; out.className='err'; return; }
          try {
            const res = await fetch('/admin/2fa', {
              method: 'DELETE',
              headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
              body: JSON.stringify({ code })
            });
            const data = await res.json().catch(() => ({}));
            if (res.ok && data.ok) { out.textContent = '2FA отключена'; out.className='ok'; }
            else { out.textContent = `Error: ${res.status} - ${JSON.stringify(data)}`; out.className='err'; }
          } catch (e) {
            out.textContent = String(e);
            out.className='err';
          }
        });
      </script>
    </body>
    </html>
    """
        return HTMLResponse(content=html)

