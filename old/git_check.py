#!/usr/bin/env python3
"""
Check git status and help with commit/push
"""
import subprocess
import sys

def run_command(cmd):
    """Run shell command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return -1, "", str(e)

def main():
    print("🔍 Checking git status...")

    # Check git status
    code, stdout, stderr = run_command("git status --porcelain")
    if code != 0:
        print(f"❌ Git status failed: {stderr}")
        return

    print("📋 Git status:")
    print(stdout)

    # Check if start.py is staged
    if "start.py" in stdout:
        print("✅ start.py found in changes")
    else:
        print("❌ start.py not found in changes - need to add it")

    # Check if there are staged changes
    code, stdout, stderr = run_command("git diff --cached --name-only")
    if code != 0:
        print(f"❌ Git diff failed: {stderr}")
        return

    staged_files = stdout.strip().split('\n') if stdout.strip() else []
    if "start.py" in staged_files:
        print("✅ start.py is staged and ready for commit")
    else:
        print("❌ start.py is not staged")
        print("💡 Run: git add start.py")

if __name__ == "__main__":
    main()
