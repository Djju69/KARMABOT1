# CHANGELOG

## 2025-01-14 - i18n Housekeeping and Documentation Cleanup

### i18n Improvements
- **Fixed duplicate keys**: `back_to_main` → `menu.back_to_main_menu`
- **Fixed duplicate keys**: `profile_settings` → `keyboard.profile_settings`
- **Added 21 missing keys** to EN locale with proper translations
- **Created alias system** for backward compatibility
- **Implemented namespace structure**: `common.*`, `keyboard.*`, `menu.*`, `partner.*`, `admin.*`, `user.*`, `errors.*`, `messages.*`
- **Added deprecated.json** for old keys
- **Created i18n consistency tests** with automated validation
- **Updated locales_v2.py** with alias support

### Documentation Cleanup
- **Consolidated documentation**: Reduced from 49 to 4 main files
- **Created comprehensive guides**:
  - `docs/INSTALL.md` - Installation and deployment
  - `docs/USER_GUIDE.md` - User and partner guide
  - `docs/DEV_GUIDE.md` - Developer guide with Non-Breaking Dev Guide
  - `docs/i18n_guide.md` - Localization guide
  - `docs/i18n_namespaces.md` - Namespace structure
  - `docs/i18n_report.md` - Migration report
- **Removed duplicate files**: README2.md, TECHNICAL_SPECIFICATION.md, DEPLOY.md, DEPLOYMENT.md, DEPLOY_DOCS.md, TESTING.md, RAILWAY_VARS.md, TELEGRAM_SETUP.md
- **Maintained backward compatibility** for all existing functionality

### Technical Improvements
- **Enhanced get_text()** function with alias resolution
- **Added namespace-based key organization**
- **Implemented automated i18n testing**
- **Created migration report** with before/after analysis
- **Maintained all existing UI/UX** without breaking changes

## 2025-01-10 - Critical Fixes and AI Help Implementation

### Critical Fixes
1. **Fixed AI Help Handler**
   - Added explicit handler for "❓ Помощь" button in all languages
   - Added callback handler for `help:main_menu` to return to main menu
   - Enhanced logging with [AI_HELP] prefix for better debugging

2. **Fixed Privacy Policy Middleware**
   - Added help commands to ALLOWED_COMMANDS list
   - Added `help:` callbacks to ALLOWED_CALLBACKS
   - Now allows `/help` and "❓ Помощь" button without policy acceptance

3. **Fixed Database Issues**
   - Created `fix_database.sql` script to fix missing tables
   - Handles duplicate column errors gracefully
   - Creates missing tables: `cards_generated`, `favorites`, `karma_log`
   - Adds missing indexes for performance

4. **Fixed Pydantic Deprecation Warnings**
   - Replaced `orm_mode = True` with `from_attributes = True` in all schema files
   - Updated: models.py, auth.py, review.py, media.py, place.py, category.py, base.py

## 2025-01-10 - AI Help Implementation

### Added
- **Complete AI Help System** (`core/handlers/ai_help.py`)
  - Implemented full AI assistant functionality with menu system
  - Added interactive chat with FSM states (`AIHelpStates`)
  - Smart keyword-based responses for common questions (discounts, karma, registration, etc.)
  - FAQ section with structured Q&A format
  - Direct support contact integration
  - Multi-language support through i18n system

### Features
- **AI Chat Features**:
  - Context-aware responses based on keywords
  - Chat history tracking
  - "Ask another question" and "End chat" buttons
  - Graceful error handling
  - Rate limiting ready (stub implemented)

- **Help Menu Structure**:
  ```
  🆘 Центр помощи Karma System
  [🤖 AI Помощник] - мгновенные ответы
  [📋 FAQ] - популярные вопросы  
  [📞 Поддержка] - связь с командой
  [◀️ Назад] - в главное меню
  ```

### Localization
- Added translations for all 4 languages (RU/EN/VI/KO):
  - `btn.ai_assistant`, `btn.faq`, `btn.contact_support`
  - `btn.ask_another`, `btn.end_chat`
  - `help.main_menu`, `ai.intro_message`
  - `ai.ask_question`, `ai.goodbye`, `main.menu_restored`

### Integration
- Integrated `ai_help_router` into `main_v2.py`
- Proper router ordering for priority handling
- Feature flag support (`settings.features.support_ai`)

### Technical Details
- Fallback responses for when OpenAI API is not available
- Keyword matching system for common topics
- Database integration for user language preferences
- Proper FSM state management for conversations

Дата: 2025-08-24

## [Unreleased]

### [2025-09-09 16:50] ДОБАВЛЕНА КНОПКА СМЕНЫ ЯЗЫКА ВО ВСЕ КАБИНЕТЫ

