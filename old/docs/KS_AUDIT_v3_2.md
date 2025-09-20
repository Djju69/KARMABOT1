# Аудит соответствия ТЗ — Karma System v3.2

Дата: 2025-08-27
Статус: в процессе

## Резюме
- Документ спецификации сохранён: `docs/KS_SPEC_v3_2.md`.
- Кодовая база импортирована. Выполнен первичный аудит ключевых модулей:
  - `web/main.py`, `web/routes_cabinet.py` — FastAPI, кабинеты, QR redeem, bind card.
  - `core/services/cards.py` — привязка пластиковой карты (UID hash+salt).
  - `core/services/loyalty.py` — кошельки/транзакции/spend intents.
  - `core/security/jwt_service.py`, `core/services/webapp_auth.py` — JWT/HMAC.
  - `core/database/migrations.py`, `core/database/db_v2.py` — миграции БД и доступ.
  - `core/utils/locales_v2.py`, `core/i18n/*.json` — i18n.
- Критичное замечание безопасности: в `web/routes_cabinet.py:get_current_claims()` присутствует небезопасный fallback, принимающий неподписанный payload JWT (для ролей admin/partner). Требуется отключить в проде.

## Ожидаемая структура по ТЗ
- Каталог: боты/роутеры/сервисы, веб API, миграции, i18n.
- Критические файлы (по ТЗ):
  - `app/core/services/{card_service.py, activity_service.py, referral_service.py}`
  - `app/api/routes/{cards.py, loyalty_activity.py, referral.py, admin_referral.py}`
  - `app/bot/routers/{start.py, activity.py, referral.py, profile.py}`
  - `app/bot/constants/buttons.py`
  - `app/db/migrations/*` (loyalty/referral/cards/enum expand)
  - `app/tests/{test_cards_bind.py, test_activity_claim.py, test_referral_flow.py}`

## Чек-лист аудита по разделам ТЗ

- [ ] Каталог и UX (v3)
  - Ожидаемые regex callback’и, пагинация 5/стр, фильтры.
  - Состояние: частично реализовано (веб-кабинет, листинг карт в `web/routes_cabinet.py`); аудит бота продолжается.

- [ ] FSM регистрации партнёра
  - Единый процесс, sub_slug для restaurants/transport/tours.
  - Состояние: требуется дальнейший поиск/проверка FSM в `core/handlers/*`.

- [x] QR-скидки (redeem атомарный, TTL)
  - Реализация: `web/routes_cabinet.py:/api/qr/redeem`, БД: `qr_codes_v2` (`core/database/migrations.py`).
  - Статус: реализовано; требуется тестирование TTL и метрик.

- [x] Пластиковая карта (v3.1)
  - Привязка: `web/routes_cabinet.py:/card/bind` → `core/services/cards.py` (SHA-256(uid+salt), `user_cards`).
  - Статус: реализовано; deeplink HMAC-токен не обнаружен (используется JWT WebApp), уточнить по ТЗ.

- [x] Лояльность: кошельки, транзакции, spend intents
  - Реализация: `core/services/loyalty.py` + таблицы `loyalty_wallets`, `loy_spend_intents`, `loyalty_transactions`.
  - Статус: реализовано; reason='referral_bonus' упомянут в ТЗ — проверить использование при добавлении рефералов (отсутствует).

- [ ] Активности (v3.2)
  - Таблицы правил/лога, кулдауны, гео-проверки.
  - Статус: реализации не обнаружено; требуется разработка согласно ТЗ.

- [ ] Рефералы (v3.2)
  - Таблицы `referral_codes`, `referrals`, анти-фрод, активация (порог/первый redeem).
  - Статус: реализации не обнаружено в кодовой базе; требуется разработка (сервисы, маршруты, БД, метрики).

- [ ] Бот: маршруты и UX
  - Профиль/привязка карты: `core/handlers/profile.py` найдено; `^ref:*` не обнаружены.
  - Статус: частично реализовано; требуется добавить рефералы и активности.

- [x] i18n (RU/EN/VI/KO)
  - Реализация: `core/utils/locales_v2.py`, `core/i18n/*.json`.
  - Статус: реализовано; требуется сверка ключей для новых фич (рефералы/активности).

- [ ] Безопасность
  - JWT: `core/security/jwt_service.py`; WebApp HMAC: `core/services/webapp_auth.py`; rate-limit: `web/main.py` (QR API).
  - Риск: небезопасный fallback JWT в `web/routes_cabinet.py:get_current_claims()` (принимает unsigned payload для admin/partner). Устранить/ограничить prod.
  - Статус: в целом реализовано; требуется хардненинг и юнит-тесты.

- [ ] Мониторинг (Prometheus)
  - Экспозиция `/metrics` есть в `web/main.py`.
  - Статус: минимально; требуется добавить метрики для activity/referral.

- [x] Миграции БД
  - Реализованы: `categories_v2`, `partners_v2`, `cards_v2`, `qr_codes_v2`, `banned_users`, `card_photos`, `loyalty_*`.
  - Отсутствуют: таблицы activity/referral (из ТЗ v3.2) — добавить.

- [ ] Тесты (pytest)
  - Наличие: `tests/` содержит базовые тесты (`auth_smoke.py`, `test_contracts.py`).
  - Статус: покрытие фич v3.2 отсутствует; требуется доп. тесты по QR, bind, loyalty, referral, activity, security.

## Следующие шаги
1) Устранить небезопасный fallback в `get_current_claims()` и добавить строгие проверки JWT (отключить unsigned-путь в prod).
2) Спроектировать и реализовать модуль «Рефералы» (БД, сервис, API, бот-UX, метрики) согласно ТЗ.
3) Спроектировать и реализовать модуль «Активности» (правила/лог, API, анти-фрод, метрики) согласно ТЗ.
4) Досверить FSM партнёра и бот-маршруты `^ref:*`, `^actv:*`; добить i18n-ключи.
5) Добавить тесты и метрики по всем новым частям; покрыть QR/bind/loyalty/безопасность.
