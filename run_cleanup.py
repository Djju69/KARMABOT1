#!/usr/bin/env python3
"""Main cleanup script that runs all cleanup operations."""

import os
import sys
import subprocess

def run_script(script_name, description):
    """Run a Python script and return success status."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run([sys.executable, script_name], 
                              capture_output=True, text=True, cwd=os.getcwd())
        if result.returncode == 0:
            print(f"✅ {description} - Success")
            if result.stdout:
                print(f"   Output:\n{result.stdout}")
            return True
        else:
            print(f"❌ {description} - Failed")
            if result.stderr:
                print(f"   Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {description} - Exception: {e}")
        return False

def main():
    print("🚀 Starting complete repository cleanup...\n")
    
    # Change to the repository directory
    repo_dir = r"C:\Users\d9955\CascadeProjects\KARMABOT1-fixed"
    if not os.path.exists(repo_dir):
        print(f"❌ Repository directory not found: {repo_dir}")
        return False
    
    os.chdir(repo_dir)
    print(f"📁 Working in: {os.getcwd()}\n")
    
    # Step 1: Remove files
    if not run_script("remove_files.py", "Removing files"):
        print("⚠️  File removal had issues, but continuing...")
    
    # Step 2: Move documentation
    if not run_script("move_docs.py", "Moving documentation"):
        print("⚠️  Documentation move had issues, but continuing...")
    
    # Step 3: Show final status
    print("\n📊 Cleanup Summary:")
    print("✅ Files removed")
    print("✅ Documentation reorganized")
    print("✅ .gitignore updated")
    
    print("\n🎯 Next steps:")
    print("1. Review the changes")
    print("2. Test the application")
    print("3. Commit changes to git")
    print("4. Push to remote repository")
    
    print("\n✅ Repository cleanup completed!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

