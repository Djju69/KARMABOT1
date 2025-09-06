#!/usr/bin/env python3
"""
Commit deployment marker
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
    print("🚨 ADDING DEPLOYMENT MARKER")
    print("="*50)

    # Add start.py
    print("📤 Adding start.py...")
    code, stdout, stderr = run_cmd("git add start.py")
    if code != 0:
        print(f"❌ Failed to add: {stderr}")
        return

    # Commit
    print("💾 Committing...")
    commit_msg = "debug: Add deployment marker V3.0 to verify Railway sync"
    code, stdout, stderr = run_cmd(f'git commit -m "{commit_msg}"')
    if code != 0:
        print(f"❌ Failed to commit: {stderr}")
        return

    # Push
    print("🚀 Pushing to GitHub...")
    code, stdout, stderr = run_cmd("git push origin main")
    if code == 0:
        print("✅ Successfully pushed to GitHub!")
        print("\n🎯 CRITICAL TEST:")
        print("Check Railway logs for:")
        print("🚨 START.PY LOADED - DEPLOYMENT MARKER V3.0")
        print("✅ IMPORTS LOADED SUCCESSFULLY")
        print("")
        print("If you see these messages:")
        print("✅ Railway is using updated code")
        print("✅ Our fixes are active")
        print("")
        print("If you DON'T see these messages:")
        print("❌ Railway is using cached old code")
        print("❌ Need to force clean rebuild")
        print("")
        print("This will tell us exactly what's happening!")
    else:
        print(f"❌ Push failed: {stderr}")

if __name__ == "__main__":
    main()
