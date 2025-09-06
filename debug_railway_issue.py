#!/usr/bin/env python3
"""
Debug Railway deployment issues
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
    print("🔍 DEBUGGING RAILWAY ISSUES")
    print("="*50)

    print("📋 ISSUES IDENTIFIED:")
    print("1. ❌ Still in polling mode (should be webhook)")
    print("2. ❌ TelegramConflictError (another bot instance running)")
    print("3. ❌ category_handlers import still failing")
    print("4. ❌ Multiple routers not found")

    print("\n📋 CHECKING GIT STATUS:")

    # Check git status
    code, stdout, stderr = run_cmd("git status --porcelain")
    if code == 0:
        if stdout.strip():
            print("Changes not committed:")
            print(stdout)
        else:
            print("✅ Working directory clean")
    else:
        print(f"❌ Git status failed: {stderr}")

    # Check recent commits
    print("\n📋 Recent commits:")
    code, stdout, stderr = run_cmd("git log --oneline -5")
    if code == 0:
        print(stdout)
    else:
        print(f"❌ Git log failed: {stderr}")

    print("\n" + "="*50)
    print("🔧 IMMEDIATE FIXES NEEDED:")

    print("\n1. 🚀 PUSH CHANGES TO GITHUB:")
    print("   git add bot/bootstrap.py")
    print("   git commit -m 'fix: Router imports and Railway webhook mode'")
    print("   git push origin main")

    print("\n2. 🌐 VERIFY RAILWAY VARIABLES:")
    print("   Check: https://railway.app/dashboard")
    print("   Variables tab should have:")
    print("   - RAILWAY_ENVIRONMENT=production")
    print("   - RAILWAY_STATIC_URL=https://web-production-d51c7.up.railway.app/")

    print("\n3. 🔄 FORCE RAILWAY REDEPLOY:")
    print("   - Go to Railway project")
    print("   - Click 'Deployments' tab")
    print("   - Click 'Redeploy' button")

    print("\n4. 📋 EXPECTED LOGS AFTER FIX:")
    print("   🌐 Railway detected, using webhook: https://web-production-d51c7.up.railway.app/")
    print("   ✅ Successfully included router from category_handlers_v2")
    print("   ✅ Partner router registered")
    print("   🚀 Bot started in webhook mode")

    print("\n" + "="*50)
    print("⚠️  ROOT CAUSE:")
    print("- Either changes not pushed to GitHub")
    print("- Or Railway using old deployment")
    print("- Or Railway variables not applied")

    print("\n🎯 PRIORITY:")
    print("1. Push code changes to GitHub")
    print("2. Force redeploy in Railway")
    print("3. Monitor logs for webhook mode")

if __name__ == "__main__":
    main()
