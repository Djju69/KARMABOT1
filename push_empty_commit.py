#!/usr/bin/env python3
"""
Push empty commit to trigger Railway rebuild
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
    print("🚀 PUSHING EMPTY COMMIT TO TRIGGER RAILWAY")
    print("="*50)

    print("📋 Checking git status...")
    code, stdout, stderr = run_cmd("git status --porcelain")
    if code == 0:
        if stdout.strip():
            print("📝 Uncommitted changes found:")
            print(stdout)
        else:
            print("✅ Working directory clean")
    else:
        print(f"❌ Git status failed: {stderr}")
        return

    # Check recent commits
    print("\n📋 Recent commits:")
    code, stdout, stderr = run_cmd("git log --oneline -3")
    if code == 0:
        print(stdout)
    else:
        print(f"❌ Git log failed: {stderr}")
        return

    print("\n" + "="*50)
    print("🔄 CREATING EMPTY COMMIT...")

    # Create empty commit
    code, stdout, stderr = run_cmd('git commit --allow-empty -m "force: Trigger Railway rebuild - empty commit"')
    if code != 0:
        print(f"❌ Failed to create empty commit: {stderr}")
        return

    print("✅ Empty commit created")

    # Push to GitHub
    print("📤 Pushing to GitHub...")
    code, stdout, stderr = run_cmd("git push origin main")
    if code == 0:
        print("✅ Successfully pushed to GitHub!")
        print("\n🎯 RESULT:")
        print("- Railway should detect new commit")
        print("- Automatic rebuild should start")
        print("- Check Railway logs in 3-5 minutes")
        print("- Look for: 🚨 DEBUG: Code updated at [timestamp]")
    else:
        print(f"❌ Push failed: {stderr}")
        print("\n🔧 Try manual commands:")
        print("git commit --allow-empty -m 'force rebuild'")
        print("git push origin main")

if __name__ == "__main__":
    main()