[2025-09-09 17:00] ИСПРАВЛЕНЫ КРИТИЧЕСКИЕ ОШИБКИ В ЛИЧНОМ КАБИНЕТЕ
- Исправлено отображение переменных в личном кабинете - теперь показываются реальные данные вместо {user_id}, {name}, {username}, {lang}
- Исправлено отображение реферальной ссылки - теперь красивый текст со скрытой ссылкой вместо нечитаемого URL
- Исправлены ошибки в referral_service - заменены неправильные методы БД fetch_all на execute_query
- Подтверждено наличие AI ассистента в /help как inline кнопка
- Подтверждено наличие кнопки "Язык" во всех кабинетах (user/partner/admin/superadmin)

[2025-09-09 17:15] ИСПРАВЛЕНЫ ОШИБКИ ИМПОРТОВ И ОБРАБОТЧИКОВ
- Исправлен импорт get_cancel_keyboard в user.py - заменен на get_return_to_main_menu
- Исправлен обработчик help в cabinet_router.py - теперь показывает AI ассистента
- Исправлены ошибки в referral_service - добавлены проверки на существование результатов БД
- Исправлены все ошибки импортов, которые мешали запуску бота

[2025-09-09 17:30] ИСПРАВЛЕН AI АССИСТЕНТ И КНОПКА ЯЗЫКА
- Удален дублирующий обработчик help из cabinet_router.py - теперь AI ассистент работает через help_with_ai_router
- Добавлено логирование в обработчик языка для отладки
- AI ассистент теперь должен появляться в /help как inline кнопка "🤖 Задать вопрос ИИ"

[2025-09-09 17:45] ДОБАВЛЕНА СИСТЕМА УПРАВЛЕНИЯ УВЕДОМЛЕНИЯМИ В AI-АССИСТЕНТА
- Реализован функционал управления уведомлениями согласно системному промту AI-ассистента "Карма"
- Добавлены категории уведомлений для всех ролей (пользователь, партнер, админ, суперадмин)
- Реализованы приоритеты уведомлений (LOW, NORMAL, HIGH, CRITICAL)
- Добавлена команда /notifications и кнопка "⚙️ Управление уведомлениями" во все кабинеты
- AI-ассистент теперь умеет обрабатывать запросы по настройке уведомлений
- Добавлена поддержка тихих часов и группировки уведомлений

[2025-09-09 18:00] ИСПРАВЛЕНЫ НАСТРОЙКИ И AI АССИСТЕНТ
- Создана кнопка "⚙️ Настройки" во всех кабинетах для упрощения интерфейса
- Перенесены кнопки "🌐 Язык" и "🔔 Уведомления" в меню настроек
- Убрано дублирование кнопок - оставлена только "🔔 Уведомления" в настройках
- Исправлен AI ассистент - добавлен обработчик для кнопки "❓ Помощь"
- Создан settings_router для обработки всех настроек
- Упрощен интерфейс кабинетов - убраны лишние кнопки
- help_with_ai_router подключен ПЕРВЫМ для приоритета перехвата /help
- Добавлены недостающие ключи переводов для кнопок уведомлений (btn.notify.on/off)
- Добавлена отладочная информация для диагностики AI ассистента
- Кнопка "🌐 Язык" должна работать во всех кабинетах

#### Добавлено
- **Кнопка "🌐 Язык"** - добавлена во все личные кабинеты (user/partner/admin/superadmin)
- **Обработчики языка** - добавлены в partner.py и admin_cabinet.py
- **Многоязычность** - кнопка поддерживает RU/EN/VI/KO

### [2025-09-09 16:45] ИСПРАВЛЕНИЯ AI-АССИСТЕНТА И МИГРАЦИЙ

#### Исправлено
- **Feature flags AI** - включены `FEATURE_SUPPORT_AI=True` и `FEATURE_SUPPORT_REPORTS=True`
- **Миграция 010** - добавлена в список миграций для создания таблиц favorites, referrals, karma_log, points_log, achievements
- **Отсутствующие таблицы** - исправлена ошибка "relation cards_generated does not exist"

### [2025-09-09 16:30] ВОССТАНОВЛЕНИЕ AI-АССИСТЕНТА "КАРМА"

