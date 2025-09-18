@echo off
git add bot/bootstrap.py
git commit -m "fix: Correct router import paths in bootstrap.py

- Fix main_menu_router import path from main_menu to main_menu_router
- Fix activity_router import from get_activity_router() to activity_router
- Add missing profile_router and language_router imports
- Remove conditional partner router logic that was causing issues"

git push origin main
echo.
echo Bootstrap fixes committed and pushed!
echo Check Railway deployment logs...
