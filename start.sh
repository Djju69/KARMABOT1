#!/bin/bash
echo "=== RAILWAY STARTUP SCRIPT ==="
echo "Current directory: $(pwd)"
echo "Files in directory:"
ls -la
echo ""
echo "Python version:"
python --version
echo ""
echo "Environment variables:"
echo "BOT_TOKEN: ${BOT_TOKEN:0:10}...${BOT_TOKEN: -4}"
echo "ADMIN_ID: $ADMIN_ID"
echo "DATABASE_URL: ${DATABASE_URL:0:20}..."
echo "PORT: $PORT"
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
echo "Starting health server on PORT=$PORT..."
python - << 'PY'
import os
port = os.getenv('PORT')
if not port:
    # Fallback default
    port = '8000'
print(f"[health] Using port: {port}")
PY
uvicorn health_app:app --host 0.0.0.0 --port ${PORT:-8000} &

echo "Starting bot (debug_main.py) ..."
python -u debug_main.py
