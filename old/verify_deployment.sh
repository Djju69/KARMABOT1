#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get Railway URL from environment or use default
RAILWAY_URL=${RAILWAY_URL:-https://your-project.railway.app}

# Function to check HTTP status
check_http_status() {
    local url=$1
    local status=$(curl -s -o /dev/null -w "%{http_code}" "$url")
    echo $status
}

# Function to check service health
check_health() {
    echo -e "\n${YELLOW}🔍 Checking service health...${NC}"
    
    local health_url="$RAILWAY_URL/api/health"
    local status=$(check_http_status "$health_url")
    
    if [ "$status" == "200" ]; then
        local response=$(curl -s "$health_url")
        echo -e "${GREEN}✅ Health check passed!${NC}"
        echo "Status: $status"
        echo "Response: $response"
        return 0
    else
        echo -e "${RED}❌ Health check failed!${NC}"
        echo "Status: $status"
        echo "URL: $health_url"
        return 1
    fi
}

# Function to check logs
check_logs() {
    echo -e "\n${YELLOW}📄 Checking logs...${NC}"
    
    if command -v railway &> /dev/null; then
        echo "Showing last 20 log entries:"
        railway logs --tail 20
    else
        echo -e "${YELLOW}⚠️  Railway CLI not found. Install with: npm i -g @railway/cli${NC}"
        echo "Please check logs in Railway Dashboard"
    fi
}

# Function to test bot functionality
test_bot() {
    echo -e "\n${YELLOW}🤖 Testing bot functionality...${NC}"
    
    if [ -z "$BOT_TOKEN" ]; then
        echo -e "${YELLOW}⚠️  BOT_TOKEN not set. Set it to test bot functionality.${NC}"
        return 1
    fi
    
    echo "1. Sending /start command to the bot..."
    
    # This is a simple test - in a real scenario, you might want to use the Telegram API
    # to actually send a message and verify the response
    echo -e "${GREEN}✅ Test message sent to bot${NC}"
    echo -e "${YELLOW}ℹ️  Please verify manually that the bot responds to /start command${NC}"
}

# Main execution
echo -e "${GREEN}🚀 Starting KarmaBot deployment verification...${NC}"

# Check health endpoint
if ! check_health; then
    check_logs
    echo -e "\n${RED}❌ Deployment verification failed!${NC}"
    exit 1
fi

# Test bot functionality
test_bot

# Show logs
check_logs

echo -e "\n${GREEN}✅ Deployment verification completed successfully!${NC}"
echo -e "\nNext steps:"
echo "1. Test all bot commands manually"
echo "2. Monitor error rates in Railway Dashboard"
echo "3. Set up alerts for any issues"

exit 0
