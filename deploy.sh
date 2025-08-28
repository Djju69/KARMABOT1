#!/bin/bash
set -e

echo "🚀 Starting deployment..."

# Install Railway CLI if not exists
if ! command -v railway &> /dev/null; then
    echo "🔧 Installing Railway CLI..."
    npm install -g @railway/cli@2.0.5
fi

# Login to Railway
echo "🔑 Logging in to Railway..."
echo $RAILWAY_TOKEN | railway login --ci

# Set project if specified
if [ -n "$RAILWAY_PROJECT" ]; then
    echo "🔗 Linking project $RAILWAY_PROJECT..."
    railway link $RAILWAY_PROJECT
fi

# Set environment if specified
if [ -n "$RAILWAY_ENVIRONMENT" ]; then
    echo "🌍 Switching to environment $RAILWAY_ENVIRONMENT..."
    railway environment switch $RAILWAY_ENVIRONMENT
fi

# Step 1: First deploy with polling disabled
echo "🔄 Step 1/2: Initial deploy with polling disabled"
railway variables set DISABLE_POLLING=1 FEATURE_PARTNER_FSM=true --yes

# Set Redis URL if provided
if [ -n "$REDIS_URL" ]; then
    railway variables set REDIS_URL="$REDIS_URL" --yes
fi

# First deploy
railway up --detach

# Step 2: Final deploy with polling enabled
echo "🚀 Step 2/2: Final deploy with polling enabled"
railway variables set DISABLE_POLLING=0 --yes

# Set polling leader lock if provided
if [ -n "$ENABLE_POLLING_LEADER_LOCK" ]; then
    railway variables set ENABLE_POLLING_LEADER_LOCK="$ENABLE_POLLING_LEADER_LOCK" --yes
fi

# Final deploy
railway up --detach

echo "✅ Deployment completed successfully!"
SERVICE_URL=$(railway status --json | jq -r '.service.privateDomain' 2>/dev/null || echo "unknown")
echo "🌐 Service URL: $SERVICE_URL"
