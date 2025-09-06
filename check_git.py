#!/usr/bin/env python3
"""
Check git status and recent commits
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
    print("🔍 Checking git status...")

    # Check git log
    code, stdout, stderr = run_cmd("git log --oneline -5")
    if code == 0:
        print("📋 Recent commits:")
        print(stdout)
    else:
        print(f"❌ Git log failed: {stderr}")

    # Check git status
    code, stdout, stderr = run_cmd("git status --porcelain")
    if code == 0:
        if stdout.strip():
            print("📋 Git status:")
            print(stdout)
        else:
            print("✅ Working directory clean")
    else:
        print(f"❌ Git status failed: {stderr}")

if __name__ == "__main__":
    main()
