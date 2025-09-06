#!/usr/bin/env python3
"""
Fix imports and commit changes
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
    print("🔧 Fixing imports and committing changes...")

    # Add changes
    code, stdout, stderr = run_cmd("git add bot/bootstrap.py")
    if code != 0:
        print(f"❌ Git add failed: {stderr}")
        return

    # Commit changes
    code, stdout, stderr = run_cmd('git commit -m "fix: Correct imports in bootstrap.py for category_handlers_v2 and partner_router"')
    if code != 0:
        print(f"❌ Git commit failed: {stderr}")
        return

    # Push changes
    code, stdout, stderr = run_cmd("git push origin main")
    if code != 0:
        print(f"❌ Git push failed: {stderr}")
        return

    print("✅ Changes committed and pushed successfully!")

if __name__ == "__main__":
    main()
