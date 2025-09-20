#!/usr/bin/env python3
import subprocess
import sys

def check_git_status():
    """Check git status"""
    try:
        result = subprocess.run(['git', 'status'], capture_output=True, text=True, encoding='utf-8')
        print("=== GIT STATUS ===")
        print(f"Exit code: {result.returncode}")
        print(f"Output:\n{result.stdout}")
        if result.stderr:
            print(f"Error:\n{result.stderr}")
        return result.returncode == 0
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    check_git_status()
