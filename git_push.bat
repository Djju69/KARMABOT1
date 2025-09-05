@echo off
chcp 65001 >nul
echo Starting Git operations...

echo.
echo 1. Checking Git status...
git status

echo.
echo 2. Adding all files...
git add .

echo.
echo 3. Committing changes...
git commit -m "feat: Добавлены новые сервисы и эндпоинты

- Реферальная система (referral_service.py)
- Профили пользователей (profile_service.py) 
- Геопоиск с Haversine формулой
- 3 боевых админ эндпоинта
- Пользовательские API эндпоинты
- Мониторинг (Prometheus + Grafana)
- Unit и integration тесты
- Миграции БД"

echo.
echo 4. Pushing to remote...
git push origin main

echo.
echo Git operations completed!
pause
