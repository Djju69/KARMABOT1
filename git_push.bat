@echo off
echo Adding all changes...
git add .

echo Checking status...
git status

echo Committing changes...
git commit -m "feat: Complete admin panel implementation

- Add comprehensive admin dashboard UI
- Implement admin API endpoints  
- Add user/partner/card management
- Add moderation system
- Add analytics and reporting
- Add system settings
- Add audit logging
- Add unit tests for admin panel
- Update progress documentation"

echo Pushing to remote...
git push origin main

echo Done!
pause