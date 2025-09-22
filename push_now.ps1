Write-Host "Добавляем файлы..."
git add core/security/roles.py core/settings.py

Write-Host "Коммитим..."
git commit -m "Исправление ролей пользователей - добавлен супер-админ и партнер"

Write-Host "Пушим..."
git push origin main

Write-Host "Готово!"
