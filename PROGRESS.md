# Текущий прогресс по ТЗ (реальный чеклист)

Обновлено: 2025-09-05, 10:28 (VN, +07+0700)
Анализ проведен: AI Code Analyzer

## 📊 Реальная сводка (проценты и статусы)

### Основные компоненты:

- **Категории и UX (бот): 85%** 🔄
  - 6 фиксированных категорий (Reply): 100%
  - Inline‑фильтры restaurants: 100% (`core/keyboards/inline_v2.py` L29-L48; `core/handlers/category_handlers_v2.py` L89-L95)
  - Пагинация 5/стр: 100% (`core/handlers/category_handlers_v2.py` L97-L105, L142-L147)
  - Рендер карточки: 85% (`core/services/card_renderer.py` + кнопки ℹ️/🗺 `get_catalog_item_row`)
  - **Проблемы:**
    - Геопоиск — заглушка (TODO в `category_handlers_v2.py` L356-L359)

- **Кабинет пользователя: 65%** 🔄
  - Профиль пользователя: 60%
  - История активности: 50%
  - Управление QR-кодами: 70% (`web/routes_qr.py` базовый флоу)
  - История скидок: 50%
  - Статистика баллов: 60% (`core/services/loyalty_service.py`)
  - Реферальная программа: 60% (есть генерация/статистика; часть TODO)
  - Избранные заведения: 40%
  - Настройки уведомлений: 40%
  - **Проблемы:**
    - Неполные обработчики в UX, часть логики помечена TODO

- **Кабинет партнёра: 80%** 🔄 
  - API загрузки/листинга/удаления: 95% (`web/routes_cabinet.py` L871-L949, L998-L1031)
  - Бот‑хендлеры галереи: 80% (`core/handlers/partner.py` — FSM загрузки фото, лимит 6)
  - Валидация и статусы: 70% (частично, требуется доработать валидации файлов)
  - **Проблемы:**
    - Проверки формата/размера файлов в API — расширить

- **Админ‑панель: 70%** 🔄
  - Роуты admin_cabinet: 75% (`core/handlers/admin_cabinet.py`)
  - Модерация: 80% (`core/handlers/moderation.py`, `core/database/db_v2.py` moderation_log)
  - Отчёты: 55% (`web/routes_dashboard.py` содержит TODO-заглушки)
  - **Проблемы:**
    - В отчётах есть TODO-заглушки (L171, L207, L231)

- **Сервисы: 82%** 🔄
  - QR‑сервис: 90% (юнит‑тесты проходят; `web/routes_qr.py`; redeem в `web/routes_cabinet.py` L212-L304)
  - Loyalty: 80% (богатый сервис `core/services/loyalty_service.py`)
  - Referral: 70% (генерация/статистика есть; есть TODO в process_referral)
  - Cards: 70%
  - **Проблемы:**
    - TODO в реферальной логике (L940-L945)

