#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Local Git push script
"""

import subprocess
import sys
import os

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
    print("Starting local Git operations...")
    
    # Check if we're in a Git repository
    if not os.path.exists('.git'):
        print("Error: Not in a Git repository!")
        return False
    
    # Check Git status
    if not run_command("git status", "1. Checking Git status"):
        return False
    
    # Add all files
    if not run_command("git add .", "2. Adding all files"):
        return False
    
    # Commit changes
    commit_message = """feat: Complete WebApp interface implementation

- Full-featured WebApp with responsive design
- User profile page with tabs (overview, loyalty, referrals, activity)
- Catalog page with search, filters, and place cards
- QR codes management page with creation and statistics
- Referrals page with tree view and earnings
- Bootstrap 5 responsive design
- Interactive JavaScript with AJAX
- Static files (CSS, JS, images)
- All pages fully functional and tested
- Progress updated to 100%"""
    
    if not run_command(f'git commit -m "{commit_message}"', "3. Committing changes"):
        return False
    
    # Push to remote
    if not run_command("git push origin main", "4. Pushing to remote"):
        return False
    
    print("\n✅ Local Git operations completed successfully!")
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n❌ Git operations failed!")
        sys.exit(1)
    else:
        print("\n🎉 All done! Code pushed successfully!")
