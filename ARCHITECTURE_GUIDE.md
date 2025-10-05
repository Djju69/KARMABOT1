# 🏗️ АРХИТЕКТУРА KARMABOT1 - ПОЛНОЕ ТЗ

## 📋 ОБЩАЯ АРХИТЕКТУРА СИСТЕМЫ

### 🎯 Основные компоненты:
1. **Telegram Bot** (aiogram v3) - основное приложение
2. **База данных** - PostgreSQL (production) / SQLite (development)
3. **Webhook сервер** - встроенный HTTPServer
4. **Multi-platform API** - дополнительный сервис
5. **Redis** - распределенные блокировки (опционально)

---

## 🗄️ АРХИТЕКТУРА БАЗЫ ДАННЫХ

### 📊 Принцип работы:

#### 1. **Адаптер базы данных** (`DatabaseAdapter`)
```python
# Автоматическое переключение между SQLite и PostgreSQL
if database_url.startswith('postgresql://') and is_production:
    self.use_postgresql = True
    self.postgresql_service = PostgreSQLService(database_url)
else:
    self.use_postgresql = False
    self.sqlite_service = DatabaseServiceV2()
```

#### 2. **Два независимых сервиса:**

**SQLite (Development):**
- `DatabaseServiceV2` - локальная база
- Файл: `core/database/data.db`
- Синхронные операции
- Миграции через `DatabaseMigrator`

**PostgreSQL (Production):**
- `PostgreSQLService` - облачная база
- Connection pool с retry логикой
- Асинхронные операции
- Миграции через `ensure_*` функции

#### 3. **Единый интерфейс:**
```python
# Все методы работают одинаково для обеих БД
db_v2.get_partner_by_tg_id(tg_user_id)
db_v2.create_card(card)
db_v2.get_categories()
```

---

## 🔄 СИСТЕМА МИГРАЦИЙ

### 📈 Принцип работы:

#### 1. **Автоматическое определение режима:**
```python
# SQLite миграции
if migrator is not None:
    migrator.run_all_migrations()

# PostgreSQL миграции  
else:
    ensure_partner_applications_table()
    ensure_user_roles_table()
    ensure_partner_tariff_system()
```

#### 2. **Последовательность миграций:**
1. `001` - Legacy таблицы для совместимости
2. `002` - Новая схема партнеров и карточек
3. `003` - Дефолтные категории
4. `004` - Опциональные поля карточек
5. `005` - Система лояльности
6. `013` - Многоуровневая реферальная система
7. `016` - Система кармы
8. `017` - Экосистема партнеров

#### 3. **Безопасность миграций:**
- Advisory locks для PostgreSQL
- Idempotent операции (можно запускать многократно)
- Проверка существования таблиц перед изменением
- Rollback при ошибках

---

## 🌐 WEBHOOK СИСТЕМА

### 🔧 Архитектура:

#### 1. **Встроенный HTTPServer:**
```python
class CustomHTTPRequestHandler(SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/webhook':
            self.handle_webhook_request()
    
    def handle_webhook_request(self):
        # Получаем JSON от Telegram
        update_data = json.loads(post_data.decode('utf-8'))
        
        # Создаём объект Update
        update = Update(**update_data)
        
        # Обрабатываем через диспетчер
        dp_instance.feed_update(bot=bot_instance, update=update)
```

#### 2. **Два режима работы:**

**Production (Webhook):**
- `DISABLE_WEBHOOK=false`
- Telegram отправляет updates на `/webhook`
- Бот работает через webhook
- Встроенный HTTPServer обрабатывает запросы

**Development (Polling):**
- `DISABLE_WEBHOOK=true`
- Бот сам запрашивает updates
- Удаляет webhook перед запуском
- Работает через long polling

#### 3. **Health Check:**
- Endpoint: `/health`
- Возвращает: `OK`
- Используется для мониторинга Railway

---

## 🔐 РАСПРЕДЕЛЕННЫЕ БЛОКИРОВКИ

### 🛡️ Принцип работы:

#### 1. **Redis Leader Lock:**
```python
# Только один экземпляр бота может работать
got_lock = await acquire_leader_lock(redis, lock_key, instance, lock_ttl)
if not got_lock:
    logger.error("❌ Failed to acquire leader lock")
    return
```

#### 2. **Настройки блокировки:**
- `LOCK_TTL = 300` секунд
- `LOCK_KEY = f"production:bot:{BOT_ID}:polling:leader"`
- `INSTANCE = f"{HOSTNAME}:{PID}"`

#### 3. **Graceful shutdown:**
```python
def signal_handler(signum, frame):
    asyncio.create_task(shutdown_handler(None))

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)
```

---

## 🚀 ЗАПУСК И ИНИЦИАЛИЗАЦИЯ

### 📋 Последовательность запуска:

