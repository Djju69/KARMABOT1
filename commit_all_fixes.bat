@echo off
echo 🚀 Committing all Railway fixes
echo ==================================================

echo 📤 Adding start.py...
git add start.py

echo 📤 Adding core/database/roles.py...
git add core/database/roles.py

echo 💾 Committing fixes...
git commit -m "fix: Force webhook mode and fix DatabaseServiceV2 fetchval error"

echo 🚀 Pushing to GitHub...
git push origin main

echo.
echo ✅ All fixes committed and pushed!
echo.
echo 🎯 EXPECTED RESULTS:
echo ✅ Railway detects webhook mode
echo ✅ No database fetchval errors
echo ✅ Healthcheck passes
echo ✅ Deployment succeeds
echo.
echo Press any key to continue...
pause >nul
