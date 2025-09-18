#!/usr/bin/env python3
"""
Fix mixed modes - separate webhook and polling
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
    print("🔧 FIXING MIXED MODES - WEBHOOK VS POLLING")
    print("="*50)

    # Add start.py
    print("📤 Adding start.py...")
    code, stdout, stderr = run_cmd("git add start.py")
    if code != 0:
        print(f"❌ Failed to add: {stderr}")
        return

    # Commit
    print("💾 Committing mixed modes fix...")
    commit_msg = "fix: Separate webhook and polling modes - no more TelegramConflictError"
    code, stdout, stderr = run_cmd(f'git commit -m "{commit_msg}"')
    if code != 0:
        print(f"❌ Failed to commit: {stderr}")
        return

    # Push
    print("🚀 Pushing to GitHub...")
    code, stdout, stderr = run_cmd("git push origin main")
    if code == 0:
        print("✅ Successfully pushed to GitHub!")
        print("\n🎯 EXPECTED RESULTS IN RAILWAY:")
        print("="*60)
        print("🎯 Deployment mode: RAILWAY (webhook)")
        print("🌐 RAILWAY MODE: Starting webhook server only")
        print("✅ Webhook cleared successfully")
        print("🚀 Bot started in webhook mode")
        print("="*60)
        print("❌ NO MORE:")
        print("❌ Starting bot with polling...")
        print("❌ TelegramConflictError")
        print("="*60)
    else:
        print(f"❌ Push failed: {stderr}")

if __name__ == "__main__":
    main()
