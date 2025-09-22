@echo off
git add core/database/migrations.py
git commit -m "Исправление загрузки каталогов: добавлено создание таблиц cards_v2 и card_photos"
git push origin main
echo Done!
