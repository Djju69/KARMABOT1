# ПОЛНОЕ ТЕХНИЧЕСКОЕ ЗАДАНИЕ: KARMABOT1

## 📋 ОБЩАЯ ИНФОРМАЦИЯ

**Название проекта:** KARMABOT1 - Система лояльности и партнерских скидок  
**Тип:** Telegram Bot + WebApp  
**Дата создания:** 09/07/2025  
**Версия:** 2.0  
**Статус:** В разработке  

## 🎯 ЦЕЛИ И ЗАДАЧИ

### Основные цели
1. **Создать единую платформу** для управления партнерскими скидками
2. **Реализовать систему лояльности** с баллами и транзакциями
3. **Обеспечить удобный интерфейс** для всех типов пользователей
4. **Автоматизировать процессы** модерации и управления
5. **Масштабировать систему** для международного использования

### Ключевые задачи
- ✅ Реализовать базовую функциональность бота
- ✅ Создать систему лояльности и рефералов
- ✅ Настроить базу данных и миграции
- 🚧 Реализовать личные кабинеты
- 🚧 Создать админ-панель
- 🚧 Добавить систему модерации
- 📝 Написать comprehensive тесты
- 📝 Настроить мониторинг

## 🏗️ АРХИТЕКТУРА СИСТЕМЫ

### Технологический стек
```
Backend:
├── Python 3.8+
├── aiogram 3.3.0+ (Telegram Bot API)
├── FastAPI (Web API)
├── SQLAlchemy (ORM)
├── Alembic (Миграции)
└── Pydantic (Валидация данных)

Database:
├── SQLite (Development)
├── PostgreSQL (Production)
└── Redis (Кеширование)

Frontend:
├── Telegram WebApp
├── HTML5/CSS3/JavaScript
└── Responsive Design

Deployment:
├── Docker
├── Railway (Hosting)
├── GitHub Actions (CI/CD)
└── Feature Flags
```

### Структура проекта
```
KARMABOT1-fixed/
├── 📁 bot/                    # Инициализация бота
├── 📁 core/                   # Основная логика
│   ├── 📁 handlers/           # Обработчики событий
│   ├── 📁 keyboards/          # Клавиатуры
│   ├── 📁 services/           # Бизнес-логика
│   ├── 📁 utils/              # Утилиты
│   ├── 📁 middleware/         # Middleware
│   └── 📁 database/           # Работа с БД
├── 📁 web/                    # Web API
├── 📁 tests/                  # Тесты
├── 📁 docs/                   # Документация
├── 📁 migrations/             # Миграции БД
└── 📁 config/                 # Конфигурация
```

## 🗄️ СТРУКТУРА БАЗЫ ДАННЫХ

### Основные таблицы

#### Пользователи
```sql
users:
  - user_id (PK) - Telegram ID
  - username, first_name, last_name
  - language_code - для локализации
  - registration_date
  - is_active, is_partner, is_admin
  - referrer_id (FK users) - кто пригласил
  - loyalty_balance - баланс баллов лояльности
  - privacy_policy_accepted - принятие политики
  - privacy_policy_accepted_at - дата принятия
```

#### Система лояльности
```sql
loyalty_transactions:
  - id (PK)
  - user_id (FK users)
  - amount - сумма баллов (+/-)
  - transaction_type - тип операции
  - description - описание
  - created_at
  - metadata - JSON с доп. данными

loyalty_rules:
  - id (PK) 
  - rule_type - тип правила (visit, referral, review)
  - points_amount - количество баллов
  - conditions - JSON условий
  - is_active
```

#### Реферальная система
```sql
referrals:
  - id (PK)
  - referrer_id (FK users) - кто привел
  - referred_id (FK users) - кого привели
  - referral_code - уникальный код
  - created_at
  - is_active
  - total_earned - всего заработано с этого реферала

referral_earnings:
  - id (PK)
  - referrer_id (FK users)
  - referred_id (FK users) 
  - amount - сумма награды
  - source_transaction_id - исходная транзакция
  - level - уровень реферала (1, 2, 3)
  - created_at
```

#### Партнеры и карточки
```sql
partners_v2:
  - id (PK)
  - user_id (FK users) - владелец
  - business_name - название бизнеса
  - contact_info - JSON контактов
  - verification_status - статус верификации
  - created_at, updated_at

cards_v2:
  - id (PK)
  - partner_id (FK partners_v2)
  - category_id (FK categories_v2) 
  - title, description
  - address, coordinates (lat, lon)
  - images - JSON массив изображений
  - discount_info - информация о скидках
  - working_hours - JSON расписания
  - status (active, moderation, archived)
  - created_at, updated_at

categories_v2:
  - id (PK)
  - name_key - ключ для локализации
  - parent_id (FK categories_v2) - для иерархии
  - icon, color
  - sort_order
```

