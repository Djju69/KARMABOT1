#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Git push script for all changes
"""

import subprocess
import sys
import os

def run_command(command):
    """Run a command and return the result"""
    print(f"Running: {command}")
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, encoding='utf-8')
        
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
    print("=== Pushing all changes to GitHub ===")
    
    # Check if we're in a Git repository
    if not os.path.exists('.git'):
        print("Error: Not in a Git repository!")
        return False
    
    # Step 1: Check status
    print("\n1. Checking Git status...")
    if not run_command("git status"):
        return False
    
    # Step 2: Add all files
    print("\n2. Adding all files...")
    if not run_command("git add ."):
        return False
    
    # Step 3: Commit changes
    print("\n3. Committing changes...")
    commit_msg = """feat: Complete WebApp interface and QR codes system

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
    
    if not run_command(f'git commit -m "{commit_msg}"'):
        return False
    
    # Step 4: Push to GitHub
    print("\n4. Pushing to GitHub...")
    if not run_command("git push origin main"):
        return False
    
    print("\n✅ SUCCESS! All changes pushed to GitHub!")
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n❌ FAILED! Check the errors above.")
        sys.exit(1)
    else:
        print("\n🎉 DONE! Your code is now on GitHub!")
