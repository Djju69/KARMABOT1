#!/usr/bin/env python3
"""
Find Railway URL from project
"""
import os

def main():
    print("🔍 FINDING RAILWAY URL")
    print("="*50)

    # Check environment variables
    railway_url = os.getenv('RAILWAY_STATIC_URL')
    if railway_url:
        print(f"✅ Found RAILWAY_STATIC_URL: {railway_url}")
        return

    print("📋 WHERE TO FIND RAILWAY URL:")
    print("\n1. Railway Dashboard:")
    print("   - Go to: https://railway.app/dashboard")
    print("   - Select your project")
    print("   - Go to 'Settings' tab")
    print("   - Look for 'Domains' section")
    print("   - Copy the URL (usually: your-project-name.railway.app)")

    print("\n2. Railway Project Page:")
    print("   - Click on your project")
    print("   - Look at the top - there should be a URL")
    print("   - Format: https://<project-name>.railway.app")

    print("\n3. Alternative method:")
    print("   - Check Railway email confirmation")
    print("   - Look for deployment confirmation emails")

    print("\n" + "="*50)
    print("🎯 EXAMPLE URLS:")
    print("✅ https://karmabot1-production.up.railway.app")
    print("✅ https://my-karma-bot.railway.app")
    print("✅ https://karmabot.railway.app")

    print("\n🔧 HOW TO ADD:")
    print("RAILWAY_STATIC_URL=https://your-project-name.railway.app")
    print("RAILWAY_ENVIRONMENT=production")

if __name__ == "__main__":
    main()
