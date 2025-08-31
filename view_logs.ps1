# Скрипт для просмотра логов Railway
# Использование: .\view_logs.ps1 [количество_строк]

param(
    [int]$Lines = 50
)

# Проверяем установлен ли Railway CLI
$railwayCmd = Get-Command railway -ErrorAction SilentlyContinue

if ($null -eq $railwayCmd) {
    Write-Host "🚨 Railway CLI не установлен" -ForegroundColor Red
    Write-Host "Установите его с помощью: npm install -g @railway/cli"
    Write-Host "Или просматривайте логи в Railway Dashboard"
    exit 1
}

# Проверяем авторизацию
$authStatus = railway status 2>&1

if ($authStatus -like "*not logged in*") {
    Write-Host "🔑 Требуется авторизация в Railway CLI" -ForegroundColor Yellow
    railway login
}

# Получаем логи
Write-Host "📋 Последние $Lines строк лога:" -ForegroundColor Green
railway logs --tail $Lines

Write-Host "`n🔍 Для просмотра логов в реальном времени выполните:" -ForegroundColor Cyan
Write-Host "railway logs --follow"
Write-Host "`n🌐 Или откройте логи в браузере:" -ForegroundColor Cyan
Write-Host "https://railway.app/project/ваш-проект/logs"

# Показываем команды для фильтрации логов
Write-Host "`n🔍 Полезные команды для фильтрации логов:" -ForegroundColor Cyan
Write-Host "railway logs | Select-String 'ERROR' -Context 2,2"
Write-Host "railway logs --tail 100 | Out-Host -Paging"
