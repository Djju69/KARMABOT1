#!/usr/bin/env python3
"""
Check current deployment status
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
    print("🔍 CHECKING DEPLOYMENT STATUS")
    print("="*50)

    # Check git status
    print("📋 Git status:")
    code, stdout, stderr = run_cmd("git status --porcelain")
    if code == 0:
        if stdout.strip():
            print("Changes to commit:")
            print(stdout)
        else:
            print("✅ Working directory clean")
    else:
        print(f"❌ Git status failed: {stderr}")

    # Check recent commits
    print("\n📋 Recent commits:")
    code, stdout, stderr = run_cmd("git log --oneline -3")
    if code == 0:
        print(stdout)
    else:
        print(f"❌ Git log failed: {stderr}")

    print("\n" + "="*50)
    print("🎯 CURRENT STATUS:")
    print("✅ Variables should be set in Railway:")
    print("   RAILWAY_ENVIRONMENT=production")
    print("   RAILWAY_STATIC_URL=https://web-production-d51c7.up.railway.app/")

    print("\n📋 WHAT TO CHECK IN RAILWAY:")
    print("1. Variables tab - confirm variables are there")
    print("2. Deployments tab - check latest deployment")
    print("3. Logs - look for webhook messages")
    print("4. If no changes - try 'Redeploy' button")

    print("\n📋 IF STILL POLLING MODE:")
    print("1. Check Railway logs for RAILWAY_ENVIRONMENT detection")
    print("2. Verify webhook URL is correct")
    print("3. Try restarting the service")

    print("\n🔧 NEXT STEPS:")
    print("1. Check Railway dashboard")
    print("2. Look at latest deployment logs")
    print("3. If needed: git add/commit/push bootstrap.py changes")

if __name__ == "__main__":
    main()
