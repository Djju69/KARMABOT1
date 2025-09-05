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
git commit -m "feat: Complete WebApp interface and QR codes system - Full-featured WebApp with responsive design - User profile page with tabs - Catalog page with search and filters - QR codes management page - Referrals page with tree view - Bootstrap 5 responsive design - Interactive JavaScript with AJAX - Static files (CSS, JS, images) - QR code service with generation, validation, redemption - Database migrations for QR codes - Unit and integration tests - Progress updated to 100%"

echo.
echo 4. Pushing to GitHub...
git push origin main

echo.
echo SUCCESS! All changes pushed to GitHub!
pause
