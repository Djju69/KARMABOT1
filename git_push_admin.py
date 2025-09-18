#!/usr/bin/env python3
"""
Git push script for admin panel changes
"""
import subprocess
import sys
import os

def run_command(cmd):
    """Run a command and return the result"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8')
        print(f"Command: {cmd}")
        print(f"Exit code: {result.returncode}")
        if result.stdout:
            print(f"Output: {result.stdout}")
        if result.stderr:
            print(f"Error: {result.stderr}")
        return result.returncode == 0
    except Exception as e:
        print(f"Error running command '{cmd}': {e}")
        return False

def main():
    """Main function to push changes"""
    print("🚀 Starting Git push for admin panel changes...")
    
    # Check if we're in a git repository
    if not os.path.exists('.git'):
        print("❌ Not in a git repository!")
        return False
    
    # Add all changes
    print("\n📁 Adding all changes...")
    if not run_command('git add .'):
        print("❌ Failed to add changes")
        return False
    
    # Check status
    print("\n📊 Checking git status...")
    run_command('git status')
    
    # Commit changes
    commit_message = "feat: Complete admin panel implementation\n\n- Add comprehensive admin dashboard UI\n- Implement admin API endpoints\n- Add user/partner/card management\n- Add moderation system\n- Add analytics and reporting\n- Add system settings\n- Add audit logging\n- Add unit tests for admin panel\n- Update progress documentation"
    
    print(f"\n💾 Committing changes...")
    if not run_command(f'git commit -m "{commit_message}"'):
        print("❌ Failed to commit changes")
        return False
    
    # Push to remote
    print(f"\n🚀 Pushing to remote repository...")
    if not run_command('git push origin main'):
        print("❌ Failed to push to remote")
        return False
    
    print("\n✅ Successfully pushed all changes!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
