param(
  [string]$BaseUrl = "http://127.0.0.1:8084",
  [string]$Secret = "test_secret"
)

function Write-Section([string]$title) {
  Write-Host ("`n=== {0} ===" -f $title) -ForegroundColor Cyan
}

function Invoke-Json($method, $url, $headers=@{}, $body=$null) {
  try {
    if ($body -ne $null -and -not ($body -is [string])) { $body = ($body | ConvertTo-Json -Compress) }
    return Invoke-RestMethod -Method $method -Uri $url -Headers $headers -Body $body
  } catch {
    $resp = $_.Exception.Response
    if ($resp) { $sr = New-Object IO.StreamReader($resp.GetResponseStream()); $txt = $sr.ReadToEnd(); Write-Host $txt -ForegroundColor Yellow }
    else { Write-Host $_ -ForegroundColor Red }
    return $null
  }
}

Write-Host ('SMOKE: BaseUrl={0}' -f $BaseUrl) -ForegroundColor Green

# A. Health
Write-Section 'A. Health'
Write-Host 'A1: GET /healthz' -ForegroundColor Green
$h = Invoke-Json GET "$BaseUrl/healthz"
if ($h) { Write-Host ( $h | ConvertTo-Json -Compress ) }

Write-Host 'A2: GET /health' -ForegroundColor Green
$h2 = Invoke-Json GET "$BaseUrl/health"
if ($h2) { Write-Host ( $h2 | ConvertTo-Json -Compress ) }

Write-Host 'A3: /metrics (first 10 lines)' -ForegroundColor Green
try { (Invoke-WebRequest "$BaseUrl/metrics").Content -split "`n" | Select-Object -First 10 | ForEach-Object { $_.TrimEnd() } | ForEach-Object { Write-Host $_ } } catch { Write-Host $_ -ForegroundColor Yellow }

# B. /auth/me (smoke) — без реального JWT ожидаем 401
Write-Section 'B. /auth/me'
$me = $null
try { $me = Invoke-WebRequest "$BaseUrl/auth/me" -Headers @{ Authorization = 'Bearer invalid' } -Method GET } catch { Write-Host 'Expected 401/403 if JWT not configured' -ForegroundColor Yellow }

# F. Webhook ui.refresh_menu
Write-Section 'F. Webhook'
Write-Host 'F1: webhook /bot/hooks/ui.refresh_menu -> 200 then 429' -ForegroundColor Green
$body = @{ user_id = 123; reason = "manual" } | ConvertTo-Json -Compress
$ts      = [int][DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
$bytesTs = [Text.Encoding]::UTF8.GetBytes("$ts")
$payload = [byte[]]($bytesTs + [Text.Encoding]::UTF8.GetBytes('.') + [Text.Encoding]::UTF8.GetBytes($body))
$hmac    = [System.Security.Cryptography.HMACSHA256]::new([Text.Encoding]::UTF8.GetBytes($Secret))
$sig     = 'sha256=' + (($hmac.ComputeHash($payload) | ForEach-Object ToString x2) -join '')

$ok = Invoke-Json POST "$BaseUrl/bot/hooks/ui.refresh_menu" @{ 'X-Karma-Timestamp'="$ts"; 'X-Karma-Signature'=$sig; 'Content-Type'='application/json' } $body
if ($ok) { Write-Host ( $ok | ConvertTo-Json -Compress ) }

$dup = Invoke-Json POST "$BaseUrl/bot/hooks/ui.refresh_menu" @{ 'X-Karma-Timestamp'="$ts"; 'X-Karma-Signature'=$sig; 'Content-Type'='application/json' } $body

# C/D/E optional checks (placeholders)
Write-Section 'C. QR (optional)'
try {
  Write-Host 'C: Skipping QR checks (endpoints not implemented in this build)' -ForegroundColor Yellow
} catch { }

Write-Section 'D. Cache invalidation (optional)'
try {
  Write-Host 'D: Skipping explicit invalidation checks (requires specific API)' -ForegroundColor Yellow
} catch { }

Write-Section 'E. Reports RL (optional)'
try {
  Write-Host 'E: Skipping reports RL checks (requires /reports API)' -ForegroundColor Yellow
} catch { }

# G. i18n (optional)
Write-Section 'G. i18n (optional)'
try {
  $r = Invoke-Json GET "$BaseUrl/i18n/keys"
  if ($r) { Write-Host ('i18n keys: {0}' -f (($r.keys | Select-Object -First 5) -join ', ')) }
} catch { Write-Host "Skip i18n check" -ForegroundColor Yellow }

# STATE file check
Write-Section 'SESSION_STATE'
$statePath = Join-Path $PSScriptRoot "..\ops\SESSION_STATE.json"
if (Test-Path $statePath) {
  $content = Get-Content $statePath -Raw
  $preview = $content.Substring(0, [Math]::Min($content.Length, 400))
  Write-Host $preview
} else {
  Write-Host ('Not found: {0}' -f $statePath) -ForegroundColor Yellow
}
