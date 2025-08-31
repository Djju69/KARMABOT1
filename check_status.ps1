# Simple status check script
Write-Host "🚀 Checking KarmaBot deployment status"

# Check if Railway CLI is installed
$railwayCli = $null -ne (Get-Command railway -ErrorAction SilentlyContinue)

if ($railwayCli) {
    Write-Host "✅ Railway CLI is installed"
    railway status
} else {
    Write-Host "ℹ Railway CLI not found. Install with: npm install -g @railway/cli"
}

Write-Host "`n📊 Open Railway dashboard: https://railway.app/dashboard"
