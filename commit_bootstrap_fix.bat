@echo off
echo Adding bootstrap.py...
git add bot/bootstrap.py

echo Committing changes...
git commit -m "fix: Correct router import paths in bootstrap.py

- Fix main_menu_router import path from main_menu to main_menu_router
- Fix activity_router import from get_activity_router() to activity_router
- Add missing profile_router and language_router imports
- Remove conditional partner router logic that was causing issues"

echo Pushing to GitHub...
git push origin main

echo.
echo ✅ Bootstrap fixes committed and pushed!
echo 📊 Check Railway deployment logs...