#### 1. **Инициализация окружения:**
```python
# Проверка переменных окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
REDIS_URL = os.getenv("REDIS_URL")
```

#### 2. **Инициализация базы данных:**
```python
# Автоматическое определение типа БД
ensure_database_ready()

# Запуск миграций
if migrator:
    migrator.run_all_migrations()
else:
    ensure_partner_applications_table()
    ensure_user_roles_table()
```

#### 3. **Инициализация бота:**
```python
async with Bot(token=BOT_TOKEN) as bot:
    # Установка команд
    await set_commands(bot)
    
    # Проверка Redis
    if redis:
        await redis.ping()
    
    # Получение блокировки
    if redis:
        got_lock = await acquire_leader_lock(...)
```

#### 4. **Запуск webhook/polling:**
```python
if DISABLE_WEBHOOK:
    # Development: polling
    await dp.start_polling(bot)
else:
    # Production: webhook
    await bot.set_webhook(url=WEBHOOK_URL)
    
    # Запуск web сервера
    web_thread = threading.Thread(target=start_web_server, args=(bot, dp))
    web_thread.start()
    
    # Keep running
    await asyncio.Future()
```

---

## 🔧 КОНФИГУРАЦИЯ

### ⚙️ Переменные окружения:

#### **Обязательные:**
- `BOT_TOKEN` - токен Telegram бота
- `DATABASE_URL` - URL базы данных
- `WEBHOOK_URL` - URL для webhook

#### **Опциональные:**
- `DISABLE_WEBHOOK` - отключить webhook (для тестирования)
- `REDIS_URL` - URL Redis для блокировок
- `API_PORT` - порт web сервера (по умолчанию 8080)
- `APPLY_MIGRATIONS` - применить миграции (по умолчанию 0)
- `SKIP_MIGRATIONS` - пропустить миграции

#### **Railway специфичные:**
- `RAILWAY_ENVIRONMENT` - окружение Railway
- `RAILWAY_STATIC_URL` - статический URL Railway

---

## 🎯 ОСНОВНЫЕ ФУНКЦИИ

### 📱 Telegram Bot функции:

#### 1. **Пользовательские функции:**
- Регистрация и авторизация
- Просмотр карточек партнеров
- Система лояльности и кармы
- Реферальная система
- Избранное и история

#### 2. **Партнерские функции:**
- Регистрация партнера
- Создание и редактирование карточек
- Управление тарифами
- Статистика и аналитика

#### 3. **Административные функции:**
- Модерация контента
- Управление пользователями
- Системные настройки
- Мониторинг

---

## 🔄 MULTI-PLATFORM API

### 🌐 Дополнительный сервис:

#### 1. **Отдельный процесс:**
```python
# Запускается в отдельном процессе
subprocess.Popen(["python", "multiplatform/main_api.py"])
```

#### 2. **Порт 8001:**
- Независимый от основного бота
- Собственная база данных
- API для внешних платформ

#### 3. **Интеграция:**
- Общие данные с основным ботом
- Синхронизация через Supabase
- Fault-tolerant операции

---

## 🛡️ БЕЗОПАСНОСТЬ И НАДЕЖНОСТЬ

### 🔒 Принципы:

#### 1. **Fault Tolerance:**
- Retry логика для БД операций
- Graceful degradation при ошибках
- Connection pooling для PostgreSQL

#### 2. **Error Handling:**
- Логирование всех ошибок
- Продолжение работы при не критичных ошибках
- Автоматический rollback при миграциях

#### 3. **Resource Management:**
- Proper connection cleanup
- Memory management для SQLite
- Thread-safe операции

---

## 📊 МОНИТОРИНГ И ЛОГИРОВАНИЕ

### 📈 Система логирования:

#### 1. **Уровни логов:**
- `INFO` - обычные операции
- `WARNING` - предупреждения
- `ERROR` - ошибки
- `DEBUG` - отладочная информация

#### 2. **Ключевые события:**
- Запуск/остановка бота
- Миграции базы данных
- Webhook события
- Ошибки обработки

#### 3. **Мониторинг:**
- Health check endpoint
- Railway logs
- Database health monitoring
- Redis connection status

---

## 🎯 ЗАКЛЮЧЕНИЕ

### ✅ Система работает по принципу:

1. **Автоматическое определение окружения** (dev/prod)
2. **Единый интерфейс** для всех операций с БД
3. **Fault-tolerant архитектура** с retry логикой
4. **Graceful degradation** при ошибках
5. **Масштабируемость** через Redis блокировки
6. **Мониторинг** через health checks и логи

### 🚀 Результат:
- **Стабильная работа** в production
- **Простое тестирование** в development
- **Автоматические миграции** при обновлениях
- **Надежная обработка** webhook событий
- **Масштабируемость** для множественных экземпляров
