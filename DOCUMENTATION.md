# KarmaSystemBot - Документация

## 🧪 Тестирование

### Запуск тестов локально

1. Установите зависимости:
```bash
pip install -r requirements.txt
pip install pytest pytest-cov pytest-asyncio
```

2. Настройте тестовую базу данных PostgreSQL

3. Запустите тесты:
```bash
DATABASE_URL=postgresql://user:password@localhost:5432/test_db TESTING=1 pytest tests/ -v
```

### Структура тестов

- `tests/integration/` - интеграционные тесты
  - `test_admin_*.py` - тесты админ-панели
  - `test_handlers.py` - тесты обработчиков
- `tests/unit/` - юнит-тесты

### Добавление новых тестов

1. Создайте тестовый класс, унаследованный от `BaseBotTest`
2. Используйте `AsyncMock` для мокирования асинхронных вызовов
3. Проверяйте как успешные сценарии, так и обработку ошибок

## 🚀 Деплой

### Переменные окружения

Создайте файл `.env` со следующими переменными:

```env
DATABASE_URL=postgresql://user:password@host:port/dbname
BOT_TOKEN=your_telegram_bot_token
ADMIN_IDS=12345,67890
```

### Staging

1. Настройте подключение к базе данных
2. Запустите миграции:
```bash
python -m alembic upgrade head
```
3. Запустите бота:
```bash
python main_v2.py
```

### Production

1. Создайте тег релиза:
```bash
git tag -a v1.0.0 -m "Production release"
git push origin v1.0.0
```

2. Запустите деплой (пример для Railway):
```bash
railway up --service bot
```

## 🔧 Troubleshooting

### Частые проблемы

1. **Ошибки подключения к БД**
   - Проверьте строку подключения
   - Убедитесь, что БД доступна

2. **Проблемы с правами доступа**
   - Проверьте `ADMIN_IDS`
   - Убедитесь, что пользователь добавлен в админы

### Логи

Логи хранятся в `logs/bot.log`

### Откат

1. Откатитесь к предыдущему тегу:
```bash
git checkout v0.9.0
```
2. Перезапустите сервис

## 📊 Мониторинг

### Метрики

- Доступность сервиса
- Время ответа
- Количество ошибок
- Использование ресурсов

### Alerting

- Ошибки 5xx
- Response time > 1000ms
- Memory usage > 80%
