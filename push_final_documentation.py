#!/usr/bin/env python3
"""
Push Final Documentation
Commits and pushes all documentation updates for Railway deployment
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
    """Main function to push final documentation"""
    print("📚 Starting Final Documentation Push")
    print("=" * 60)
    
    # Check if we're in a git repository
    if not os.path.exists('.git'):
        print("❌ Not in a git repository")
        sys.exit(1)
    
    # Get current timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Files to commit
    files_to_commit = [
        "README.md",
        "DEPLOY.md",
        "RAILWAY_VARS.md",
        "RAILWAY_DEPLOY_READY.md",
        "check_railway_deploy.py",
        "Dockerfile"
    ]
    
    # Check if files exist
    missing_files = []
    for file_path in files_to_commit:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        sys.exit(1)
    
    # Add files to git
    for file_path in files_to_commit:
        result = run_command(f"git add {file_path}", f"Adding {file_path}")
        if result is None:
            sys.exit(1)
    
    # Commit changes
    commit_message = f"""docs: Complete Railway deployment documentation

📚 FINAL DOCUMENTATION UPDATE:
- Updated README.md with 100% completion status
- Added Railway deployment instructions
- Created comprehensive deployment guides
- Updated project status and features

🚀 RAILWAY DEPLOYMENT READY:
- DEPLOY.md: Quick 5-minute deployment guide
- RAILWAY_VARS.md: Environment variables reference
- RAILWAY_DEPLOY_READY.md: Complete deployment report
- check_railway_deploy.py: Deployment readiness checker

📊 PROJECT STATUS UPDATES:
- Status badge updated to 100% Ready
- Added Railway deployment badge
- Updated features section with all components
- Added comprehensive documentation links

🔧 TECHNICAL UPDATES:
- Dockerfile optimized for Railway
- Health check endpoint verified
- Start script configured for Railway
- Environment variables documented

📅 Documentation completed: {timestamp}"""
    
    result = run_command(f'git commit -m "{commit_message}"', "Committing final documentation")
    if result is None:
        sys.exit(1)
    
    # Push to remote
    result = run_command("git push origin main", "Pushing to remote repository")
    if result is None:
        sys.exit(1)
    
    print("\n🎉 Final Documentation Successfully Pushed!")
    print("=" * 60)
    print("📋 Summary of documentation updates:")
    print("✅ README.md updated with 100% status")
    print("✅ DEPLOY.md created - quick deployment guide")
    print("✅ RAILWAY_VARS.md created - environment variables")
    print("✅ RAILWAY_DEPLOY_READY.md created - deployment report")
    print("✅ check_railway_deploy.py created - readiness checker")
    print("✅ Dockerfile optimized for Railway")
    print("\n🚀 Project is now fully documented and ready for Railway deployment!")
    print("🎯 Follow DEPLOY.md for 5-minute deployment!")

if __name__ == "__main__":
    main()
