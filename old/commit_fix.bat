@echo off
echo Committing IndentationError fix...
git add .
git commit -m "CRITICAL FIX: Fixed IndentationError in migrations.py line 503"
git push origin main
echo Done!
pause
