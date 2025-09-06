#!/usr/bin/env python3
import subprocess
import sys

def run_command(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        print(f"Running: {cmd}")
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(f"Error: {result.stderr}")
        return result.returncode == 0
    except Exception as e:
        print(f"Exception: {e}")
        return False

# Add file
if not run_command("git add bot/bootstrap.py"):
    sys.exit(1)

# Commit
commit_msg = """fix: Correct router import paths in bootstrap.py

- Fix main_menu_router import path from main_menu to main_menu_router
- Fix activity_router import from get_activity_router() to activity_router
- Add missing profile_router and language_router imports
- Remove conditional partner router logic that was causing issues"""

if not run_command(f'git commit -m "{commit_msg}"'):
    sys.exit(1)

# Push
if not run_command("git push origin main"):
    sys.exit(1)

print("✅ Bootstrap fixes committed and pushed successfully!")
print("📊 Check Railway deployment logs...")
