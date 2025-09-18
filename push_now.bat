@echo off
echo Starting Git push...
echo.
echo 1. Checking status...
git status
echo.
echo 2. Adding files...
git add .
echo.
echo 3. Committing...
git commit -m "chore: fix legacy imports and remove outdated files"
echo.
echo 4. Pushing to main...
git push origin main
echo.
echo Done!
pause
