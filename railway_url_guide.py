#!/usr/bin/env python3
"""
Guide to find Railway URL for your project
"""
def main():
    print("🎯 RAILWAY URL GUIDE FOR YOUR PROJECT")
    print("="*50)
    print("Project: fe51fd14-7977-471a-8966-9ca498f4c729")
    print("Service: e4b84ecf-4e66-4624-aa11-4d819d38052b")
    print("Environment: 724b2726-022c-424e-8ada-1c213312e1bb")
    print("="*50)

    print("\n📍 STEP 1: Open your Railway project")
    print("🔗 https://railway.com/project/fe51fd14-7977-471a-8966-9ca498f4c729/service/e4b84ecf-4e66-4624-aa11-4d819d38052b?environmentId=724b2726-022c-424e-8ada-1c213312e1bb")

    print("\n📍 STEP 2: Find the URL")
    print("1. Look at the top of the page")
    print("2. Find the domain/URL section")
    print("3. It should look like:")
    print("   ✅ https://karmabot1.up.railway.app")
    print("   ✅ https://karmabot1-production.up.railway.app")
    print("   ✅ https://your-project-name.railway.app")

    print("\n📍 STEP 3: Check Settings")
    print("1. Click 'Settings' tab in your project")
    print("2. Look for 'Domains' or 'URL' section")
    print("3. Copy the full URL including https://")

    print("\n📍 STEP 4: Add Variables")
    print("In Railway Dashboard -> Variables, add:")
    print("RAILWAY_ENVIRONMENT=production")
    print("RAILWAY_STATIC_URL=https://[YOUR-FOUND-URL].railway.app")

    print("\n📍 STEP 5: Alternative - Check Logs")
    print("Look in Railway deployment logs for lines like:")
    print("🌐 Railway detected, using webhook: https://...")

    print("\n" + "="*50)
    print("⚠️  If you can't find the URL:")
    print("1. Try refreshing the Railway page")
    print("2. Check if deployment is active")
    print("3. Contact Railway support if needed")

    print("\n🎯 MOST COMMON URL FORMATS:")
    print("✅ https://karmabot1.up.railway.app")
    print("✅ https://karmabot1-production.up.railway.app")
    print("✅ https://fe51fd14-7977-471a-8966-9ca498f4c729.up.railway.app")

if __name__ == "__main__":
    main()
