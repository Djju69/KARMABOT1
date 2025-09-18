# PowerShell script for Git operations
Write-Host "Starting Git operations..." -ForegroundColor Green

Write-Host "`n1. Checking Git status..." -ForegroundColor Yellow
git status

Write-Host "`n2. Adding all files..." -ForegroundColor Yellow
git add .

Write-Host "`n3. Committing changes..." -ForegroundColor Yellow
git commit -m "chore: fix legacy imports and remove outdated files

- Created modern exception module core/common/exceptions.py
- Created restaurant keyboards module core/keyboards/restaurant_keyboards.py  
- Updated all imports in handlers and services to use new modules
- Removed legacy files: core/keyboards/inline.py and core/exceptions.py
- Updated legacy_report.json to reflect completed cleanup"

Write-Host "`n4. Pushing to remote..." -ForegroundColor Yellow
git push origin main

Write-Host "`nGit operations completed!" -ForegroundColor Green
Read-Host "Press Enter to continue"
