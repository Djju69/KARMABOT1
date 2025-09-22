@echo off
git add core/services/help_service.py
git add core/database/migrations.py
git commit -m "Исправление ошибок: HelpService Role.USER и создание таблицы card_photos"
git push origin main
echo Done!
