@echo off
echo 🔧 ИСПРАВЛЕНИЕ И ДЕПЛОЙ
echo ======================

echo 📋 Добавление исправления...
git add main_v2.py

echo.
echo 💾 Создание коммита исправления...
git commit -m "🔧 Исправление ошибки Settings.bots.bot_token

❌ Проблема: AttributeError: 'Settings' object has no attribute 'bots'
✅ Решение: Изменено settings.bots.bot_token на settings.bot_token
🚀 Основной бот теперь должен запускаться без ошибок"

echo.
echo 🚀 Пуш исправления...
git push origin main

echo.
echo ✅ Исправление отправлено!
echo 🤖 Основной бот должен заработать

pause
