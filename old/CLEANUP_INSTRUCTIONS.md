# 🧹 Repository Cleanup Instructions

## Overview
This document provides instructions for cleaning up the KARMABOT1 repository by removing sensitive files, duplicates, and artifacts.

## ⚠️ Important Warnings

### Security
- **NEVER** commit sensitive files like service account keys, database files, or secrets
- The file `mythic-brook-414011-6b6b807faea2.json` appears to be a GCP service account key - **DELETE IMMEDIATELY** and revoke the key in Google Cloud Console
- Database files (`*.db`, `*.sqlite`) should never be in version control

### Backup
- Create a backup branch before starting cleanup
- Review all changes before pushing to remote

## 🗑️ Files to Remove

### 1. Sensitive Files (CRITICAL)
```
mythic-brook-414011-6b6b807faea2.json  # GCP service account key
*.db, *.sqlite, *.sqlite3              # Database files
```

### 2. Old Entry Points
```
main.py                                # Old main file
main_old.py                           # Very old main file
```

### 3. Root Duplicates
```
category_handlers.py                  # Duplicate of core/handlers/category_handlers_v2.py
database.py                           # Duplicate of core/database/...
```

### 4. Broken/Random Files
```
"h -u origin main --force"            # Accidental file with spaces
"etup"                                # Broken filename
```

### 5. Environment Files (Keep only .env.example and env.prod.example)
```
env.example
env.example.txt
env.dev.view
env.local
env.production
```

### 6. Build Configuration (Keep only pyproject.toml)
```
setup.py
```

### 7. Platform-Specific Artifacts
```
Procfile                              # Heroku
runtime.txt                           # Heroku
netlify.toml                          # Netlify
index.js                              # Node.js
```

### 8. Deploy Scripts (Keep only deploy.ps1 and deploy.sh)
```
deploy_windows.ps1
deploy_simple.ps1
check_deployment.ps1
check_status.ps1
deploy.bat
```

### 9. Old Helper Scripts
```
fix_deployment.py
fix_text_imports.py
update_settings.py
update_settings_fixed.py
enable_partner_fsm.py
generate_test_token.py
```

### 10. Requirements Duplicates
```
requirements-auth.txt
requirements-qr.txt
```

## 📚 Files to Move to docs/

```
RAILWAY_VARS.txt → docs/RAILWAY_VARS.md
REPORT.md → docs/REPORT.md
TZ_LK.md → docs/TZ_LK.md
README_WEBAPP.md → docs/README_WEBAPP.md
MONITORING.md → docs/MONITORING.md
```

## 🔧 Execution Methods

### Method 1: Automated Script
```bash
# Run the cleanup script
python cleanup_repo.py

# Or run with git operations
python execute_cleanup.py
```

### Method 2: Manual Git Commands
```bash
# 1. Create cleanup branch
git checkout -b chore/repo-cleanup

# 2. Remove sensitive files
git rm -f mythic-brook-*.json *.db *.sqlite *.sqlite3

# 3. Remove old entry points
git rm -f main.py main_old.py

# 4. Remove root duplicates
git rm -f category_handlers.py database.py

# 5. Remove broken files
git rm -f "h -u origin main --force" "etup"

# 6. Clean environment files
git rm -f env.example env.example.txt env.dev.view env.local env.production

# 7. Remove setup.py
git rm -f setup.py

# 8. Remove platform artifacts
git rm -f Procfile runtime.txt netlify.toml index.js

# 9. Clean deploy scripts
git rm -f deploy_windows.ps1 deploy_simple.ps1 check_deployment.ps1 check_status.ps1 deploy.bat

# 10. Remove helper scripts
git rm -f fix_deployment.py fix_text_imports.py update_settings.py update_settings_fixed.py enable_partner_fsm.py generate_test_token.py

# 11. Remove requirements duplicates
git rm -f requirements-auth.txt requirements-qr.txt

# 12. Move documentation
mkdir -p docs
git mv RAILWAY_VARS.txt docs/RAILWAY_VARS.md
git mv REPORT.md docs/REPORT.md
git mv TZ_LK.md docs/TZ_LK.md
git mv README_WEBAPP.md docs/README_WEBAPP.md
git mv MONITORING.md docs/MONITORING.md

# 13. Add updated .gitignore
git add .gitignore

# 14. Commit changes
git commit -m "chore: cleanup repo, remove secrets & binaries, unify env and entrypoints, move docs"

# 15. Push branch
git push -u origin chore/repo-cleanup
```

## ✅ Verification

After cleanup, verify:

1. **No sensitive files**: Check that no `.json` keys or database files remain
2. **Single entry point**: Only `main_v2.py` should be the main entry point
3. **Clean structure**: No duplicate files in root directory
4. **Documentation**: All docs moved to `docs/` directory
5. **Git status**: `git status` should show only intended changes

## 🚨 Security Checklist

- [ ] Service account keys removed and revoked
- [ ] Database files removed from git history
- [ ] `.gitignore` updated to prevent future commits
- [ ] No secrets in commit history (check with `git log --all --full-history -- "*.json"`)

## 📋 Post-Cleanup Tasks

1. Update README.md to reflect new structure
2. Update deployment documentation
3. Test that the application still works
4. Update CI/CD pipelines if needed
5. Create pull request for review

## 🔄 Rollback

If something goes wrong:
```bash
# Switch back to main branch
git checkout main

# Delete cleanup branch
git branch -D chore/repo-cleanup

# Reset to previous state
git reset --hard HEAD~1
```

