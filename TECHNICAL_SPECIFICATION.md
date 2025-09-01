# ТЕХНИЧЕСКОЕ ЗАДАНИЕ: KARMABOT1 - Полная система скидок и лояльности

## 1. ОБЗОР И АРХИТЕКТУРА

### 1.1 Назначение системы
Telegram-бот с WebApp для управления:
- Каталогом заведений с партнерскими карточками
- Системой лояльности с баллами и транзакциями ✅ РЕАЛИЗОВАНО
- Реферальной программой с многоуровневыми наградами ✅ РЕАЛИЗОВАНО
- QR-кодами для получения скидок
- Личными кабинетами пользователей и партнеров
- Системой модерации контента 🚧 В ПРОЦЕССЕ
- Админ-панелью управления 🚧 В ПРОЦЕССЕ

### 1.2 Технологический стек ✅ НАСТРОЕН
- **Backend**: Python 3.8+, aiogram 3.3.0+, FastAPI
- **Database**: SQLite → PostgreSQL (миграции готовы ✅)
- **Auth**: JWT для WebApp, Telegram initData
- **Testing**: Pytest (базовые контракт-тесты ✅)
- **Deployment**: Docker, фича-флаги ✅

## 2. СТРУКТУРА БАЗЫ ДАННЫХ

### 2.1 Основные таблицы (v2) ✅ СОЗДАНЫ МИГРАЦИИ

#### Система пользователей
```sql
users:
  - user_id (PK) - Telegram ID
  - username, first_name, last_name
  - language_code - для локализации
  - registration_date
  - is_active, is_partner, is_admin
  - referrer_id (FK users) ✅ - кто пригласил
  - loyalty_balance ✅ - баланс баллов лояльности
```

#### Система лояльности ✅ РЕАЛИЗОВАНО
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

#### Реферальная система ✅ РЕАЛИЗОВАНО
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

#### Партнеры и карточки заведений
```sql
partners_v2: ✅ СОЗДАНА
  - id (PK)
  - user_id (FK users) - владелец
  - business_name - название бизнеса
  - contact_info - JSON контактов
  - verification_status - статус верификации
  - created_at, updated_at

cards_v2: ✅ СОЗДАНА
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
  
categories_v2: ✅ СОЗДАНА
  - id (PK)
  - name_key - ключ для локализации
  - parent_id (FK categories_v2) - для иерархии
  - icon, color
  - sort_order
```

## 3. ПОЛЬЗОВАТЕЛЬСКИЕ ФУНКЦИИ

### 3.1 Главное меню и навигация ✅ РЕАЛИЗОВАНО БАЗОВОЕ
Структура меню:
```
🏠 Главное меню
├── 🗂️ Каталог заведений
│   ├── 📱 По категориям ✅
│   ├── 📍 Поиск рядом ✅  
│   └── 🌆 По районам ✅
├── 💰 Личный кабинет 📝 НУЖНО РЕАЛИЗОВАТЬ
│   ├── 📊 Мои баллы ✅
│   ├── 📱 QR-коды и скидки  
│   ├── 📈 История операций ✅
│   └── ⚙️ Настройки профиля
├── 👥 Реферальная программа ✅ РЕАЛИЗОВАНО
│   ├── 🔗 Моя ссылка ✅
│   ├── 📋 Приглашенные ✅  
│   └── 💵 Мои доходы ✅
├── ➕ Стать партнером 🚧 В ПРОЦЕССЕ
└── 🌐 Язык / Settings
```

### 3.2 Личный кабинет пользователя 📝 КРИТИЧНО - НУЖНО РЕАЛИЗОВАТЬ

#### 3.2.1 Профиль и статистика
```python
# Структура данных профиля
UserProfile:
  - basic_info: имя, username, дата регистрации
  - loyalty_stats: 
    * current_balance ✅
    * total_earned ✅  
    * total_spent
    * level/status (Bronze, Silver, Gold)
  - referral_stats: ✅
    * total_referrals
    * active_referrals  
    * total_earned_from_referrals
  - activity_stats:
    * visits_count
    * reviews_count
    * qr_codes_used
```

[Остальная часть спецификации...]

## 15. ЗАКЛЮЧЕНИЕ

Проект KARMABOT1 имеет отличную техническую основу - ключевые системы лояльности и рефералов полностью реализованы и готовы к использованию. База данных спроектирована правильно, миграции созданы, архитектура модульная и расширяемая.

Основные задачи для завершения проекта:
1. Реализовать личный кабинет - это критично для пользовательского опыта
2. Завершить админ-панель - нужна для управления системой
3. Написать comprehensive тесты - для стабильности продакшена
4. Добавить локализацию - для международной аудитории
5. Настроить мониторинг - для отслеживания здоровья системы

При правильном планировании и приоритизации, проект может быть готов к продакшн-запуску через 6-8 недель интенсивной разработки.

Ключевое преимущество: система спроектирована с учетом поэтапного развертывания через фича-флаги, что позволяет запускать функциональность по мере готовности без рисков для стабильности.
