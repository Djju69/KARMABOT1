#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Direct Git push using subprocess without shell
"""

import os
import subprocess
import sys

def run_git_direct(args):
    """Run Git command directly without shell"""
    print(f"Running: git {' '.join(args)}")
    
    try:
        result = subprocess.run(
            ['git'] + args,
            capture_output=True,
            text=True,
            encoding='utf-8',
            cwd=os.getcwd()
        )
        
        if result.stdout:
            print("Output:")
            print(result.stdout)
        
        if result.stderr:
            print("Errors:")
            print(result.stderr)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    """Main function to push all changes"""
    print("=== Direct Git Push ===")
    print(f"Working directory: {os.getcwd()}")
    
    # Check if we're in a Git repository
    if not os.path.exists('.git'):
        print("Error: Not in a Git repository!")
        return False
    
    # Step 1: Check Git status
    print("\n1. Checking Git status...")
    if not run_git_direct(['status']):
        print("Failed to check Git status")
        return False
    
    # Step 2: Add all files
    print("\n2. Adding all files...")
    if not run_git_direct(['add', '.']):
        print("Failed to add files")
        return False
    
    # Step 3: Commit changes
    print("\n3. Committing changes...")
    commit_message = "feat: Complete WebApp interface and QR codes system"
    if not run_git_direct(['commit', '-m', commit_message]):
        print("Failed to commit changes")
        return False
    
    # Step 4: Push to GitHub
    print("\n4. Pushing to GitHub...")
    if not run_git_direct(['push', 'origin', 'main']):
        print("Failed to push to GitHub")
        return False
    
    print("\n✅ SUCCESS! All changes pushed to GitHub!")
    return True

if __name__ == "__main__":
    print("Starting direct Git operations...")
    success = main()
    
    if success:
        print("\n🎉 DONE! Your code is now on GitHub!")
    else:
        print("\n❌ FAILED! Check the errors above.")
        sys.exit(1)