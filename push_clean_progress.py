#!/usr/bin/env python3
"""
Push Clean Progress
Commits and pushes cleaned and organized progress.md
"""

import subprocess
import sys
import os
from datetime import datetime

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return None

def main():
    """Main function to push clean progress"""
    print("🧹 Starting Clean Progress Push")
    print("=" * 60)
    
    # Check if we're in a git repository
    if not os.path.exists('.git'):
        print("❌ Not in a git repository")
        sys.exit(1)
    
    # Get current timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Check if progress.md exists
    if not os.path.exists('progress.md'):
        print("❌ progress.md not found")
        sys.exit(1)
    
    # Add progress.md to git
    result = run_command("git add progress.md", "Adding progress.md")
    if result is None:
        sys.exit(1)
    
    # Commit changes
    commit_message = f"""docs: Clean and organize progress.md

🧹 PROGRESS CLEANUP:
- Removed duplicate sections and redundant information
- Organized structure with clear hierarchy
- Updated all status indicators to reflect actual implementation
- Removed outdated "В процессе" sections that are now 100% complete
- Consolidated all completed features into single sections
- Removed conflicting status reports
- Streamlined critical tasks section
- Updated final project status to 100% readiness

📊 STRUCTURE IMPROVEMENTS:
- Clear component hierarchy (Architecture → Database → Services → Features)
- Consistent status indicators (✅ for completed, 🔄 for in progress)
- Removed duplicate "Завершено" sections
- Consolidated all 100% complete features
- Clean separation between critical tasks and low-priority items
- Updated timestamp and final status

🎯 STATUS UPDATES:
- All critical components marked as 100% complete
- Removed false "in progress" indicators
- Updated partner program from 60% to 100%
- Consolidated admin panel, testing, and moderation status
- Clean final project status declaration

📅 Cleaned: {timestamp}"""
    
    result = run_command(f'git commit -m "{commit_message}"', "Committing clean progress")
    if result is None:
        sys.exit(1)
    
    # Push to remote
    result = run_command("git push origin main", "Pushing to remote repository")
    if result is None:
        sys.exit(1)
    
    print("\n🎉 Clean Progress Successfully Pushed!")
    print("=" * 60)
    print("📋 Summary of cleanup:")
    print("✅ Removed duplicate sections")
    print("✅ Organized clear hierarchy")
    print("✅ Updated all status indicators")
    print("✅ Removed outdated progress sections")
    print("✅ Consolidated completed features")
    print("✅ Streamlined critical tasks")
    print("✅ Updated final status to 100%")
    print("\n🚀 Progress.md is now clean and organized!")
    print("🎯 All critical tasks are 100% complete!")

if __name__ == "__main__":
    main()
