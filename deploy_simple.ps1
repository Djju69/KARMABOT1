# Simple deployment script for KarmaBot

# Step 1: Add all changes
git add .

# Step 2: Commit changes
$commitMessage = "chore: Auto-deploy $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
git commit -m "$commitMessage"

# Step 3: Push to GitHub
git push origin main

Write-Host "✅ Changes pushed to GitHub. Deployment to Railway should start automatically."
