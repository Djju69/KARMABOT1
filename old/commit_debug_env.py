#!/usr/bin/env python3
"""
Commit debug environment variables
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
    print("🔍 COMMITTING ENVIRONMENT DEBUG CHANGES")
    print("="*50)

    # Add start.py
    print("📤 Adding start.py...")
    code, stdout, stderr = run_cmd("git add start.py")
    if code != 0:
        print(f"❌ Failed to add: {stderr}")
        return

    # Commit
    print("💾 Committing...")
    commit_msg = "debug: Add environment variable logging to diagnose Railway webhook issue"
    code, stdout, stderr = run_cmd(f'git commit -m "{commit_msg}"')
    if code != 0:
        print(f"❌ Failed to commit: {stderr}")
        return

    # Push
    print("🚀 Pushing to GitHub...")
    code, stdout, stderr = run_cmd("git push origin main")
    if code == 0:
        print("✅ Successfully pushed to GitHub!")
        print("\n🎯 WHAT TO LOOK FOR IN RAILWAY LOGS:")
        print("🔍 RAILWAY_ENVIRONMENT: '[value or None]'")
        print("🔍 RAILWAY_STATIC_URL: '[value or None]'")
        print("")
        print("If both are 'None':")
        print("❌ Variables not set in Railway Dashboard")
        print("💡 Go to Railway -> Variables and add them")
        print("")
        print("If RAILWAY_ENVIRONMENT has value:")
        print("✅ Variables are set correctly")
        print("❌ Problem is elsewhere in the code")
        print("🌐 Should see: Railway detected, using webhook")
    else:
        print(f"❌ Push failed: {stderr}")

if __name__ == "__main__":
    main()
