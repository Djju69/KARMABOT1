#!/usr/bin/env python3
"""
Add Railway variables guide
"""
def main():
    print("🎯 ADD RAILWAY VARIABLES")
    print("="*50)
    print("Found URL: https://web-production-d51c7.up.railway.app/")
    print("="*50)

    print("\n📍 STEP 1: Open Railway Dashboard")
    print("🔗 https://railway.app/dashboard")

    print("\n📍 STEP 2: Select your project")
    print("Project ID: fe51fd14-7977-471a-8966-9ca498f4c729")

    print("\n📍 STEP 3: Go to Variables")
    print("1. Click 'Variables' tab")
    print("2. Click 'Add Variable'")

    print("\n📍 STEP 4: Add these variables:")
    print("RAILWAY_ENVIRONMENT=production")
    print("RAILWAY_STATIC_URL=https://web-production-d51c7.up.railway.app/")

    print("\n📍 STEP 5: Save and redeploy")
    print("1. Click 'Save' or 'Deploy'")
    print("2. Wait for Railway to rebuild (5-7 minutes)")

    print("\n" + "="*50)
    print("🎯 EXPECTED RESULTS:")
    print("✅ Bot will switch to webhook mode")
    print("✅ No more polling mode warnings")
    print("✅ Production-ready deployment")
    print("✅ Router import warnings fixed")

    print("\n📋 CHECK LOGS AFTER:")
    print("🌐 Railway detected, using webhook: https://web-production-d51c7.up.railway.app/")
    print("🤖 === BOT STARTUP BEGIN ===")
    print("🧹 Clearing webhook to avoid conflicts...")

    print("\n" + "="*50)
    print("⚠️  DON'T FORGET TO COMMIT:")
    print("git add bot/bootstrap.py")
    print("git commit -m 'fix: Correct router imports'")
    print("git push origin main")

if __name__ == "__main__":
    main()
