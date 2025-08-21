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
echo "Starting Python script..."
python -u simple_test.py
