@echo off
echo Starting Git push to GitHub...

echo.
echo 1. Checking Git status...
git status

echo.
echo 2. Adding all files...
git add .

echo.
echo 3. Committing changes...
git commit -m "feat: Complete WebApp interface implementation

- Full-featured WebApp with responsive design
- User profile page with tabs (overview, loyalty, referrals, activity)
- Catalog page with search, filters, and place cards
- QR codes management page with creation and statistics
- Referrals page with tree view and earnings
- Bootstrap 5 responsive design
- Interactive JavaScript with AJAX
- Static files (CSS, JS, images)
- All pages fully functional and tested
- Progress updated to 100%"

echo.
echo 4. Pushing to GitHub...
git push origin main

echo.
echo Git push completed!
pause
