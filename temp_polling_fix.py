#!/usr/bin/env python3
"""
Temporary polling fix for Railway
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
    print("🔧 TEMPORARY POLLING FIX FOR RAILWAY")
    print("="*50)

    # Add start.py
    print("📤 Adding start.py...")
    code, stdout, stderr = run_cmd("git add start.py")
    if code != 0:
        print(f"❌ Failed to add: {stderr}")
        return

    # Commit
    print("💾 Committing temporary polling fix...")
    commit_msg = "fix: Temporary polling mode for Railway - web app not ready yet"
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
        print("🌐 RAILWAY MODE: Web app not available, using polling temporarily")
        print("⚠️ Temporary: Starting polling on Railway (webhook server not ready)")
        print("🤖 BOT_TOKEN found, starting polling on Railway...")
        print("🚀 Starting bot polling...")
        print("✅ Bot commands set up successfully")
        print("="*60)
        print("❌ NO MORE:")
        print("❌ Web app not imported in Railway mode!")
        print("❌ TelegramConflictError (should be gone)")
        print("="*60)
    else:
        print(f"❌ Push failed: {stderr}")

if __name__ == "__main__":
    main()
