#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Final Git push script using os and subprocess
"""

import os
import subprocess
import sys

def run_git_command(command):
    """Run a Git command using subprocess"""
    print(f"Executing: {command}")
    
    try:
        # Use subprocess.run with proper encoding
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            encoding='utf-8',
            cwd=os.getcwd()
        )
        
        if result.stdout:
            print("STDOUT:")
            print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"Error executing command: {e}")
        return False

def main():
    """Main function to push all changes"""
    print("=== Git Push Script ===")
    print(f"Working directory: {os.getcwd()}")
    
    # Check if we're in a Git repository
    if not os.path.exists('.git'):
        print("Error: Not in a Git repository!")
        return False
    
    # Step 1: Check Git status
    print("\n1. Checking Git status...")
    if not run_git_command("git status"):
        print("Failed to check Git status")
        return False
    
    # Step 2: Add all files
    print("\n2. Adding all files...")
    if not run_git_command("git add ."):
        print("Failed to add files")
        return False
    
    # Step 3: Commit changes
    print("\n3. Committing changes...")
    commit_message = """feat: Complete WebApp interface and QR codes system

- Full-featured WebApp with responsive design
- User profile page with tabs (overview, loyalty, referrals, activity)
- Catalog page with search, filters, and place cards
- QR codes management page with creation and statistics
- Referrals page with tree view and earnings
- Bootstrap 5 responsive design
- Interactive JavaScript with AJAX
- Static files (CSS, JS, images)
- QR code service with generation, validation, redemption
- Database migrations for QR codes
- Unit and integration tests
- Progress updated to 100%"""
    
    if not run_git_command(f'git commit -m "{commit_message}"'):
        print("Failed to commit changes")
        return False
    
    # Step 4: Push to GitHub
    print("\n4. Pushing to GitHub...")
    if not run_git_command("git push origin main"):
        print("Failed to push to GitHub")
        return False
    
    print("\n✅ SUCCESS! All changes pushed to GitHub!")
    return True

if __name__ == "__main__":
    print("Starting Git operations...")
    success = main()
    
    if success:
        print("\n🎉 DONE! Your code is now on GitHub!")
    else:
        print("\n❌ FAILED! Check the errors above.")
        sys.exit(1)
