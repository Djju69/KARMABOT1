@echo off
echo Adding all changes...
git add .

echo Checking status...
git status

echo Committing changes...
git commit -m "chore: fix legacy imports and remove outdated files

- Created modern exception module core/common/exceptions.py
- Created restaurant keyboards module core/keyboards/restaurant_keyboards.py  
- Updated all imports in handlers and services to use new modules
- Removed legacy files: core/keyboards/inline.py and core/exceptions.py
- Updated legacy_report.json to reflect completed cleanup"

echo Pushing to remote...
git push origin main

echo Done!
pause