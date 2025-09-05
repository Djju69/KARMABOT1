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
git commit -m "feat: Added new services and endpoints - Referral system, User profiles, Geo search, Admin endpoints, Monitoring"

echo.
echo 4. Pushing to remote...
git push origin main

echo.
echo Git operations completed!
pause