## 🎨 ПОЛЬЗОВАТЕЛЬСКИЕ ИНТЕРФЕЙСЫ

### Главное меню бота
```
🏠 Главное меню
├── 🗂️ Категории
│   ├── 🍽️ Рестораны
│   ├── 💆 SPA
│   ├── 🏍️ Транспорт
│   ├── 🏨 Отели
│   ├── 🚶‍♂️ Экскурсии
│   └── 🛍️ Магазины и услуги
├── 📍 Рядом
├── ❓ Помощь
├── 🌐 Язык
└── 👤 Личный кабинет
```

### Категории и подкатегории

#### Рестораны
```
🍽️ Рестораны
├── 🌶️ Азиатская
├── 🍝 Европейская
├── 🌭 Уличная еда
├── 🥗 Вегетарианская
├── 📋 Показать все
└── ⬅️ К категориям
```

#### Транспорт
```
🏍️ Транспорт
├── 🏍️ Байки
├── 🚗 Машины
├── 🚲 Велосипеды
└── ⬅️ К категориям
```

#### SPA
```
💆 SPA
├── 💄 Салон красоты
├── 💆 Массаж
├── 🧖 Сауна
└── ⬅️ К категориям
```

#### Отели
```
🏨 Отели
├── 🏨 Отели
├── 🏠 Апартаменты
└── ⬅️ К категориям
```

#### Экскурсии
```
🚶‍♂️ Экскурсии
├── 👥 Групповые
├── 👤 Индивидуальные
└── ⬅️ К категориям
```

#### Магазины и услуги
```
🛍️ Магазины и услуги
├── 🛍️ Магазины
├── 🔧 Услуги
└── ⬅️ К категориям
```

## 🔐 СИСТЕМА БЕЗОПАСНОСТИ

### Роли пользователей
```python
USER_ROLES = {
    'USER': 'Обычный пользователь',
    'PARTNER': 'Партнер (владелец заведения)',
    'MODERATOR': 'Модератор',
    'ADMIN': 'Администратор',
    'SUPER_ADMIN': 'Супер-администратор'
}
```

### Права доступа
```python
PERMISSIONS = {
    'USER': [
        'read_profile',
        'read_points',
        'read_transactions',
        'manage_favorites',
        'use_referral_system'
    ],
    'PARTNER': [
        'read_profile',
        'manage_cards',
        'view_statistics',
        'upload_images',
        'manage_establishments'
    ],
    'MODERATOR': [
        'moderate_cards',
        'manage_partners',
        'view_moderation_queue',
        'approve_reject_cards'
    ],
    'ADMIN': [
        'manage_users',
        'view_financials',
        'system_settings',
        'manage_categories',
        'view_analytics'
    ],
    'SUPER_ADMIN': [
        'all_permissions',
        'manage_admins',
        'system_maintenance',
        'database_management'
    ]
}
```

### Политика конфиденциальности
- ✅ Обязательное принятие при первом запуске
- ✅ Middleware для проверки принятия
- ✅ Блокировка функций до принятия
- ✅ Логирование принятия политики

## 🌐 ЛОКАЛИЗАЦИЯ

### Поддерживаемые языки
- 🇷🇺 **Русский (RU)** - основной язык
- 🇺🇸 **Английский (EN)** - международный
- 🇰🇷 **Корейский (KO)** - азиатский рынок
- 🇻🇳 **Вьетнамский (VI)** - азиатский рынок

### Структура локализации
```python
translations = {
    'ru': {
        'menu.categories': '🗂️ Категории',
        'menu.help': '❓ Помощь',
        'categories.restaurants': '🍽️ Рестораны',
        # ... остальные ключи
    },
    'en': {
        'menu.categories': '🗂️ Categories',
        'menu.help': '❓ Help',
        'categories.restaurants': '🍽️ Restaurants',
        # ... остальные ключи
    },
    # ... остальные языки
}
```

## 📊 СИСТЕМА ЛОЯЛЬНОСТИ

### Типы транзакций
```python
TRANSACTION_TYPES = {
    'REFERRAL_BONUS': 'Бонус за приглашение',
    'VISIT_BONUS': 'Бонус за посещение',
    'REVIEW_BONUS': 'Бонус за отзыв',
    'PURCHASE_BONUS': 'Бонус за покупку',
    'SPENDING': 'Трата баллов',
    'ADMIN_GRANT': 'Начисление администратором',
    'ADMIN_DEDUCT': 'Списание администратором'
}
```

