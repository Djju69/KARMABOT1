@echo off
echo Starting Git operations...

echo.
echo 1. Checking Git status...
git status

echo.
echo 2. Adding all files...
git add .

echo.
echo 3. Committing changes...
git commit -m "chore: fix legacy imports and remove outdated files - Created modern exception module core/common/exceptions.py - Created restaurant keyboards module core/keyboards/restaurant_keyboards.py - Updated all imports in handlers and services to use new modules - Removed legacy files: core/keyboards/inline.py and core/exceptions.py - Updated legacy_report.json to reflect completed cleanup"

echo.
echo 4. Pushing to GitHub...
git push origin main

echo.
echo SUCCESS! All changes pushed to GitHub!
pause
