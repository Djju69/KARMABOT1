@echo off
echo 🚀 Pushing empty commit to trigger Railway rebuild
echo ==================================================

echo 📋 Checking git status...
git status --porcelain
if %errorlevel% neq 0 (
    echo ❌ Git status failed
    pause
    exit /b 1
)

echo.
echo 📋 Recent commits:
git log --oneline -3
if %errorlevel% neq 0 (
    echo ❌ Git log failed
    pause
    exit /b 1
)

echo.
echo ==================================================
echo 🔄 Creating empty commit...

git commit --allow-empty -m "force: Trigger Railway rebuild - empty commit"
if %errorlevel% neq 0 (
    echo ❌ Failed to create empty commit
    pause
    exit /b 1
)

echo ✅ Empty commit created
echo.
echo 📤 Pushing to GitHub...

git push origin main
if %errorlevel% neq 0 (
    echo ❌ Push failed
    echo.
    echo 🔧 Try manual commands:
    echo git commit --allow-empty -m "force rebuild"
    echo git push origin main
    pause
    exit /b 1
)

echo ✅ Successfully pushed to GitHub!
echo.
echo 🎯 RESULT:
echo - Railway should detect new commit
echo - Automatic rebuild should start
echo - Check Railway logs in 3-5 minutes
echo - Look for: 🚨 DEBUG: Code updated at [timestamp]
echo.
echo Press any key to continue...
pause >nul
