#!/bin/bash
echo "=== RAILWAY STARTUP SCRIPT ==="
echo "Current directory: $(pwd)"
echo "Files in directory:"
ls -la
echo ""
echo "Files in web/:"
ls -la web || echo "[warn] cannot list web/"
echo ""
echo "Python version:"
python --version
echo ""
echo "Environment variables:"
echo "BOT_TOKEN: ${BOT_TOKEN:0:10}...${BOT_TOKEN: -4}"
echo "ADMIN_ID: $ADMIN_ID"
echo "DATABASE_URL: ${DATABASE_URL:0:20}..."
echo "PORT: $PORT"
echo "ALLOW_PARTNER_FOR_CABINET: ${ALLOW_PARTNER_FOR_CABINET:-<unset>}"
echo "APPLY_MIGRATIONS: ${APPLY_MIGRATIONS:-<unset>}"
echo "FEATURE_PARTNER_FSM: ${FEATURE_PARTNER_FSM:-<unset>}"
echo "ENABLE_POLLING_LEADER_LOCK: ${ENABLE_POLLING_LEADER_LOCK:-<unset>}"
echo "PREEMPT_LEADER: ${PREEMPT_LEADER:-<unset>}"
echo "FASTAPI_ONLY: ${FASTAPI_ONLY:-<unset>}"
echo "DISABLE_POLLING: ${DISABLE_POLLING:-<unset>}"
echo "LOYALTY_MIN_SPEND_PTS: ${LOYALTY_MIN_SPEND_PTS:-<unset>}"
echo ""
echo "Dependency versions:"
python - << 'PY'
import importlib
def ver(mod):
    try:
        m = importlib.import_module(mod)
        v = getattr(m, '__version__', None)
        if v is None and mod == 'pydantic_core':
            # pydantic-core exposes version in _pydantic_core
            m2 = importlib.import_module('_pydantic_core')
            v = getattr(m2, '__version__', 'unknown')
        return v or 'unknown'
    except Exception as e:
        return f'ERROR: {e}'

mods = ['aiogram','pydantic','pydantic_core','asyncpg','aiohttp','marshmallow','environs']
for mod in mods:
    print(f" - {mod}: {ver(mod)}")
PY
echo ""
echo "Sanity import: web.routes_auth_email"
python - << 'PY'
import traceback
try:
    import importlib
    m = importlib.import_module('web.routes_auth_email')
    print('[ok] imported web.routes_auth_email, router has', len(getattr(m, 'router').routes), 'routes')
except Exception as e:
    print('[error] cannot import web.routes_auth_email:', e)
    traceback.print_exc()
PY
echo ""
echo "Sanity import: web.routes_cabinet"
python - << 'PY'
import traceback, inspect
try:
    import importlib
    m = importlib.import_module('web.routes_cabinet')
    has_vp = hasattr(m, 'verify_partner')
    print(f"[ok] imported web.routes_cabinet; verify_partner in module: {has_vp}")
    # Extra: print snippet around get_current_claims to ensure fallback present
    try:
        src = inspect.getsource(m.get_current_claims)
        print('[snippet] get_current_claims contains ALLOW_PARTNER:', 'ALLOW_PARTNER_FOR_CABINET' in src)
    except Exception as e:
        print('[warn] cannot introspect get_current_claims:', e)
except Exception as e:
    print('[error] cannot import web.routes_cabinet:', e)
    traceback.print_exc()
PY
echo ""
echo "Apply migrations (optional): APPLY_MIGRATIONS=${APPLY_MIGRATIONS:-0}"
# Accept common truthy values: 1/true/yes/on (case-insensitive)
FLAG="${APPLY_MIGRATIONS,,}"
if [ "$FLAG" = "1" ] || [ "$FLAG" = "true" ] || [ "$FLAG" = "yes" ] || [ "$FLAG" = "on" ]; then
  python - << 'PY'
import os, asyncio, sys
import asyncpg

DB_URL = os.getenv('DATABASE_URL')
migration_path = 'migrations/001_partner_cards.sql'
if not DB_URL:
    print('[migrate] DATABASE_URL not set; skip')
    sys.exit(0)
try:
    with open(migration_path, 'r', encoding='utf-8') as f:
        sql = f.read()
except FileNotFoundError:
    print(f'[migrate] file not found: {migration_path}; skip')
    sys.exit(0)