#### Восстановлено
- **AI-ассистент "Карма"** - полностью восстановлен функционал поддержки
- **FSM состояния** - `SupportStates` для управления AI-чатом
- **Сервисы поддержки** - `SupportAIService`, `ReportService`, `STTService`
- **Email отправка** - `EmailSender` для отчётов
- **Rate limiting** - ограничения частоты запросов
- **Клавиатуры AI** - кнопки управления в AI-режиме
- **Обработчики** - `help_with_ai.py`, `support_ai.py`
- **i18n ключи** - полная локализация для AI-ассистента
- **Feature flags** - `FEATURE_SUPPORT_AI`, `FEATURE_SUPPORT_REPORTS`, `FEATURE_SUPPORT_VOICE`
- **Скрытая команда** - `/support` для прямого запуска AI
- **Интеграция** - подключение роутеров к основному боту

#### Функционал AI-ассистента
- **Кнопка под /help** - "🤖 Задать вопрос ИИ" для всех ролей
- **Ролевые отчёты** - разные отчёты для user/partner/admin/superadmin
- **Голосовые сообщения** - распознавание речи (до 60 сек, 2 МБ)
- **FAQ система** - ответы на частые вопросы
- **Эскалация** - передача сложных вопросов администратору
- **Многоязычность** - поддержка RU/EN/VI/KO

### [2025-09-09 16:00] КРИТИЧЕСКИЕ ИСПРАВЛЕНИЯ

#### Исправлено
- **Личный кабинет пользователя**: исправлены ошибки загрузки (no such column: qr_id)
- **Реферальная система**: исправлены методы fetch_one/fetch_all → execute_query
- **Сервис избранных**: исправлены методы БД для корректной работы
- **Импорты**: удален несуществующий get_confirmation_keyboard из user.py
- **Настройки**: исправлен импорт settings в main_menu_router.py
- **Категории**: отключен показ списка с количеством мест (только кнопки)
- **Дублирование иконок**: убрано дублирование эмодзи в категориях
- **Команда /add**: упрощена, направляет к кнопке в меню
- **Текст помощи**: заменен на красивый HTML формат с секциями
- **Реферальная ссылка**: исправлено отображение с HTML тегами

#### Изменено
- **Показ категорий**: теперь только кнопки без статистики для обычных пользователей
- **Форматирование помощи**: HTML вместо простого текста
- **Парсинг сообщений**: Markdown → HTML для рефералов

### Добавлено
- **Обновленная система настроек**:
  - Добавлена поддержка Pydantic v2 с обратной совместимостью
  - Гибкая система фича-флагов для управления функционалом
  - Улучшенная валидация настроек
  - Подробное логирование работы системы
- **QR-коды**:
  - Сервис для генерации и управления QR-кодами
  - Интеграция с WebApp для удобного управления
  - История операций с QR-кодами
- **Документация**:
  - Обновлен README с инструкциями по настройке
  - Добавлено описание работы с QR-кодами

### Изменено
- Рефакторинг системы настроек для большей гибкости
- Обновлены зависимости в requirements.txt
- **Loyalty System**:
  - Добавлена таблица `loyalty_points_tx` для учета транзакций с баллами
  - Реализован `LoyaltyService` с методами:
    - `add_transaction()`: Запись начисления/списания баллов
    - `get_balance()`: Получение текущего баланса (с кэшированием)
    - `get_recent_transactions()`: Просмотр истории операций
  - Интеграция с эндпоинтом начисления баллов за активности
  - Комплексные тесты для новой функциональности
- SPA-страница кабинета (`INDEX_HTML` в `web/main.py`) с вкладками «Профиль» и «Мои карточки».
- Диагностические элементы UI: `#status`, `#error`, `#diag`, статусы при вводе токена.
- Автобутстрап SQLite (`web/routes_cabinet.py`): создаются минимальные таблицы `partners_v2`, `categories_v2`, `cards_v2` при первом запуске.
- Документация:
  - `README_WEBAPP.md` — состояние проекта, как запускать/тестировать.
  - `TZ_LK.md` — сводное ТЗ по личным кабинетам.

### Исправлено
- Фронтенд `asciiToken()` теперь фильтрует токен до печатаемых ASCII (32..126) — безопасный заголовок Authorization.
- `devTokenFlow()` сразу вызывает `loadProfile()` (UI обновляется даже без редиректа), после этого мягкий переход на URL с `?token=`.
- Обработчик Enter в поле токена и явные статусы «Применяю токен… / Загружаю профиль…».

### Изменено
- `web/routes_cabinet.py`: усилена устойчивость `get_current_claims()` и логирование auth-событий.
- Возврат пустых списков и корректных кодов вместо 500 при пустой БД.

### Известные ограничения
- Продвинутый UI карточек (фильтры/таблица/модалки/пагинация) — не завершён (MVP-рендер в `ul#cardsList`).
- Возможны 401/403 при невалидном/просроченном токене.
- В отдельных окружениях требуется принудительный сброс кэша/Service Worker (используйте Ctrl+F5/инкогнито).
