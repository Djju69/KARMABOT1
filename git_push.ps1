# PowerShell script for Git operations
Write-Host "Starting Git operations..." -ForegroundColor Green

Write-Host "`n1. Checking Git status..." -ForegroundColor Yellow
git status

Write-Host "`n2. Adding all files..." -ForegroundColor Yellow
git add .

Write-Host "`n3. Committing changes..." -ForegroundColor Yellow
git commit -m "feat: Добавлены новые сервисы и эндпоинты

- Реферальная система (referral_service.py)
- Профили пользователей (profile_service.py) 
- Геопоиск с Haversine формулой
- 3 боевых админ эндпоинта
- Пользовательские API эндпоинты
- Мониторинг (Prometheus + Grafana)
- Unit и integration тесты
- Миграции БД"

Write-Host "`n4. Pushing to remote..." -ForegroundColor Yellow
git push origin main

Write-Host "`nGit operations completed!" -ForegroundColor Green
Read-Host "Press Enter to continue"
