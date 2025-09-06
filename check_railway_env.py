#!/usr/bin/env python3
"""
Check Railway environment and provide setup instructions
"""
import os

def main():
    print("🔍 RAILWAY ENVIRONMENT CHECK")
    print("="*50)

    # Check Railway-specific variables
    railway_vars = [
        'RAILWAY_ENVIRONMENT',
        'RAILWAY_STATIC_URL',
        'RAILWAY_PROJECT_ID',
        'PORT'
    ]

    print("📋 Railway Variables:")
    for var in railway_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: NOT SET")

    print("\n📋 Required Variables:")
    required_vars = ['BOT_TOKEN', 'DATABASE_URL', 'REDIS_URL']
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {'*' * min(len(value), 10)}...")
        else:
            print(f"❌ {var}: NOT SET")

    print("\n" + "="*50)
    print("🎯 MISSING VARIABLES TO ADD IN RAILWAY:")
    print("1. RAILWAY_ENVIRONMENT=production")
    print("2. RAILWAY_STATIC_URL=your-app-name.railway.app")

    print("\n🔧 WHY THIS MATTERS:")
    print("- RAILWAY_ENVIRONMENT enables webhook mode")
    print("- Without it, bot runs in polling mode (not suitable for production)")
    print("- RAILWAY_STATIC_URL is needed for webhook URL construction")

if __name__ == "__main__":
    main()
