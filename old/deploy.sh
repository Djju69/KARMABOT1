#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🚀 Starting KarmaBot deployment to Railway...${NC}\n"

# Step 1: Check for uncommitted changes
if ! git diff --quiet && git diff --cached --quiet; then
    echo -e "${YELLOW}⚠️  Warning: You have uncommitted changes. Please commit or stash them before deploying.${NC}"
    git status
    exit 1
fi

# Step 2: Get current branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$CURRENT_BRANCH" != "main" ]; then
    echo -e "${YELLOW}⚠️  Warning: You're not on the main branch. Current branch: $CURRENT_BRANCH${NC}"
    read -p "Do you want to continue deploying from $CURRENT_BRANCH? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}✖ Deployment cancelled.${NC}"
        exit 1
    fi
fi

# Step 3: Pull latest changes
echo -e "\n${GREEN}🔄 Pulling latest changes...${NC}"
git pull origin $CURRENT_BRANCH

# Step 4: Add and commit changes
echo -e "\n${GREEN}💾 Committing changes...${NC}"
git add .
git commit -m "chore: Auto-deploy $(date +'%Y-%m-%d %H:%M:%S')" || {
    echo -e "${YELLOW}ℹ No changes to commit.${NC}"
}

# Step 5: Push to GitHub
echo -e "\n${GREEN}🚀 Pushing to GitHub...${NC}"
git push origin $CURRENT_BRANCH

# Step 6: Show deployment info
echo -e "\n${GREEN}✅ Deployment initiated!${NC}\n"
echo -e "Next steps:"
echo "1. Monitor deployment in Railway Dashboard"
echo "2. Check health endpoint: https://your-project.railway.app/api/health"
echo "3. Test bot functionality"

echo -e "\n${YELLOW}🔍 To view logs, run:${NC}"
echo "railway logs"

echo -e "\n${GREEN}🎉 Deployment process started!${NC}"
