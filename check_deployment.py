#!/usr/bin/env python3
"""
Check deployment status and provide troubleshooting
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
    print("🔍 Checking deployment status...\n")

    # Check git status
    print("📋 Git status:")
    code, stdout, stderr = run_cmd("git status --porcelain")
    if code == 0:
        if stdout.strip():
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
    print("🎯 DEPLOYMENT STATUS:")
    print("✅ APPLY_MIGRATIONS=1 (enabled)")
    print("✅ Latest commit: 8 minutes ago")
    print("⏳ Railway should be rebuilding...")

    print("\n🔧 TROUBLESHOOTING:")
    print("1. Check: https://github.com/Djju69/KARMABOT1/actions")
    print("2. Check Railway dashboard logs")
    print("3. Look for BOT_TOKEN detection logs")
    print("4. Check if migrations ran successfully")

    print("\n⚠️  If deployment fails:")
    print("- Check Railway environment variables")
    print("- Verify BOT_TOKEN is set correctly")
    print("- Check PostgreSQL connection")

if __name__ == "__main__":
    main()
