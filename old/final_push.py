#!/usr/bin/env python3
import subprocess
import sys
import os

def run_command(cmd):
    """Run command and return result"""
    try:
        print(f"Running: {cmd}")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8')
        print(f"Exit code: {result.returncode}")
        if result.stdout:
            print(f"Output: {result.stdout}")
        if result.stderr:
            print(f"Error: {result.stderr}")
        return result.returncode == 0
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    """Main function"""
    print("🚀 Starting Git push...")
    
    # Add all changes
    print("\n📁 Adding all changes...")
    if not run_command("git add ."):
        print("❌ Failed to add changes")
        return False
    
    # Commit
    print("\n💾 Committing changes...")
    commit_msg = "feat: Complete admin panel implementation - Add comprehensive admin dashboard UI - Implement admin API endpoints - Add user/partner/card management - Add moderation system - Add analytics and reporting - Add system settings - Add audit logging - Add unit tests for admin panel - Update progress documentation"
    
    if not run_command(f'git commit -m "{commit_msg}"'):
        print("❌ Failed to commit")
        return False
    
    # Push
    print("\n🚀 Pushing to remote...")
    if not run_command("git push origin main"):
        print("❌ Failed to push")
        return False
    
    print("\n✅ Successfully pushed all changes!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
