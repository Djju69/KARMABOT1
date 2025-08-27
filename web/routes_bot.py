from __future__ import annotations

import os
import traceback
import hmac
import hashlib
import time
from ipaddress import ip_network, ip_address
from datetime import datetime, timezone
from typing import Optional, List

from fastapi import APIRouter, Request, HTTPException
from starlette.responses import JSONResponse

from core.services.cache import cache_service
from ops.session_state import mark_webhook_ui_refresh, save as ss_save
from core.utils.telemetry import log_event

router = APIRouter()


def _parse_allowlist(val: str) -> List[str]:
    parts = [p.strip() for p in (val or "").split(",")]
    return [p for p in parts if p]


def _client_ip(request: Request) -> str:
    # prefer first X-Forwarded-For ip
    xff = request.headers.get("x-forwarded-for") or request.headers.get("X-Forwarded-For")
    if xff:
        first = xff.split(",")[0].strip()
        if first:
            return first
    return request.client.host if request.client else ""


def _ip_allowed(ip: str, allowlist: List[str]) -> bool:
    if not allowlist:
        return True  # allow all if not configured
    try:
        ip_obj = ip_address(ip)
        for item in allowlist:
            try:
                if "/" in item:
                    if ip_obj in ip_network(item, strict=False):
                        return True
                else:
                    if ip == item:
                        return True
            except Exception:
                continue
    except Exception:
        return False
    return False


def _compute_signature(secret: str, ts: str, body: bytes) -> str:
    mac = hmac.new(secret.encode("utf-8"), digestmod=hashlib.sha256)
    mac.update(ts.encode("utf-8"))
    mac.update(b".")
    mac.update(body)
    return "sha256=" + mac.hexdigest()


async def _dedupe_try(key: str, ttl_sec: int) -> bool:
    # Prefer Redis SETNX with EX
    r = getattr(cache_service, "_redis", None)
    if r is not None:
        try:
            # aioredis>=2: set(name, value, nx=True, ex=ttl)
            ok = await r.set(key, "1", ex=ttl_sec, nx=True)
            return bool(ok)
        except Exception:
            pass
    # Fallback (memory): approximate using get/set under lock
    existing = await cache_service.get(key)
    if existing:
        return False
    await cache_service.set(key, "1", ttl_sec)
    return True