### Правила начисления
```python
LOYALTY_RULES = {
    'referral_level_1': {
        'points': 100,
        'description': 'За приглашение первого уровня'
    },
    'referral_level_2': {
        'points': 50,
        'description': 'За приглашение второго уровня'
    },
    'referral_level_3': {
        'points': 25,
        'description': 'За приглашение третьего уровня'
    },
    'visit_bonus': {
        'points': 10,
        'description': 'За посещение заведения'
    },
    'review_bonus': {
        'points': 20,
        'description': 'За написание отзыва'
    }
}
```

## 🔄 РЕФЕРАЛЬНАЯ СИСТЕМА

### Многоуровневая структура
```
Пользователь A приглашает B
├── A получает 100 баллов (уровень 1)
└── B приглашает C
    ├── B получает 100 баллов (уровень 1)
    └── A получает 50 баллов (уровень 2)
        └── C приглашает D
            ├── C получает 100 баллов (уровень 1)
            ├── B получает 50 баллов (уровень 2)
            └── A получает 25 баллов (уровень 3)
```

### Генерация реферальных ссылок
```python
def generate_referral_link(user_id: int) -> str:
    """Генерация уникальной реферальной ссылки"""
    referral_code = generate_unique_code(user_id)
    return f"https://t.me/{BOT_USERNAME}?start=ref_{referral_code}"
```

## 🏢 ПАРТНЕРСКАЯ СИСТЕМА

### Процесс регистрации партнера
1. **Подача заявки** через бота
2. **Заполнение анкеты** с данными о бизнесе
3. **Модерация заявки** администратором
4. **Верификация** документов
5. **Активация аккаунта** партнера

### Управление карточками
```python
CARD_STATUSES = {
    'DRAFT': 'Черновик',
    'PENDING': 'На модерации',
    'APPROVED': 'Одобрено',
    'REJECTED': 'Отклонено',
    'ARCHIVED': 'Архивировано'
}
```

### Процесс модерации
1. **Создание карточки** партнером
2. **Автоматическая проверка** на спам/дубли
3. **Ручная модерация** модератором
4. **Одобрение/отклонение** с комментариями
5. **Уведомление партнера** о результате

## 📱 TELEGRAM WEBAPP

### Инициализация
```javascript
// Инициализация WebApp
const webApp = window.Telegram.WebApp;
webApp.ready();
webApp.expand();

// Получение данных пользователя
const user = webApp.initDataUnsafe.user;
const authData = webApp.initData;
```

### API интеграция
```javascript
// Отправка данных на сервер
async function sendData(endpoint, data) {
    const response = await fetch(`/api/${endpoint}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${getAuthToken()}`
        },
        body: JSON.stringify(data)
    });
    return response.json();
}
```

## 🧪 ТЕСТИРОВАНИЕ

### Структура тестов
```
tests/
├── 📁 unit/                   # Юнит-тесты
│   ├── test_services.py
│   ├── test_handlers.py
│   └── test_utils.py
├── 📁 integration/            # Интеграционные тесты
│   ├── test_api.py
│   ├── test_database.py
│   └── test_webapp.py
└── 📁 e2e/                    # End-to-end тесты
    ├── test_user_flow.py
    ├── test_partner_flow.py
    └── test_admin_flow.py
```

### Покрытие тестами
- **Цель:** 80%+ покрытие кода
- **Критичные компоненты:** 95%+ покрытие
- **Автоматические тесты** при каждом коммите
- **Регрессионные тесты** при релизах

## 🚀 ДЕПЛОЙ И МОНИТОРИНГ

### Переменные окружения
```env
# Основные настройки
BOT_TOKEN=your_telegram_bot_token
DATABASE_URL=postgresql://user:password@host:port/dbname
WEBHOOK_URL=https://your-domain.com/webhook
WEBHOOK_SECRET=your_webhook_secret

# Администраторы
ADMIN_IDS=12345,67890
SUPER_ADMIN_IDS=12345

# Настройки приложения
DEBUG=False
LOG_LEVEL=INFO
ENVIRONMENT=production

# Безопасность
JWT_SECRET=your_jwt_secret
ENCRYPTION_KEY=your_encryption_key

# Внешние сервисы
REDIS_URL=redis://localhost:6379
SENTRY_DSN=your_sentry_dsn
```

