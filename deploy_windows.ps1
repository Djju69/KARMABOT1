# Stop any running Python processes
Write-Host "=== Stopping any running Python processes..."
Get-Process python* | Stop-Process -Force -ErrorAction SilentlyContinue

# Kill processes on port 8000 and 8080
Write-Host "=== Freeing up ports 8000 and 8080..."
$ports = @(8000, 8080)
foreach ($port in $ports) {
    $process = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($process) {
        $process | ForEach-Object { 
            $processId = $_.OwningProcess
            Stop-Process -Id $processId -Force
            Write-Host "Killed process $processId on port $port"
        }
    }
}

# Validate configuration
Write-Host "`n=== Validating configuration..."
python validate_config.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Configuration validation failed" -ForegroundColor Red
    exit 1
}

# Fix common issues
Write-Host "`n=== Fixing common issues..."
python fix_deployment.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Failed to fix common issues" -ForegroundColor Red
    exit 1
}

# Install dependencies
Write-Host "`n=== Installing dependencies..."
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Failed to install dependencies" -ForegroundColor Red
    exit 1
}

# Start the server in the background
Write-Host "`n=== Starting test server..."
$serverProcess = Start-Process -NoNewWindow -PassThru -FilePath "python" -ArgumentList "-m uvicorn web.minimal:app --host 0.0.0.0 --port 8000"

# Wait for server to start
Start-Sleep -Seconds 5

# Test health check
Write-Host "`n=== Testing health check..."
python test_health_check.py
$healthCheckResult = $LASTEXITCODE

# Stop the test server
Stop-Process -Id $serverProcess.Id -Force

if ($healthCheckResult -ne 0) {
    Write-Host "[ERROR] Health check failed. Please check the logs above." -ForegroundColor Red
    exit 1
}

# If we got here, everything is working
Write-Host "`n=== All checks passed! Ready to deploy to Railway." -ForegroundColor Green
Write-Host "`nNext steps:"
Write-Host "1. Commit your changes: git add ."
Write-Host "2. Create a commit: git commit -m 'Prepare for deployment'"
Write-Host "3. Push to GitHub: git push origin main"
Write-Host "4. Deploy to Railway: railway up"
Write-Host "`nTo monitor the deployment: railway logs --follow"
