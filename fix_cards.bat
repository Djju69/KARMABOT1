@echo off
git add core/handlers/category_handlers_v2.py
git commit -m "Исправление отображения карточек - показывать по 5 карточек на страницу с индивидуальными кнопками"
git push origin main
echo Готово!
pause