### Мониторинг
- **Доступность сервиса** - проверка каждые 5 минут
- **Время ответа** - мониторинг API endpoints
- **Ошибки** - автоматические алерты при критических ошибках
- **Использование ресурсов** - CPU, память, диск

### Логирование
```python
# Структура логов
{
    "timestamp": "2025-07-09T16:00:00Z",
    "level": "INFO",
    "logger": "bot.handlers",
    "message": "User opened categories menu",
    "user_id": 12345,
    "action": "category_open",
    "metadata": {
        "category": "restaurants",
        "language": "ru"
    }
}
```

## 📈 АНАЛИТИКА И МЕТРИКИ

### Ключевые метрики
- **DAU/MAU** - ежедневные/месячные активные пользователи
- **Retention** - удержание пользователей
- **Conversion** - конверсия в партнеры
- **Engagement** - вовлеченность пользователей

### Бизнес-метрики
- **Количество партнеров** - рост базы партнеров
- **Количество карточек** - активность партнеров
- **Сканирования QR** - использование скидок
- **Реферальная активность** - эффективность реферальной программы

## 🔧 ОПТИМИЗАЦИЯ ПРОИЗВОДИТЕЛЬНОСТИ

### Кеширование
- **Redis** для кеширования часто используемых данных
- **Кеш меню** - кеширование клавиатур и текстов
- **Кеш карточек** - кеширование популярных карточек
- **Кеш пользователей** - кеширование профилей

### База данных
- **Индексы** на часто используемые поля
- **Пагинация** для больших списков
- **Оптимизация запросов** - минимизация N+1 проблем
- **Партиционирование** для больших таблиц

### API оптимизация
- **Rate limiting** - ограничение частоты запросов
- **Compression** - сжатие ответов
- **CDN** - кеширование статических ресурсов
- **Connection pooling** - пул соединений с БД

## 📋 ПЛАН РАЗРАБОТКИ

### Этап 1: Базовая функциональность ✅ ЗАВЕРШЕН
- [x] Настройка проекта и архитектуры
- [x] Создание базы данных и миграций
- [x] Реализация базовых обработчиков
- [x] Система лояльности и рефералов
- [x] Локализация на 4 языка

### Этап 2: Стандартизация интерфейса ✅ ЗАВЕРШЕН
- [x] Единые reply клавиатуры для всех категорий
- [x] Стандартизация навигации
- [x] Исправление кнопки "Помощь"
- [x] Обработка ошибок

### Этап 3: Личные кабинеты 🚧 В ПРОЦЕССЕ
- [ ] Кабинет пользователя
- [ ] Кабинет партнера
- [ ] Кабинет модератора
- [ ] Кабинет администратора

### Этап 4: Админ-панель 📝 ПЛАНИРУЕТСЯ
- [ ] Управление пользователями
- [ ] Управление партнерами
- [ ] Система модерации
- [ ] Аналитика и отчеты

### Этап 5: Полировка и тестирование 📝 ПЛАНИРУЕТСЯ
- [ ] Comprehensive тестирование
- [ ] Оптимизация производительности
- [ ] Мониторинг и алерты
- [ ] Документация

## 🎯 КРИТЕРИИ ГОТОВНОСТИ

### MVP (Minimum Viable Product)
- ✅ Бот запускается и работает
- ✅ Все категории функционируют
- ✅ Система лояльности работает
- ✅ Реферальная программа работает
- ✅ Локализация на 4 языка
- 🚧 Личные кабинеты (частично)
- 📝 Админ-панель (планируется)

### Production Ready
- ✅ Стабильная работа бота
- ✅ Обработка ошибок
- ✅ Логирование и мониторинг
- ✅ Безопасность и авторизация
- 🚧 Полные личные кабинеты
- 🚧 Полная админ-панель
- 📝 Comprehensive тестирование
- 📝 Документация

## 📞 ПОДДЕРЖКА И ОБСЛУЖИВАНИЕ

### Техническая поддержка
- **Документация** для разработчиков
- **API документация** с примерами
- **Troubleshooting guide** для частых проблем
- **Мониторинг** для раннего обнаружения проблем

### Обновления и релизы
- **Semantic versioning** для версий
- **Changelog** для каждого релиза
- **Rollback plan** для отката изменений
- **Feature flags** для постепенного внедрения

---

**Статус проекта:** 🚧 В активной разработке  
**Готовность к продакшену:** 70%  
**Следующий этап:** Реализация личных кабинетов  
**Дата обновления:** 09/07/2025 16:30:00
