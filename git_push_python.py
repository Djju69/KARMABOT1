#!/usr/bin/env python3
"""
Git push script using subprocess
"""
import subprocess
import sys
import os

def run_git_command(args):
    """Run git command and return result"""
    try:
        cmd = ['git'] + args
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        
        print(f"Exit code: {result.returncode}")
        if result.stdout:
            print(f"Output:\n{result.stdout}")
        if result.stderr:
            print(f"Error:\n{result.stderr}")
            
        return result.returncode == 0
    except Exception as e:
        print(f"Error running git command: {e}")
        return False

def main():
    """Main function"""
    print("🚀 Starting Git operations...")
    
    # Check if we're in git repo
    if not os.path.exists('.git'):
        print("❌ Not in a git repository!")
        return False
    
    # Add all changes
    print("\n📁 Adding all changes...")
    if not run_git_command(['add', '.']):
        print("❌ Failed to add changes")
        return False
    
    # Check status
    print("\n📊 Checking status...")
    run_git_command(['status'])
    
    # Commit
    print("\n💾 Committing changes...")
    commit_msg = """chore: fix legacy imports and remove outdated files

- Created modern exception module core/common/exceptions.py
- Created restaurant keyboards module core/keyboards/restaurant_keyboards.py  
- Updated all imports in handlers and services to use new modules
- Removed legacy files: core/keyboards/inline.py and core/exceptions.py
- Updated legacy_report.json to reflect completed cleanup"""
    
    if not run_git_command(['commit', '-m', commit_msg]):
        print("❌ Failed to commit")
        return False
    
    # Push
    print("\n🚀 Pushing to remote...")
    if not run_git_command(['push', 'origin', 'main']):
        print("❌ Failed to push")
        return False
    
    print("\n✅ Successfully pushed all changes!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
