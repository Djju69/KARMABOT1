#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Python script for Git operations
"""
import os
import subprocess
import sys

def run_command(command, description):
    """Run a command and return the result"""
    print(f"\n{description}...")
    print(f"Command: {command}")
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, encoding='utf-8')
        
        if result.stdout:
            print("STDOUT:")
            print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        if result.returncode != 0:
            print(f"Command failed with return code: {result.returncode}")
            return False
        
        return True
        
    except Exception as e:
        print(f"Error running command: {e}")
        return False

def main():
    """Main function to perform Git operations"""
    print("Starting Git operations...")
    
    # Check if we're in a Git repository
    if not os.path.exists('.git'):
        print("Error: Not in a Git repository!")
        return False
    
    # 1. Check Git status
    if not run_command("git status", "1. Checking Git status"):
        return False
    
    # 2. Add all files
    if not run_command("git add .", "2. Adding all files"):
        return False
    
    # 3. Commit changes
    commit_message = "feat: Added new services and endpoints - Referral system, User profiles, Geo search, Admin endpoints, Monitoring"
    if not run_command(f'git commit -m "{commit_message}"', "3. Committing changes"):
        return False
    
    # 4. Push to remote
    if not run_command("git push origin main", "4. Pushing to remote"):
        return False
    
    print("\n✅ Git operations completed successfully!")
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n❌ Git operations failed!")
        sys.exit(1)
    else:
        print("\n🎉 All done!")