@router.post("/ui.refresh_menu")
async def ui_refresh_menu(request: Request):
    # Security headers
    ts = request.headers.get("X-Karma-Timestamp") or ""
    sig = request.headers.get("X-Karma-Signature") or ""
    request_id = request.headers.get("X-Request-Id") or request.headers.get("x-request-id") or ""
    trace_id = request.headers.get("X-Trace-Id") or request.headers.get("x-trace-id") or ""
    t0 = time.monotonic()

    # IP allowlist
    allowlist = _parse_allowlist(os.getenv("WEBHOOK_IP_ALLOWLIST", ""))
    ip = _client_ip(request)
    if not _ip_allowed(ip, allowlist):
        dur_ms = int((time.monotonic() - t0) * 1000)
        await log_event(
            "ui.refresh_menu",
            ip=ip,
            allowlist=allowlist,
            outcome="rejected",
            request_id=request_id,
            trace_id=trace_id,
            status_code=403,
            duration_ms=dur_ms,
            error="ip_not_allowed",
        )
        return JSONResponse(status_code=403, content={"ok": False, "code": "unauthorized"})

    # Timestamp skew
    try:
        ts_i = int(ts)
    except Exception:
        dur_ms = int((time.monotonic() - t0) * 1000)
        await log_event(
            "ui.refresh_menu",
            ip=ip,
            outcome="rejected",
            request_id=request_id,
            trace_id=trace_id,
            status_code=401,
            duration_ms=dur_ms,
            error="bad_timestamp",
        )
        return JSONResponse(status_code=401, content={"ok": False, "code": "unauthorized"})
    skew = int(os.getenv("BOT_WEBHOOK_MAX_SKEW_SEC", "120") or 120)
    now = int(time.time())
    if abs(now - ts_i) > skew:
        dur_ms = int((time.monotonic() - t0) * 1000)
        await log_event(
            "ui.refresh_menu",
            ip=ip,
            outcome="rejected",
            request_id=request_id,
            trace_id=trace_id,
            status_code=401,
            duration_ms=dur_ms,
            error="timestamp_skew",
            ts=ts_i,
            now=now,
        )
        return JSONResponse(status_code=401, content={"ok": False, "code": "unauthorized"})

    # Body and HMAC
    secret = os.getenv("BOT_WEBHOOK_SECRET", "")
    if not secret:
        dur_ms = int((time.monotonic() - t0) * 1000)
        await log_event(
            "ui.refresh_menu",
            outcome="error",
            request_id=request_id,
            trace_id=trace_id,
            status_code=500,
            duration_ms=dur_ms,
            error="missing_secret",
        )
        return JSONResponse(status_code=500, content={"ok": False, "code": "server_error"})

    body = await request.body()
    expected = _compute_signature(secret, ts, body)
    if not hmac.compare_digest(sig, expected):
        dur_ms = int((time.monotonic() - t0) * 1000)
        await log_event(
            "ui.refresh_menu",
            ip=ip,
            outcome="rejected",
            request_id=request_id,
            trace_id=trace_id,
            status_code=401,
            duration_ms=dur_ms,
            error="bad_signature",
        )
        return JSONResponse(status_code=401, content={"ok": False, "code": "unauthorized"})

    # Main processing: JSON parse, idempotency, and success
    try:
        # Predefine to avoid UnboundLocalError in edge branches
        payload = {}
        user_id = ""
        reason = "manual"
        # Parse JSON
        try:
            payload = await request.json()
        except Exception:
            dur_ms = int((time.monotonic() - t0) * 1000)
            await log_event(
                "ui.refresh_menu",
                ip=ip,
                outcome="rejected",
                request_id=request_id,
                trace_id=trace_id,
                status_code=400,
                duration_ms=dur_ms,
                error="bad_json",
            )
            return JSONResponse(status_code=400, content={"ok": False, "code": "unauthorized"})

        user_id = str(payload.get("user_id") or payload.get("uid") or "")
        reason = str(payload.get("reason") or "manual")

        # Idempotency key: 30s buckets
        rounded = (ts_i // 30) * 30
        dedupe_key = None
        # Only enforce idempotency if we have a user_id
        if user_id:
            dedupe_key = f"{user_id}:{reason}:{rounded}"
            full_key = f"dedupe:{dedupe_key}"
            if not await _dedupe_try(full_key, 30):
                dur_ms = int((time.monotonic() - t0) * 1000)
                await log_event(
                    "ui.refresh_menu",
                    ip=ip,
                    user_id=user_id,
                    reason=reason,
                    outcome="duplicate",
                    request_id=request_id,
                    trace_id=trace_id,
                    dedupe_key=dedupe_key,
                    status_code=200,
                    duration_ms=dur_ms,
                )
                return JSONResponse(status_code=200, content={"ok": True, "result": "duplicate"})

        # TODO: place business logic here (e.g., enqueue refresh, notify bot, etc.)
        # Persist marker into SESSION_STATE (best-effort)
        try:
            mark_webhook_ui_refresh(reason=reason, ts=datetime.fromtimestamp(ts_i, tz=timezone.utc))
            ss_save()
        except Exception:
            pass
        dur_ms = int((time.monotonic() - t0) * 1000)
        await log_event(
            "ui.refresh_menu",
            ip=ip,
            user_id=user_id,
            reason=reason,
            outcome="processed",
            request_id=request_id,
            trace_id=trace_id,
            dedupe_key=dedupe_key,
            status_code=200,
            duration_ms=dur_ms,
            error=None,
        )
        return JSONResponse(status_code=200, content={"ok": True, "result": "processed"})
    except Exception as e:
        # Log unexpected exceptions and return JSON 500 for easier diagnostics
        dur_ms = int((time.monotonic() - t0) * 1000)
        tb = traceback.format_exc()
        tb_short = " | ".join([line.strip() for line in tb.strip().splitlines()[-5:]])
        try:
            await log_event(
                "ui.refresh_menu",
                ip=_client_ip(request),
                outcome="error",
                request_id=request_id,
                trace_id=trace_id,
                status_code=500,
                duration_ms=dur_ms,
                error=f"{type(e).__name__}: {str(e)} | {tb_short}",
            )
        except Exception:
            pass
        return JSONResponse(status_code=500, content={"ok": False, "code": "server_error"})
