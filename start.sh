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
