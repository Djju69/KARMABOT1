@echo off
echo 🚀 COMMITTING V5.0 WEBHOOK FORCE FIX
echo ==================================================

echo 📤 Adding start.py...
git add start.py

echo 💾 Committing with V5.0 markers...
git commit -m "fix: Force webhook mode always - ignore environment variables"

echo 🚀 Pushing to GitHub...
git push origin main

echo.
echo ✅ V5.0 FORCE FIX PUSHED!
echo.
echo 🎯 LOOK FOR IN RAILWAY LOGS:
echo ================================
echo 🚨 START.PY LOADED - DEPLOYMENT MARKER V5.0
echo 🎯 RAILWAY WEBHOOK FORCE ENABLED - ALWAYS
echo ✅ POLLING DISABLED - WEBHOOK ONLY
echo ================================
echo 🚀 FORCE ENABLING WEBHOOK MODE FOR RAILWAY (ALWAYS)
echo 🌐 Railway detected, using webhook: https://web-production-d51c7.up.railway.app/
echo ✅ Webhook mode enabled
echo 🚀 Bot started in webhook mode
echo ================================
echo.
echo Press any key to continue...
pause >nul
