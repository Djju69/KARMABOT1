#!/usr/bin/env python3
"""Dry run script to check what files would be deleted during repo cleanup."""

import glob
import os

def main():
    print("🔍 DRY RUN: Checking files that would be deleted during repo cleanup\n")
    
    patterns = [
        # Sensitive files and secrets
        "*.json.key", "*service-account*.json", "*credentials*.json", "*secret*.json", "*.p12",
        "mythic-brook-*.json",
        
        # Database files
        "*.db", "*.sqlite", "*.sqlite3",
        
        # Old entry points
        "main.py", "main_old.py", "app.py", "run.py",
        
        # Root duplicates
        "category_handlers.py", "database.py",
        
        # Broken/random files
        "h -u origin main --force", "etup*", "*~", "*.swp", "*.orig",
        
        # Environment files (keep only .env.example and env.prod.example)
        "env.example", "env.example.txt", "env.dev.view", "env.local", "env.production",
        
        # Build config (keep only pyproject.toml)
        "setup.py", "setup.cfg",
        
        # Heroku/Netlify artifacts
        "Procfile", "runtime.txt", "netlify.toml",
        "index.js", "package.json", "package-lock.json", "yarn.lock",
        
        # Deploy scripts (keep only deploy.ps1 and deploy.sh)
        "deploy_windows.ps1", "deploy_simple.ps1", "check_deployment.ps1", "check_status.ps1",
        "deploy.bat",
        
        # Old helper scripts
        "fix_deployment.py", "fix_text_imports.py", "update_settings.py", 
        "update_settings_fixed.py", "enable_partner_fsm.py", "generate_test_token.py",
        
        # Requirements duplicates
        "requirements-auth.txt", "requirements-qr.txt",
    ]
    
    files_to_delete = []
    files_to_keep = []
    
    for pattern in patterns:
        matches = glob.glob(pattern)
        for file_path in matches:
            if os.path.isfile(file_path):
                files_to_delete.append(file_path)
            else:
                files_to_keep.append(f"{file_path} (not a file)")
    
    print(f"📁 Files that would be DELETED ({len(files_to_delete)}):")
    for file_path in sorted(files_to_delete):
        print(f"  ❌ {file_path}")
    
    print(f"\n📁 Files that would be KEPT (not found) ({len(files_to_keep)}):")
    for file_path in sorted(files_to_keep):
        print(f"  ✅ {file_path}")
    
    print(f"\n📊 Summary:")
    print(f"  - Files to delete: {len(files_to_delete)}")
    print(f"  - Files to keep: {len(files_to_keep)}")
    
    if files_to_delete:
        print(f"\n⚠️  WARNING: {len(files_to_delete)} files would be deleted!")
        print("   Review the list above before proceeding with actual cleanup.")
    else:
        print(f"\n✅ No files found matching cleanup patterns.")

if __name__ == "__main__":
    main()

