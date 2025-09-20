#!/usr/bin/env python3
"""
Simple test to check if Python works on Railway
"""
import sys
import os

print("=== SIMPLE RAILWAY TEST ===")
print(f"Python version: {sys.version}")
print(f"Platform: {sys.platform}")
print(f"Current directory: {os.getcwd()}")
print(f"Files in directory: {os.listdir('.')}")

# Check environment variables
print("\n=== ENVIRONMENT VARIABLES ===")
for key in ['BOT_TOKEN', 'ADMIN_ID', 'DATABASE_URL', 'PORT']:
    value = os.getenv(key)
    if value:
        if key == 'BOT_TOKEN':
            print(f"{key}: {value[:10]}...{value[-4:]}")
        else:
            print(f"{key}: {value}")
    else:
        print(f"{key}: NOT SET")

# Test basic imports
print("\n=== IMPORT TEST ===")
try:
    import aiogram
    print(f"aiogram: {aiogram.__version__}")
except Exception as e:
    print(f"aiogram FAILED: {e}")

try:
    from environs import Env
    print("environs: OK")
except Exception as e:
    print(f"environs FAILED: {e}")

print("\n=== TEST COMPLETE ===")
print("If you see this message, Python is working on Railway!")
