#!/usr/bin/env python3
"""
Quick fix for Railway deployment
"""
import subprocess
import sys

def run_cmd(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd='.')
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return -1, "", str(e)

def main():
    print("🚀 QUICK FIX FOR RAILWAY DEPLOYMENT")
    print("="*50)

    print("📋 EXECUTING FIXES:")

    # Step 1: Add bootstrap changes
    print("\n1. Adding bootstrap.py changes...")
    code, stdout, stderr = run_cmd("git add bot/bootstrap.py")
    if code == 0:
        print("✅ Added bot/bootstrap.py")
    else:
        print(f"❌ Failed to add: {stderr}")

    # Step 2: Commit changes
    print("\n2. Committing changes...")
    commit_msg = "fix: Router imports - category_handlers_v2 and partner_router fixes"
    code, stdout, stderr = run_cmd(f'git commit -m "{commit_msg}"')
    if code == 0:
        print("✅ Changes committed")
    else:
        print(f"⚠️  Commit result: {stdout}")

    # Step 3: Push to GitHub
    print("\n3. Pushing to GitHub...")
    code, stdout, stderr = run_cmd("git push origin main")
    if code == 0:
        print("✅ Pushed to GitHub")
    else:
        print(f"❌ Push failed: {stderr}")

    print("\n" + "="*50)
    print("🎯 NEXT STEPS IN RAILWAY:")
    print("1. Go to: https://railway.app/dashboard")
    print("2. Select your KARMABOT1 project")
    print("3. Click 'Deployments' tab")
    print("4. Click 'Redeploy' button")
    print("5. Wait 5-7 minutes")
    print("6. Check logs for:")
    print("   🌐 Railway detected, using webhook...")
    print("   ✅ Category router registered")
    print("   ✅ Partner router registered")

    print("\n" + "="*50)
    print("⚠️  IF STILL FAILING:")
    print("- Check Railway Variables tab")
    print("- Ensure RAILWAY_ENVIRONMENT=production exists")
    print("- Ensure RAILWAY_STATIC_URL is correct")
    print("- Try 'Redeploy' again")

if __name__ == "__main__":
    main()