async def run():
    try:
        conn = await asyncpg.connect(DB_URL)
        try:
            await conn.execute(sql)
            print('[migrate] applied 001_partner_cards.sql successfully')
        finally:
            await conn.close()
    except Exception as e:
        print('[migrate] failed to apply migration:', e)

asyncio.run(run())
PY
  echo ""
else
  echo "[migrate] skipped: APPLY_MIGRATIONS flag is not enabled"
fi
RUN_MODE=${RUN_MODE:-both}
echo "RUN_MODE=$RUN_MODE"
echo "Starting FastAPI WebApp on PORT=${PORT:-8000} (if enabled by RUN_MODE)..."
python - << 'PY'
import os
port = os.getenv('PORT')
if not port:
    # Fallback default
    port = '8000'
print(f"[health] Using port: {port}")
PY
# Запускаем основной WebApp (FastAPI) вместо health_app
# В нём уже есть эндпоинт /health
export FASTAPI_ONLY=${FASTAPI_ONLY:-0}
export DISABLE_POLLING=${DISABLE_POLLING:-0}
echo "\n[boot] Polling config summary:"
echo " - RUN_MODE=${RUN_MODE:-both}"
echo " - FASTAPI_ONLY=${FASTAPI_ONLY}"
echo " - DISABLE_POLLING=${DISABLE_POLLING} (set 1 on followers to avoid getUpdates conflicts)"
echo " - ENABLE_POLLING_LEADER_LOCK=${ENABLE_POLLING_LEADER_LOCK:-0} (1 enables in-app leader election)"
echo " - PREEMPT_LEADER=${PREEMPT_LEADER:-0} (1 forces takeover if lock is stale)"
# Respect PREEMPT_LEADER from environment; do NOT auto-force by default to avoid multi-poller conflicts
if [ "${DISABLE_POLLING}" = "0" ]; then
  : "${PREEMPT_LEADER:=0}"
  export PREEMPT_LEADER
  if [ "${PREEMPT_LEADER}" = "1" ]; then
    echo "[boot] PREEMPT_LEADER explicitly set to 1 → will attempt takeover if lock is stale."
  else
    echo "[boot] PREEMPT_LEADER=0 (default). No forced takeover."
  fi
fi
if [ "$RUN_MODE" = "web" ] || [ "${FASTAPI_ONLY}" = "1" ] || [ "${DISABLE_POLLING}" = "1" ]; then
  echo "[decision] Bot polling will NOT start on this instance. Reason: RUN_MODE=web or FASTAPI_ONLY=1 or DISABLE_POLLING=1."
  echo "[hint] To run a single poller: set DISABLE_POLLING=0 on the leader only; keep 1 on others. Optionally set ENABLE_POLLING_LEADER_LOCK=1 in app to guard against concurrency."
else
  echo "[decision] Bot polling is ALLOWED to start on this instance."
fi
# Optionally start web depending on RUN_MODE
WEB_PID=""
if [ "$RUN_MODE" = "both" ] || [ "$RUN_MODE" = "web" ]; then
  # Start uvicorn and capture PID
  uvicorn web.main:app --host 0.0.0.0 --port ${PORT:-8000} &
  WEB_PID=$!
else
  echo "RUN_MODE=$RUN_MODE → web disabled"
fi

if [ "$RUN_MODE" = "web" ] || [ "${FASTAPI_ONLY}" = "1" ] || [ "${DISABLE_POLLING}" = "1" ]; then
  echo "FASTAPI_ONLY=${FASTAPI_ONLY} DISABLE_POLLING=${DISABLE_POLLING} → бот не запускается на этом инстансе (избегаем getUpdates конфликта)."
  echo "Waiting on web (PID=$WEB_PID) ..."
  wait "$WEB_PID"
else
  echo "Starting bot (main_v2.py) ..."
  # Print first 60 lines of main_v2.py to verify deployed version
  python - << 'PY'
print("--- main_v2.py (head) ---")
try:
    import itertools
    with open('main_v2.py', 'r', encoding='utf-8') as f:
        for i, line in zip(range(60), f):
            print(f"{i+1:02d}: "+line.rstrip('\n'))
except Exception as e:
    print(f"[WARN] Cannot read main_v2.py: {e}")
print("--- end head ---")
PY
  python -u main_v2.py
  if [ -n "$WEB_PID" ]; then
    wait "$WEB_PID"
  fi
fi
