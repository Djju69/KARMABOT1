#!/usr/bin/env python3
"""Remove files identified for cleanup."""

import os
import shutil

def remove_file(file_path):
    """Remove a file if it exists."""
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
    print("🧹 Starting file removal...\n")
    
    # Critical security files
    critical_files = [
        "mythic-brook-414011-6b6b807faea2.json",
        "database.db",
        "sqlite.db",
        "test_loyalty.db"
    ]
    
    print("🚨 Removing critical security files...")
    for file_path in critical_files:
        remove_file(file_path)
    
    # Old entry points
    old_files = [
        "main.py",
        "main_old.py"
    ]
    
    print("\n📁 Removing old entry points...")
    for file_path in old_files:
        remove_file(file_path)
    
    # Root duplicates
    duplicate_files = [
        "category_handlers.py",
        "database.py"
    ]
    
    print("\n🔄 Removing root duplicates...")
    for file_path in duplicate_files:
        remove_file(file_path)
    
    # Broken files
    broken_files = [
        "h -u origin main --force",
        "etup"
    ]
    
    print("\n🗑️ Removing broken files...")
    for file_path in broken_files:
        remove_file(file_path)
    
    # Environment files
    env_files = [
        "env.example",
        "env.example.txt",
        "env.dev.view",
        "env.local",
        "env.production"
    ]
    
    print("\n🌍 Cleaning environment files...")
    for file_path in env_files:
        remove_file(file_path)
    
    # Build config
    build_files = [
        "setup.py"
    ]
    
    print("\n🏗️ Removing build config...")
    for file_path in build_files:
        remove_file(file_path)
    
    # Platform artifacts
    platform_files = [
        "Procfile",
        "runtime.txt",
        "netlify.toml",
        "index.js"
    ]
    
    print("\n🌐 Removing platform artifacts...")
    for file_path in platform_files:
        remove_file(file_path)
    
    # Deploy scripts
    deploy_files = [
        "deploy_windows.ps1",
        "deploy_simple.ps1",
        "check_deployment.ps1",
        "check_status.ps1",
        "deploy.bat"
    ]
    
    print("\n🚀 Cleaning deploy scripts...")
    for file_path in deploy_files:
        remove_file(file_path)
    
    # Helper scripts
    helper_files = [
        "fix_deployment.py",
        "fix_text_imports.py",
        "update_settings.py",
        "update_settings_fixed.py",
        "enable_partner_fsm.py",
        "generate_test_token.py"
    ]
    
    print("\n🛠️ Removing helper scripts...")
    for file_path in helper_files:
        remove_file(file_path)
    
    # Requirements duplicates
    req_files = [
        "requirements-auth.txt",
        "requirements-qr.txt"
    ]
    
    print("\n📦 Cleaning requirements...")
    for file_path in req_files:
        remove_file(file_path)
    
    print("\n✅ File removal completed!")

if __name__ == "__main__":
    main()

