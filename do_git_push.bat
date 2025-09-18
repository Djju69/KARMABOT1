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
git commit -m "chore: fix legacy imports and remove outdated files - Created modern exception module, restaurant keyboards, updated imports, removed legacy files"

echo.
echo 4. Pushing to remote...
git push origin main

echo.
echo Git operations completed!
pause
