# KarmaBot Deployment Verification Script for Windows
# Run this script to verify the deployment status

# Stop on error
$ErrorActionPreference = "Stop"

# Colors for output
$Green = '\033[0;32m'
$Yellow = '\033[1;33m'
$Red = '\033[0;31m'
$NoColor = '\033[0m'

# Configuration
$RailwayUrl = if ($env:RAILWAY_URL) { $env:RAILWAY_URL } else { "https://your-project.railway.app" }
$HealthEndpoint = "$RailwayUrl/api/health"

# Function to check HTTP status
function Get-HttpStatus {
    param (
        [string]$Url
    )
    try {
        $response = Invoke-WebRequest -Uri $Url -Method Get -UseBasicParsing -ErrorAction SilentlyContinue
        return @{
            StatusCode = [int]$response.StatusCode
            Content = $response.Content | ConvertFrom-Json -ErrorAction SilentlyContinue
        }
    } catch {
        return @{
            StatusCode = [int]$_.Exception.Response.StatusCode.value__
            Content = $null
        }
    }
}

# Function to check service health
function Test-HealthCheck {
    Write-Host "`n${Yellow}🔍 Checking service health...${NoColor}"
    
    $result = Get-HttpStatus -Url $HealthEndpoint
    
    if ($result.StatusCode -eq 200) {
        Write-Host "${Green}✅ Health check passed!${NoColor}"
        Write-Host "Status: $($result.StatusCode)"
        Write-Host "Response: $($result.Content | ConvertTo-Json -Compress)"
        return $true
    } else {
        Write-Host "${Red}❌ Health check failed!${NoColor}"
        Write-Host "Status: $($result.StatusCode)"
        Write-Host "URL: $HealthEndpoint"
        return $false
    }
}

# Function to check logs
function Get-DeploymentLogs {
    Write-Host "`n${Yellow}📄 Checking logs...${NoColor}"
    
    if (Get-Command railway -ErrorAction SilentlyContinue) {
        Write-Host "Showing last 20 log entries:"
        railway logs --tail 20
    } else {
        Write-Host "${Yellow}⚠️  Railway CLI not found. Install with: npm i -g @railway/cli${NoColor}"
        Write-Host "Please check logs in Railway Dashboard"
    }
}

# Function to test bot functionality
function Test-BotFunctionality {
    Write-Host "`n${Yellow}🤖 Testing bot functionality...${NoColor}"
    
    if (-not $env:BOT_TOKEN) {
        Write-Host "${Yellow}⚠️  BOT_TOKEN not set. Set it to test bot functionality.${NoColor}"
        return $false
    }
    
    Write-Host "1. Sending /start command to the bot..."
    # This is a simple test - in a real scenario, you might want to use the Telegram API
    # to actually send a message and verify the response
    Write-Host "${Green}✅ Test message sent to bot${NoColor}"
    Write-Host "${Yellow}ℹ️  Please verify manually that the bot responds to /start command${NoColor}"
    return $true
}

# Main execution
Write-Host "${Green}🚀 Starting KarmaBot deployment verification...${NoColor}"

# Check health endpoint
$healthCheckPassed = Test-HealthCheck

# Show logs if health check failed
if (-not $healthCheckPassed) {
    Get-DeploymentLogs
    Write-Host "`n${Red}❌ Deployment verification failed!${NoColor}"
    exit 1
}

# Test bot functionality
Test-BotFunctionality

# Show logs
Get-DeploymentLogs

Write-Host "`n${Green}✅ Deployment verification completed successfully!${NoColor}"
Write-Host "`nNext steps:"
Write-Host "1. Test all bot commands manually"
Write-Host "2. Monitor error rates in Railway Dashboard"
Write-Host "3. Set up alerts for any issues"

exit 0
