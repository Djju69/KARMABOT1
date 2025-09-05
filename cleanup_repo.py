#!/usr/bin/env python3
"""Script to clean up repository by removing sensitive files, duplicates, and artifacts."""

import os
import shutil
import glob

def safe_remove(file_path):
    """Safely remove a file if it exists."""
    if os.path.exists(file_path):
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
                print(f"✅ Removed file: {file_path}")
                return True
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
                print(f"✅ Removed directory: {file_path}")
                return True
        except Exception as e:
            print(f"❌ Error removing {file_path}: {e}")
            return False
    else:
        print(f"⚠️  File not found: {file_path}")
        return False

def main():
    print("🧹 Starting repository cleanup...\n")
    
    # Files to remove
    files_to_remove = [
        # Sensitive files and secrets
        "mythic-brook-414011-6b6b807faea2.json",
        
        # Database files
        "database.db",
        "sqlite.db", 
        "test_loyalty.db",
        
        # Old entry points
        "main.py",
        "main_old.py",
        
        # Root duplicates
        "category_handlers.py",
        "database.py",
        
        # Broken/random files
        "h -u origin main --force",
        "etup",
        
        # Environment files (keep only .env.example and env.prod.example)
        "env.example",
        "env.example.txt", 
        "env.dev.view",
        "env.local",
        "env.production",
        
        # Build config (keep only pyproject.toml)
        "setup.py",
        
        # Heroku/Netlify artifacts
        "Procfile",
        "runtime.txt",
        "netlify.toml",
        "index.js",
        
        # Deploy scripts (keep only deploy.ps1 and deploy.sh)
        "deploy_windows.ps1",
        "deploy_simple.ps1", 
        "check_deployment.ps1",
        "check_status.ps1",
        "deploy.bat",
        
        # Old helper scripts
        "fix_deployment.py",
        "fix_text_imports.py",
        "update_settings.py",
        "update_settings_fixed.py", 
        "enable_partner_fsm.py",
        "generate_test_token.py",
        
        # Requirements duplicates
        "requirements-auth.txt",
        "requirements-qr.txt",
    ]
    
    removed_count = 0
    total_count = len(files_to_remove)
    
    print(f"📁 Files to remove: {total_count}\n")
    
    for file_path in files_to_remove:
        if safe_remove(file_path):
            removed_count += 1
    
    print(f"\n📊 Cleanup Summary:")
    print(f"  - Files processed: {total_count}")
    print(f"  - Files removed: {removed_count}")
    print(f"  - Files not found: {total_count - removed_count}")
    
    # Move documentation files to docs/
    docs_to_move = [
        ("RAILWAY_VARS.txt", "docs/RAILWAY_VARS.md"),
        ("REPORT.md", "docs/REPORT.md"),
        ("TZ_LK.md", "docs/TZ_LK.md"),
        ("README_WEBAPP.md", "docs/README_WEBAPP.md"),
        ("MONITORING.md", "docs/MONITORING.md"),
    ]
    
    print(f"\n📚 Moving documentation files to docs/...")
    
    # Ensure docs directory exists
    os.makedirs("docs", exist_ok=True)
    
    moved_count = 0
    for src, dst in docs_to_move:
        if os.path.exists(src):
            try:
                shutil.move(src, dst)
                print(f"✅ Moved: {src} → {dst}")
                moved_count += 1
            except Exception as e:
                print(f"❌ Error moving {src}: {e}")
        else:
            print(f"⚠️  File not found: {src}")
    
    print(f"\n📚 Documentation Summary:")
    print(f"  - Files moved: {moved_count}")
    
    print(f"\n✅ Repository cleanup completed!")

if __name__ == "__main__":
    main()

