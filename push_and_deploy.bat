@echo off
echo Starting git operations...

git add .
echo Files added to staging

git commit -m "Fix migrations.py indentation error and start.py encoding"
echo Changes committed

git push origin main
echo Changes pushed to repository

echo Deployment completed!
pause
echo Starting git operations...

git add .
echo Files added to staging

git commit -m "Fix migrations.py indentation error and start.py encoding"
echo Changes committed

git push origin main
echo Changes pushed to repository

echo Deployment completed!
pause
