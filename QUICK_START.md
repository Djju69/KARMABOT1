# 🚀 Быстрый старт: Деплой на Railway

## 1. Запуск деплоя

```powershell
# В папке проекта
.\deploy.ps1
```

## 2. Настройка в Railway Dashboard

1. Перейдите в [Railway Dashboard](https://railway.app/dashboard)
2. Создайте новый проект
3. Выберите "Deploy from GitHub repo"
4. Подключите репозиторий: `Djju69/KARMABOT1`
5. Выберите ветку: `main`

## 3. Настройка переменных окружения

В Railway Dashboard перейдите в раздел Variables и добавьте:

```
BOT_TOKEN=8201307288:AAHB0hdPKXLsd0a6MR4klgtNEM5p46kEmr4
ADMIN_ID=6391215556
ENVIRONMENT=production
LOG_LEVEL=INFO
APP_VERSION=1.0.0
```

## 4. Проверка деплоя

```powershell
.\verify_deployment.ps1
```

## 5. Тестирование

1. Откройте Telegram
2. Найдите своего бота
3. Отправьте команду `/start`

## 🔍 Где смотреть логи

- В Railway Dashboard: Projects → Your Project → Logs
- Или через CLI: `railway logs`

## 🛠 Устранение неполадок

### Деплой не запускается
- Проверьте логи в Railway Dashboard
- Убедитесь, что все переменные окружения установлены
- Проверьте подключение к GitHub

### Бот не отвечает
- Проверьте `BOT_TOKEN`
- Убедитесь, что бот активирован в @BotFather
- Проверьте логи на наличие ошибок

### Проблемы с базой данных
- Убедитесь, что `DATABASE_URL` установлен
- Проверьте логи миграций

## 📞 Поддержка

Если возникли проблемы, проверьте:
1. Логи в Railway Dashboard
2. [Документацию Railway](https://docs.railway.app/)
3. Откройте issue в репозитории
