#!/usr/bin/env python3
"""Execute repository cleanup with git operations."""

import os
import subprocess
import sys

def run_command(cmd, description):
    """Run a command and return success status."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} - Success")
            if result.stdout:
                print(f"   Output: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ {description} - Failed")
            if result.stderr:
                print(f"   Error: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"❌ {description} - Exception: {e}")
        return False

def main():
    print("🚀 Starting repository cleanup with git operations...\n")
    
    # Check if we're in a git repository
    if not os.path.exists('.git'):
        print("❌ Not in a git repository. Please run this script from the repository root.")
        return False
    
    # 1. Create cleanup branch
    if not run_command("git checkout -b chore/repo-cleanup", "Creating cleanup branch"):
        print("⚠️  Branch might already exist, continuing...")
        run_command("git checkout chore/repo-cleanup", "Switching to cleanup branch")
    
    # 2. Remove sensitive files
    sensitive_files = [
        "mythic-brook-*.json",
        "*.db",
        "*.sqlite", 
        "*.sqlite3"
    ]
    
    for pattern in sensitive_files:
        run_command(f"git rm -f --ignore-unmatch {pattern}", f"Removing {pattern}")
    
    # 3. Remove old entry points
    old_entry_points = [
        "main.py",
        "main_old.py"
    ]
    
    for file in old_entry_points:
        run_command(f"git rm -f --ignore-unmatch {file}", f"Removing {file}")
    
    # 4. Remove root duplicates
    root_duplicates = [
        "category_handlers.py",
        "database.py"
    ]
    
    for file in root_duplicates:
        run_command(f"git rm -f --ignore-unmatch {file}", f"Removing {file}")
    
    # 5. Remove broken files
    broken_files = [
        '"h -u origin main --force"',
        '"etup"'
    ]
    
    for file in broken_files:
        run_command(f"git rm -f --ignore-unmatch {file}", f"Removing {file}")
    
    # 6. Clean up environment files
    env_files = [
        "env.example",
        "env.example.txt",
        "env.dev.view", 
        "env.local",
        "env.production"
    ]
    
    for file in env_files:
        run_command(f"git rm -f --ignore-unmatch {file}", f"Removing {file}")
    
    # 7. Remove setup.py (keep pyproject.toml)
    run_command("git rm -f --ignore-unmatch setup.py", "Removing setup.py")
    
    # 8. Remove Heroku/Netlify artifacts
    heroku_files = [
        "Procfile",
        "runtime.txt", 
        "netlify.toml",
        "index.js"
    ]
    
    for file in heroku_files:
        run_command(f"git rm -f --ignore-unmatch {file}", f"Removing {file}")
    
    # 9. Clean up deploy scripts
    deploy_scripts = [
        "deploy_windows.ps1",
        "deploy_simple.ps1",
        "check_deployment.ps1", 
        "check_status.ps1",
        "deploy.bat"
    ]
    
    for file in deploy_scripts:
        run_command(f"git rm -f --ignore-unmatch {file}", f"Removing {file}")
    
    # 10. Remove old helper scripts
    helper_scripts = [
        "fix_deployment.py",
        "fix_text_imports.py",
        "update_settings.py",
        "update_settings_fixed.py",
        "enable_partner_fsm.py", 
        "generate_test_token.py"
    ]
    
    for file in helper_scripts:
        run_command(f"git rm -f --ignore-unmatch {file}", f"Removing {file}")
    
    # 11. Remove requirements duplicates
    req_files = [
        "requirements-auth.txt",
        "requirements-qr.txt"
    ]
    
    for file in req_files:
        run_command(f"git rm -f --ignore-unmatch {file}", f"Removing {file}")
    
    # 12. Move documentation files
    docs_moves = [
        ("RAILWAY_VARS.txt", "docs/RAILWAY_VARS.md"),
        ("REPORT.md", "docs/REPORT.md"),
        ("TZ_LK.md", "docs/TZ_LK.md"),
        ("README_WEBAPP.md", "docs/README_WEBAPP.md"),
        ("MONITORING.md", "docs/MONITORING.md")
    ]
    
    # Ensure docs directory exists
    run_command("mkdir -p docs", "Creating docs directory")
    
    for src, dst in docs_moves:
        run_command(f"git mv -f {src} {dst}", f"Moving {src} to {dst}")
    
    # 13. Add updated .gitignore
    run_command("git add .gitignore", "Adding updated .gitignore")
    
    # 14. Commit changes
    if run_command('git commit -m "chore: cleanup repo, remove secrets & binaries, unify env and entrypoints, move docs"', "Committing cleanup changes"):
        print("\n✅ Repository cleanup completed successfully!")
        print("\n📋 Next steps:")
        print("1. Review the changes: git diff HEAD~1")
        print("2. Push the branch: git push -u origin chore/repo-cleanup")
        print("3. Create a pull request on GitHub")
        return True
    else:
        print("\n❌ Cleanup completed but commit failed. Check git status.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