- **Безопасность: 80%** 🔄
  - RBAC: 85% (`core/security/policy.py`, `web/routes_admin.py` роли/зависимости)
  - 2FA: 100% (админ TOTP `web/routes_admin.py`)
  - JWT: 80% (`core/services/webapp_auth.py`, `core/security/jwt_service.py`)
  - Rate limiting: 60% (`web/main.py` in‑memory для /api/qr/*)
  - **Проблемы:**
    - JWT секрет/pyjwt в dev фоллбеках — убедиться в прод-настройках

- **Мониторинг: 55%** 🔄
  - Метрики: 60% (`core/monitoring.py`, структурированное логирование, базовые события)
  - Prometheus: 60% (есть `/metrics` в `web/main.py` L424-L426)
  - Grafana: 0% (дашборды отсутствуют)
  - Health checks: 70% (`web/health.py`)
  - **Проблемы:**
    - Нет готовых дашбордов и алертов

- **Тестирование: 68%** 🔄
  - Unit тесты: 60%
  - Integration: 60%
  - E2E: 55% (каркас `tests/e2e/test_user_journey.py`, xfail 3/3 — в работе)
  - Покрытие кода: ~60-70% (по структуре набора тестов)
  - **Проблемы:**
    - Smoke партнёрского кабинета исправлен (алиасы /cabinet/* в minimal‑mode)

- **Документация: 80%** 🔄
  - README: 85% (подробный)
  - API docs: 60%
  - Deploy guide: 80% (`DEPLOYMENT.md`, Railway/Heroku)
  - **Проблемы:**
    - Не хватает срезов по API/мониторингу

## 🎯 Критические недоработки

### Высокий приоритет:
- Нет Grafana дашбордов и предупреждений
- TODO в реферальной логике (начисления/проверки)

### Средний приоритет:
- Геопоиск — заглушка в категориях
- Отчёты админки содержат TODO

### Низкий приоритет:
- Расширить валидацию изображений в партнёрском API

## 📝 План доработки

### Неделя 1:
- [ ] Заполнить E2E сценарии (user journey, catalog, cabinet)
- [ ] Завершить реферальную логику и тесты

### Неделя 2:
- [ ] Дашборды Grafana и алерты Prometheus
- [ ] Доработать рендер карточек и UX

### Неделя 3-4:
- [ ] Улучшить отчёты админки и экспорт
- [ ] Оптимизация БД и кэширования

## 🐛 Найденные TODO/FIXME

### Критичные:
- core/services/loyalty_service.py L940-L945 — TODO по реферальной обработке

### Обычные:
- web/routes_dashboard.py L171/L207/L231 — заглушки
- core/handlers/category_handlers_v2.py L356 — геопоиск

## 📈 Общая готовность проекта

**Реальная готовность: 82%**

**Оценка качества кода: B**

**Готовность к продакшену: Частично**

## 🚀 Рекомендации

1. **Немедленно:**
   - Завершить реферальную логику и покрыть тестами
   - Добавить Grafana дашборды и базовые алерты

2. **В течение недели:**
   - Допилить E2E сценарии и стабилизировать тестовый запуск
   - Расширить проверки загрузки изображений

3. **В течение месяца:**
   - Расширить отчёты и экспорт в админке
   - Включить пром-метрики и алерты по SLA

---

## 📂 Карта проекта (структура и статистика)
- Всего файлов: 434
- Размер проекта: 9.3M
- Строк кода (Python): 38 937
- Строки Markdown: 2 925; Shell: 473; PowerShell: 486; JS: 1
- Ключевые директории:
  - `core/` — логика бота, сервисы, безопасность, БД-адаптеры, клавиатуры, хендлеры
  - `web/` — FastAPI маршруты, основной `web/main.py`, health, cabinet, admin, auth, loyalty, qr
  - `tests/` — unit/integration/e2e; каркасы E2E помечены xfail
  - `migrations/` — SQL-скрипты для схем: лояльность, рефералы, 2FA, каталог
  - `docs/` — документация, чеклисты; есть `docs/prometheus/`
  - `deployment/` — `docker-compose.prod.yml`
  - корневые файлы Railway/Procfile/Dockerfile и requirements*

## 🔎 Сверка заявлений (✅/🔄/❌/⚠️)
- `process_referral` в лояльности: ❌ (есть TODO на L940–945)
- Геопоиск (5 км, интеграция): 🔄 (есть утилиты `core/utils/geo.py`, но заглушка в `category_handlers_v2.py` L356–359)
- Admin Dashboard «реальные запросы к БД»: ❌ (`web/routes_dashboard.py` использует моки, TODO на L171/207/231)
- Эндпоинты `/admin/top-places`, `/admin/referrals-stats`: ❌ (не найдены)
- `routes_user_cabinet.py`: ❌ (нет файла; функции кабинета в `web/routes_cabinet.py`)
- `moderation_service.py`, `notification_service.py`: ❌ (нет файлов; функционал частично в других модулях)
- 2FA (TOTP) для админов: ✅ (`web/routes_admin.py`)
- `/metrics` Prometheus: ✅ (`web/main.py` L424–426)

## 🧩 Ключевые компоненты (файлы)
- Лояльность: ✅ `core/services/loyalty_service.py` (полный сервис, кроме реферальной обработки)
- Рефералы: 🔄 `core/services/referral_service.py` (базовая статистика/бонусы, без многоуровневых уровней)
- Категории: ✅ `core/handlers/category_handlers_v2.py` (фильтры/пагинация/просмотр), ⚠️ геопоиск — заглушка
- Партнёры: ✅ `core/handlers/partner.py`, ✅ `web/routes_cabinet.py` (галерея, CRUD)
- Пользователи: ✅ `core/handlers/user.py`, профильные экраны в работе
- Админ-дашборд: 🔄 `web/routes_dashboard.py` (моки)
- Авторизация: ✅ `web/routes_auth.py`, ✅ `core/services/webapp_auth.py`, ✅ `core/security/jwt_service.py`

## 🚄 Railway: готовность
- Конфигурация: ✅ `railway.toml`, ✅ `railway.json`, ✅ `Procfile` (start: `python start.py`), ✅ `Dockerfile`, ✅ `requirements.txt`
- Healthcheck: ✅ `/health`
- Переменные окружения: ✅ `DATABASE_URL`, ✅ `REDIS_URL` (в `env.example`), ✅ `PORT` (в Railway), ✅ `BOT_TOKEN`, ✅ `ADMIN_ID`, ✅ `JWT_SECRET` (используются в коде)
- Порты: ✅ `PORT` пробрасывается; `start.py` запускает сервер
- Миграции: ✅ SQL-скрипты в `migrations/`; автоматическое применение при старте не включено (нужно проверить пайплайн)

## ⚠️ Найденные проблемы (выборка)
- TODO: `core/services/loyalty_service.py` L940–945; `web/routes_dashboard.py` L171/207/231; `core/handlers/category_handlers_v2.py` L356–359; `web/routes_loyalty.py` L88
- Заглушки/моки: `web/routes_dashboard.py` (статистика/графики)
- Не найденные по заявлению файлы: `core/services/moderation_service.py`, `core/services/notification_service.py`, `web/routes/routes_user_cabinet.py`, эндпоинты `/admin/top-places`, `/admin/referrals-stats`

## 🧪 Тестирование
- Тесты: есть unit/integration, E2E-скелеты (`tests/e2e/test_user_journey.py` xfail)
- Оценка покрытия: ~60–70% (по объёму и охвату модулей)
- Критично дописать: E2E сценарии (бот → каталог → QR → лояльность), интеграцию дашборда

