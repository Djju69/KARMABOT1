#!/usr/bin/env python3
"""
Commit all deployment fixes
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
    print("🚀 COMMITTING ALL DEPLOYMENT FIXES")
    print("="*50)

    # Add all changed files
    files_to_add = [
        "start.py",
        "core/database/roles.py"
    ]

    for file in files_to_add:
        print(f"📤 Adding {file}...")
        code, stdout, stderr = run_cmd(f"git add {file}")
        if code != 0:
            print(f"❌ Failed to add {file}: {stderr}")

    # Commit
    print("💾 Committing fixes...")
    commit_msg = "fix: Force webhook mode and fix DatabaseServiceV2 fetchval error"
    code, stdout, stderr = run_cmd(f'git commit -m "{commit_msg}"')
    if code != 0:
        print(f"❌ Failed to commit: {stderr}")
        return

    # Push
    print("🚀 Pushing to GitHub...")
    code, stdout, stderr = run_cmd("git push origin main")
    if code == 0:
        print("✅ Successfully pushed to GitHub!")
        print("\n🎯 FIXES APPLIED:")
        print("✅ Forced webhook mode detection")
        print("✅ Fixed DatabaseServiceV2 fetchval error")
        print("✅ Added environment variable logging")
        print("✅ Health endpoint already exists")
        print("\n📊 EXPECTED RESULTS:")
        print("✅ Railway detects webhook mode")
        print("✅ No database errors")
        print("✅ Healthcheck passes")
        print("✅ Deployment succeeds")
    else:
        print(f"❌ Push failed: {stderr}")

if __name__ == "__main__":
    main()
