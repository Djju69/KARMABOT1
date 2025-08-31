# Simple deployment check script

# Set the Railway URL - replace with your actual Railway URL
$railwayUrl = "https://your-project.railway.app"

# Check if curl is available
$curlAvailable = $null -ne (Get-Command curl -ErrorAction SilentlyContinue)

# Function to check health endpoint
function Check-Health {
    param (
        [string]$url
    )
    
    Write-Host "Checking health at: $url"
    
    try {
        if ($curlAvailable) {
            $response = curl -s -o $null -w "%{http_code}" $url
            $status = [int]$response
            
            if ($status -eq 200) {
                Write-Host "✅ Health check passed (Status: $status)" -ForegroundColor Green
                return $true
            } else {
                Write-Host "❌ Health check failed (Status: $status)" -ForegroundColor Red
                return $false
            }
        } else {
            $response = Invoke-WebRequest -Uri $url -UseBasicParsing -ErrorAction Stop
            if ($response.StatusCode -eq 200) {
                Write-Host "✅ Health check passed (Status: $($response.StatusCode))" -ForegroundColor Green
                return $true
            } else {
                Write-Host "❌ Health check failed (Status: $($response.StatusCode))" -ForegroundColor Red
                return $false
            }
        }
    } catch {
        Write-Host "❌ Error checking health: $_" -ForegroundColor Red
        return $false
    }
}

# Main execution
Write-Host "🚀 Checking KarmaBot deployment status" -ForegroundColor Cyan

# Check if Railway CLI is installed
$railwayCli = $null -ne (Get-Command railway -ErrorAction SilentlyContinue)

if ($railwayCli) {
    Write-Host "ℹ Railway CLI is installed" -ForegroundColor Green
    Write-Host "📋 Checking deployment status..."
    railway status
} else {
    Write-Host "ℹ Railway CLI not found. Install with: npm install -g @railway/cli" -ForegroundColor Yellow
}

# Check health endpoint
$healthUrl = "$railwayUrl/api/health"
Write-Host "`n🔍 Checking health endpoint: $healthUrl"
$healthOk = Check-Health -url $healthUrl

# Final status
if ($healthOk) {
    Write-Host "`n🎉 Deployment appears to be healthy!" -ForegroundColor Green
    Write-Host "   You can test the bot by sending a /start command in Telegram" -ForegroundColor Green
} else {
    Write-Host "`n⚠️  There might be an issue with the deployment" -ForegroundColor Yellow
    Write-Host "   Check the logs in the Railway dashboard for more details" -ForegroundColor Yellow
}

Write-Host "`n📊 Open Railway dashboard: https://railway.app/dashboard" -ForegroundColor Cyan
