#!/usr/bin/env python3
"""
Force commit the final webhook fix
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
    print("🔧 FORCE COMMITTING FINAL WEBHOOK FIX")
    print("="*50)

    # Add start.py
    print("📤 Adding start.py...")
    code, stdout, stderr = run_cmd("git add start.py")
    if code != 0:
        print(f"❌ Failed to add: {stderr}")
        return

    # Commit
    print("💾 Committing...")
    commit_msg = "fix: Force webhook mode always - ignore environment variables"
    code, stdout, stderr = run_cmd(f'git commit -m "{commit_msg}"')
    if code != 0:
        print(f"❌ Failed to commit: {stderr}")
        return

    # Push
    print("🚀 Pushing to GitHub...")
    code, stdout, stderr = run_cmd("git push origin main")
    if code == 0:
        print("✅ Successfully pushed to GitHub!")
        print("\n🎯 LOOK FOR IN RAILWAY LOGS:")
        print("="*60)
        print("🚨 START.PY LOADED - DEPLOYMENT MARKER V5.0")
        print("🎯 RAILWAY WEBHOOK FORCE ENABLED - ALWAYS")
        print("✅ POLLING DISABLED - WEBHOOK ONLY")
        print("="*60)
        print("🚀 FORCE ENABLING WEBHOOK MODE FOR RAILWAY (ALWAYS)")
        print("🌐 Railway detected, using webhook: https://web-production-d51c7.up.railway.app/")
        print("✅ Webhook mode enabled")
        print("🚀 Bot started in webhook mode")
    else:
        print(f"❌ Push failed: {stderr}")

if __name__ == "__main__":
    main()
