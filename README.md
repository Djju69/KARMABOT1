# Karma System Bot

## Обновление до aiogram v3

### Основные изменения

1. **Новая структура настроек**:
   - Унифицированный класс `Settings` в `core/config.py`
   - Поддержка переменных окружения с префиксом `BOTS__`
   - Автоматическая загрузка `.env` только в режиме разработки

2. **Обновленные обработчики**:
   - Совместимость с aiogram v3
   - Улучшенная обработка ошибок
   - Поддержка старых и новых сигнатур хэндлеров

3. **Новые возможности**:
   - Улучшенное логирование
   - Более надежная обработка команд
   - Поддержка FSM из коробки

## Настройка окружения

### Проверка переменных окружения

Перед запуском убедитесь, что все необходимые переменные окружения установлены корректно:

```bash
# Проверка переменных окружения
printenv | grep -i -E 'BOTS__BOT_TOKEN|BOT_TOKEN|TELEGRAM_TOKEN|ENVIRONMENT'

# Проверка токена бота
python -c "import os; print('BOTS__BOT_TOKEN =', repr(os.getenv('BOTS__BOT_TOKEN')))"

# Проверка доступа к Telegram API
curl -s "https://api.telegram.org/bot${BOTS__BOT_TOKEN}/getMe"
```

Ожидаемый вывод:
- `BOTS__BOT_TOKEN` должен быть установлен
- `BOT_TOKEN` и `TELEGRAM_TOKEN` не должны быть установлены (если есть - удалите их)
- Запрос к API должен вернуть `{"ok":true,...}`

### Файлы окружения

#### .env (для разработки)
```env
BOTS__BOT_TOKEN=your_bot_token_here
BOTS__ADMIN_ID=6391215556
ENVIRONMENT=development
FEATURES__BOT_ENABLED=1
FEATURES__PARTNER_FSM=0
FEATURES__MODERATION=0
```

#### Настройки Railway/Production
```env
BOTS__BOT_TOKEN=your_production_token
ENVIRONMENT=production
FEATURES__BOT_ENABLED=1
```

## Запуск

1. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```

2. Запустите бота:
   ```bash
   python main_v2.py
   ```

## Тестирование

Запустите тесты для проверки работоспособности:

```bash
python -m pytest tests/test_imports.py -v
```

## Обратная совместимость

Для поддержки старых обработчиков используется модуль `core.compat`:
- `@compat_handler` - декоратор для старых хэндлеров
- `call_compat()` - функция для вызова старых обработчиков
- Автоматические алиасы для устаревших имен функций

## Проверка работы

1. Проверьте логи на наличие сообщения о успешной авторизации:
   ```
   ✅ Bot authorized: @your_bot_username (id=...)
   ```

2. Убедитесь, что токен в логах маскируется (начинается с 8 символов, затем многоточие):
   ```
   🔑 Using bot token: 83635304…
   ```

## Устранение неполадок

Если бот не запускается:
1. Проверьте, что переменная `BOTS__BOT_TOKEN` установлена и корректна
2. Убедитесь, что нет конфликтующих переменных (`BOT_TOKEN`, `TELEGRAM_TOKEN`)
3. Проверьте доступность API Telegram с вашего сервера
4. Проверьте логи на наличие ошибок авторизации
