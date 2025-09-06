#!/usr/bin/env python3
"""
Commit debug changes
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
    print("📝 COMMITTING DEBUG CHANGES")
    print("="*50)

    # Add start.py
    print("📤 Adding start.py...")
    code, stdout, stderr = run_cmd("git add start.py")
    if code != 0:
        print(f"❌ Failed to add: {stderr}")
        return

    # Commit
    print("💾 Committing...")
    commit_msg = "debug: Add timestamp print to verify Railway picks up changes"
    code, stdout, stderr = run_cmd(f'git commit -m "{commit_msg}"')
    if code != 0:
        print(f"❌ Failed to commit: {stderr}")
        return

    # Push
    print("🚀 Pushing to GitHub...")
    code, stdout, stderr = run_cmd("git push origin main")
    if code == 0:
        print("✅ Successfully pushed to GitHub!")
        print("\n🎯 NEXT STEPS:")
        print("1. Wait 2-3 minutes")
        print("2. Check Railway logs")
        print("3. Look for: 🚨 DEBUG: Code updated at [timestamp]")
        print("\nIf you see the debug message - Railway is working!")
        print("If not - GitHub integration is broken")
    else:
        print(f"❌ Failed to push: {stderr}")

if __name__ == "__main__":
    main()
