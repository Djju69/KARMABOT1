# KarmaBot Deployment Script for Windows
# Run this script to deploy changes to Railway

# Stop on error
$ErrorActionPreference = "Stop"

# Colors for output
$Green = "`e[0;32m"
$Yellow = "`e[1;33m"
$Red = "`e[0;31m"
$NoColor = "`e[0m"

Write-Host "`n${Yellow}🚀 Starting KarmaBot deployment to Railway...${NoColor}`n"

# Step 1: Check for uncommitted changes
$status = git status --porcelain
if ($status) {
    Write-Host "${Yellow}⚠️  Warning: You have uncommitted changes.${NoColor}"
    git status
    $proceed = Read-Host "Do you want to proceed with deployment? (y/N)"
    if ($proceed -ne "y") {
        Write-Host "${Red}✖ Deployment cancelled.${NoColor}"
        exit 1
    }
}

# Step 2: Get current branch
$currentBranch = git rev-parse --abbrev-ref HEAD
if ($currentBranch -ne "main") {
    Write-Host "${Yellow}⚠️  Warning: You're not on the main branch. Current branch: $currentBranch${NoColor}"
    $proceed = Read-Host "Do you want to continue deploying from $currentBranch? (y/N)"
    if ($proceed -ne "y") {
        Write-Host "${Red}✖ Deployment cancelled.${NoColor}"
        exit 1
    }
}

# Step 3: Pull latest changes
Write-Host "`n${Green}🔄 Pulling latest changes...${NoColor}"
git pull origin $currentBranch

# Step 4: Add and commit changes
Write-Host "`n${Green}💾 Committing changes...${NoColor}"
git add .
$commitMessage = "chore: Auto-deploy $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
$commitOutput = git commit -m $commitMessage 2>&1

if ($LASTEXITCODE -ne 0) {
    if ($commitOutput -match "nothing to commit") {
        Write-Host "${Yellow}ℹ No changes to commit.${NoColor}"
    } else {
        Write-Host "${Red}❌ Error committing changes:${NoColor}"
        Write-Host $commitOutput
        exit 1
    }
}

# Step 5: Push to GitHub
Write-Host "`n${Green}🚀 Pushing to GitHub...${NoColor}"
git push origin $currentBranch

# Step 6: Show deployment info
Write-Host "`n${Green}✅ Deployment initiated!${NoColor}`n"

Write-Host "Next steps:"
Write-Host "1. Monitor deployment in Railway Dashboard"
Write-Host "2. Check health endpoint: https://your-project.railway.app/api/health"
Write-Host "3. Test bot functionality"

Write-Host "`n${Yellow}🔍 To view logs, run:${NoColor}"
Write-Host "railway logs"

Write-Host "`n${Green}🎉 Deployment process started!${NoColor}"
