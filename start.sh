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
echo "Starting FastAPI WebApp on PORT=$PORT..."
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
# Start uvicorn and capture PID
uvicorn web.main:app --host 0.0.0.0 --port ${PORT:-8000} &
WEB_PID=$!

if [ "${FASTAPI_ONLY}" = "1" ]; then
  echo "FASTAPI_ONLY=1 → бот не запускается на этом инстансе (избегаем getUpdates конфликта)."
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
  wait "$WEB_PID"
fi
