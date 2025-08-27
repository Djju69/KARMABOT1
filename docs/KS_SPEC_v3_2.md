# 🧠 ГЛАВНОЕ ТЗ — Karma System (tech+UX) v3.2 [ФИНАЛЬНАЯ ВЕРСИЯ]

v3 → v3.1: добавлена пластиковая карта (deeplink-привязка, HMAC, одноразовый bind-токен).
v3.1 → v3.2 (этот документ): добавлены баллы за активность и реферальная программа.

0) Overview — что реализует бот
Karma System — многоязычная система лояльности и каталога для туристов и жителей.
Архитектура: Telegram-бот + FastAPI + PostgreSQL/PostGIS + Redis + мониторинг.
Ключевые возможности:
📂 Каталог 6 категорий: 🍽 рестораны, 🧖‍♀️ SPA, 🚗 транспорт, 🏨 отели, 🚶‍♂️ экскурсии, 🛍 магазины и услуги.
🎫 Скидки по QR (Fernet, payload=jti, TTL=24ч, redeem атомарный).
💳 Пластиковая карта без срока (deeplink HMAC + одноразовый bind-токен).
🎯 Баллы за активность (чек-ин, анкета, привязка карты, гео-чек-ин и т. п., с анти-фрод и кулдаунами).
👥 Реферальная программа (код/ссылка, активация, бонусы инвайтеру и инвайти).
👤 Личный кабинет гостя/партнёра (FSM-регистрация).
🌐 4 языка: RU/EN/VI/KO (i18n JSON).
🌆 Мульти-город (Нячанг, Дананг, Хошимин, Ханой, Фукуок).
📍 «Рядом» (PostGIS).
📑 PDF справка/политика.
🛠 JWT веб-API (партнёр), админ-эндпоинты.
🔒 Безопасность: PII-хэш, rate-limit, Redis-кэш, Prometheus/Grafana.
🎁 Лояльность (баллы) — фича-флаг LOYALTY_ENABLED.

0.1) Нестираемые константы (НЕ МЕНЯТЬ)
Главное меню (ReplyKeyboardMarkup, всегда на экране):
🗂️ Категории | 👤 Личный кабинет (растянутая) | 📍 По районам / Рядом | ❓ Помощь | 🌐 Язык
«Категории» (ReplyKeyboardMarkup — ровно 6):
🍽 restaurants | 🧖‍♀️ spa | 🚗 transport | 🏨 hotels | 🚶‍♂️ tours | 🛍 shops
Пагинация: 5 карточек/страница.
Callback-регэкспы (как в v3, без изменений):
^act:view:[0-9]+$
^pg:(restaurants|spa|transport|hotels|tours|shops):[0-9]+$
^filt:restaurants:(asia|europe|street|vege|all)$
^city:set:[0-9]+$
^qr:create:[0-9]+$
^policy:accept$
^lang:set:(ru|en|vi|ko)$
^qr:scan$
# Лояльность:
^loy:wallet$
^loy:history:[0-9]+$
^loy:spend:start$
^loy:spend:confirm:[0-9]+$
^loy:spend:create:[0-9]+$

Новые callback’и (добавлены, не ломают существующие):
Активность:
^actv:list$                                 # список доступных активностей
^actv:claim:(checkin|profile|bindcard|geocheckin)$

Рефералы:
^ref:my$                                    # показать мой код/ссылку и счётчики
^ref:stats:[0-9]+$                          # пагинация списка рефералов
^ref:copy$                                   # скопировать ссылку (UX-ответ)

Все тексты — i18n JSON. Существующие ключи не переименовывать/не удалять; новые — добавить.

1) Архитектура и стек (без изменений)
Python 3.11 • aiogram v3 • FastAPI • PostgreSQL 15 + PostGIS • SQLAlchemy 2 async + Alembic • Redis 7 • Docker • Prometheus/Grafana • Логи без PII.
Крипто: Fernet (QR скидки), HMAC-SHA256 (карта).

2) Категории и UX (без изменений логики)
🍽 Рестораны → Inline-фильтры (asia/europe/street/vege/all).
🧖‍♀️ SPA → список сразу (5/стр).
🚗 Транспорт → Reply-подменю (🛵/🚘/🚲) → список (5/стр).
🏨 Отели → список сразу (5/стр).
🚶‍♂️ Экскурсии → Reply-подменю (👥/🧑‍🤝‍🧑) → список (5/стр).
🛍 Магазины и услуги → список сразу (5/стр), без sub_slug, с модерацией/QR/лояльностью.

3) База данных
3.1 Каталог (как в v3)
listings.category ENUM('restaurants','spa','transport','hotels','tours','shops')
3.2 Карты (как в v3.1)
Таблицы: cards, card_bind_tokens, loyalty_card_events (event_type='bind' и др.).
3.3 Лояльность (расширения для v3.2)
В loyalty_transactions.reason добавить значения:
'activity', 'referral_bonus' (миграция ENUM — expand).
Новые таблицы (активности):
-- правила активностей
CREATE TABLE loyalty_activity_rules (
  id SERIAL PRIMARY KEY,
  code TEXT UNIQUE NOT NULL,               -- 'checkin', 'profile', 'bindcard', 'geocheckin'
  points INT NOT NULL,                     -- баллы за выполненную активность
  cooldown_seconds INT NOT NULL DEFAULT 86400,  -- анти-спам/кулдаун
  geo_required BOOL NOT NULL DEFAULT false,     -- для geocheckin
  min_distance_m INT NULL,                 -- радиус для geocheckin (например 50м)
  is_active BOOL NOT NULL DEFAULT true,
  start_at TIMESTAMPTZ NULL,
  end_at TIMESTAMPTZ NULL
);

-- журнал активности (идемпотентность и анти-фрод)
CREATE TABLE loyalty_activity_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id BIGINT NOT NULL REFERENCES users(id),
  rule_code TEXT NOT NULL,
  occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  meta JSONB NOT NULL DEFAULT '{}'         -- { "lat":..., "lng":..., "listing_id":... }
);

CREATE INDEX ix_activity_log_user_rule_time
  ON loyalty_activity_log(user_id, rule_code, occurred_at DESC);

Новые таблицы (рефералы):
-- реферальные коды пользователя
CREATE TABLE referral_codes (
  user_id BIGINT PRIMARY KEY REFERENCES users(id),
  code TEXT UNIQUE NOT NULL,               -- 'KARMA7F3D'
  link TEXT UNIQUE NOT NULL,               -- t.me/karma...?start=ref_KARMA7F3D
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- связи приглашений
CREATE TABLE referrals (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  inviter_user_id BIGINT NOT NULL REFERENCES users(id),
  invitee_user_id BIGINT NOT NULL REFERENCES users(id),
  status TEXT NOT NULL CHECK (status IN ('pending','activated','rewarded','rejected')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  activated_at TIMESTAMPTZ NULL
);

CREATE UNIQUE INDEX ux_ref_unique_pair
  ON referrals(inviter_user_id, invitee_user_id);

-- (опционально) агрегаты по реф.статистике, если понадобится

Инварианты/анти-фрод:
inviter_user_id != invitee_user_id
запрещать активацию, если phone_hash один и тот же у обоих
один invitee_user_id может иметь только одного инвайтера (первая успешная активация закрепляет связь)

4) FSM регистрации партнёра (как в v3)
Единый процесс; sub_slug только для restaurants/transport/tours; Redis TTL=48ч.

5) QR-скидки (как в v3)
Fernet payload=jti, TTL=24ч, redeem атомарный, Nginx rate-limit.

6) Пластиковая карта (как в v3.1)
Печать: CR80 PVC, матовая; QR на обеих сторонах; Card ID KS-1234-5678; Code-128 KS12345678.
Deeplink: startapp=bind&cid=...&t=...&sig=...&v=1 (HMAC; токен одноразовый; нет exp).
API: POST /api/cards/bind (атомаpность; коды ошибок).
POS (опция): earn/spend by card.

7) Баллы за активность (новое, v3.2)
7.1 Преднастроенные активности (правила по умолчанию)
checkin — ежедневный чект-ин в боте: +ACTIVITY_CHECKIN_POINTS (кулдаун 24ч).
profile — завершение профиля (язык, город, принятие политики): +ACTIVITY_PROFILE_POINTS (однократно).
bindcard — привязка пластиковой карты: +ACTIVITY_BINDCARD_POINTS (однократно).
geocheckin — гео-чект-ин в пределах полигона города (PostGIS, ≤ ACTIVITY_GEO_RADIUS_M м): +ACTIVITY_GEO_POINTS (кулдаун, например 24ч/город).
Все значения — настраиваются в loyalty_activity_rules и/или через .env по умолчанию.
7.2 Алгоритм начисления
Бот вызывает POST /api/loyalty/activity/claim с rule_code (+контекст, напр. lat/lng).
API проверяет: активность включена, окно дат, кулдаун для этого пользователя/правила, анти-фрод (гео, повтор).
В транзакции:
запись в loyalty_activity_log
запись loyalty_transactions (direction='earn', reason='activity', points=rule.points)
обновление loyalty_wallets.balance и lifetime_points (+возможный апгрейд tier)
Возврат { ok:true, points_awarded } или { ok:false, code }.
Коды ошибок: cooldown_active, rule_disabled, out_of_coverage, geo_required, daily_cap_exceeded.
7.3 Бот UX
В «👤 Личный кабинет» добавить Inline-кнопку: 🎯 Активность → ^actv:list$.
Экран «Активность»: список карточек (ежедневный чек-ин, заполнить профиль, привязать карту, гео-чек-ин) с кнопками CLAIM.
Кнопки:
Ежедневный чек-ин → ^actv:claim:checkin
Заполнить профиль → ^actv:claim:profile (если профиль ещё не полный)
Привязать карту → ^actv:claim:bindcard (если карта не привязана)
Гео-чек-ин → ^actv:claim:geocheckin (запросить геолокацию → проверка PostGIS)

8) Реферальная программа (новое, v3.2)
8.1 Механика
У каждого пользователя есть реф.код (напр. KARMA7F3D) и реф.ссылка: t.me/karma_system_bot?start=ref_KARMA7F3D.
Новый пользователь запускает бота по ссылке → создаётся связь pending (если валидно и не self-invite).
Активация реферала: при достижении порога активности (любым способом) — по умолчанию:
условие: суммарно начислить ≥ REFERRAL_ACTIVATION_MIN_POINTS (за QR/активности/карта)
или первый успешный redeem QR — если включено правилом
При активации: начисляем бонусы:
инвайтеру: REFERRAL_BONUS_INVITER
инвайти: REFERRAL_BONUS_INVITEE
Анти-фрод:
запрет self-invite
проверка phone_hash и, при наличии, card_id — не совпадают
дневной лимит активаций на инвайтера: REFERRAL_DAILY_CAP
анти-бот/рейт-лимит
Все начисления — через loyalty_transactions (reason='referral_bonus').
8.2 API
GET /api/referral/my — вернуть код/ссылку, счётчики (pending/activated/rewarded).
POST /api/referral/attach — привязать реф.код к текущему юзеру при старте (если без ссылки).
GET /api/referral/stats?page=&per_page= — список рефералов (для пользователя).
Админ:
GET /api/admin/referral/rules / POST /api/admin/referral/rules
параметры: activation_min_points, bonus_inviter, bonus_invitee, daily_cap, mode ('by_points'|'first_redeem').
8.3 Бот UX
В «👤 Личный кабинет» добавить Inline-кнопку: 👥 Рефералы → ^ref:my$.
Экран «Мои рефералы»: показать код, ссылку (копировать), счётчики, кнопка Посмотреть список → ^ref:stats:1.
Обработка deeplink start=ref_<CODE>: сохранить связь pending (если валид), показать приветствие и условия активации.

9) Сервисы и API (добавления)
9.1 Сервисы
card_service.py — как в v3.1 (привязка карты, HMAC).
activity_service.py — проверка правил/кулдаунов/гео, запись логов и транзакций.
referral_service.py — генерация кода/ссылки, привязка, проверка активации, выдача бонусов, лимиты.
9.2 API роуты (новые)
POST /api/loyalty/activity/claim { rule_code, geo?, listing_id? }
GET /api/referral/my, POST /api/referral/attach, GET /api/referral/stats
GET/POST /api/admin/referral/rules
(все — JWT user/admin; партнёр — не имеет доступа, кроме обычных лояльностных операций)

10) Бот: маршруты (добавления)
routers/start.py — обработка start=ref_<CODE> (pending связь) и startapp=bind... (карта).
routers/profile.py — экраны «🎯 Активность», «👥 Рефералы».
routers/activity.py — хендлеры ^actv:*.
routers/referral.py — хендлеры ^ref:*.
Единый контракт кнопок: новые ярлыки → новые i18n-ключи, единая маршрутизация в buttons.py, тест-линтер валидирует.

11) Безопасность
Карта: HMAC + одноразовый токен (hash), без exp → безопасно; rate-limit и анти-бот.
Активности: кулдауны, гео-проверки (PostGIS), дневные лимиты.
Рефералы: анти-фрод (self-invite, одинаковые phone_hash/card_id), дневной cap.
Разные секреты для Fernet/JWT/HMAC карты.
Логи без PII.

12) Кэш/инвалидация (без изменений)
Каталог — Redis + LISTEN/NOTIFY; активности и рефералы — не кэшируем, транзакционные операции.

13) Гео «Рядом» (без изменений)
PostGIS, coverage polygon, out_of_coverage.

14) Мониторинг (Prometheus)
Добавить:
activity_claim_total{rule_code,status="ok|err",code}
activity_claim_latency_seconds_bucket
referral_attach_total{status,code}
referral_activation_total{status,code}
cards_bind_attempts_total{status,code} (как в v3.1)
Алерты:
HighActivityErrorRate (>10% err за 10м)
HighReferralActivationErrorRate (>10% err за 10м)

15) Nginx (rate-limit)
limit_req_zone $binary_remote_addr zone=card_bind_zone:10m rate=5r/s;
limit_req_zone $binary_remote_addr zone=activity_zone:10m rate=5r/s;
limit_req_zone $binary_remote_addr zone=referral_zone:10m rate=5r/s;

server {
  location /api/cards/bind        { limit_req zone=card_bind_zone burst=10 nodelay; proxy_pass http://api:8000/api/cards/bind; }
  location /api/loyalty/activity/claim { limit_req zone=activity_zone burst=10 nodelay; proxy_pass http://api:8000/api/loyalty/activity/claim; }
  location /api/referral/          { limit_req zone=referral_zone  burst=10 nodelay; proxy_pass http://api:8000; }
}


16) Тестирование (pytest)
Unit
Активности: кулдаун, включённость правила, гео-радиус, дневные лимиты; reason='activity'.
Рефералы: attach, запрет self-invite, анти-фрод по phone_hash, активация по порогу, бонусы обоим, дневной cap; reason='referral_bonus'.
Карта: HMAC, одноразовый токен, повтор — отказ.
Конкурентность
10 параллельных activity/claim одного правила → ≤1 успешный по кулдауну.
10 параллельных активаций одного реферала → 1 успех, остальные отказ.
Integration
start=ref_CODE → pending; после достижения порога → activated → бонусы.
Профиль: экраны Активности/Рефералов; i18n.
Smoke
Привязать карту → чек-ин → гео-чек-ин → первый redeem → активация реферала (по сценарию) → начисления.

17) README / запуск (дополнить)
Миграции ENUM reason и новых таблиц.
Новые переменные .env.
Описание deeplink’ов start=ref_... и startapp=bind....
Smoke-сценарии для Активности и Рефералов.

18) .env (добавления)
Карты (как в v3.1):
CARD_HMAC_SECRET=__STRONG_RANDOM_32B__
CARD_ID_PREFIX=KS
CARD_KEY_VERSION=1
CARD_BIND_RATE_LIMIT=5r/s

Активности:
ACTIVITY_ENABLED=true
ACTIVITY_CHECKIN_POINTS=5
ACTIVITY_PROFILE_POINTS=20
ACTIVITY_BINDCARD_POINTS=30
ACTIVITY_GEO_POINTS=10
ACTIVITY_GEO_RADIUS_M=50
ACTIVITY_DAILY_EARN_CAP=5000

Рефералы:
REFERRAL_ENABLED=true
REFERRAL_ACTIVATION_MIN_POINTS=50     # порог для активации
REFERRAL_BONUS_INVITER=100
REFERRAL_BONUS_INVITEE=50
REFERRAL_DAILY_CAP=10


19) i18n — новые ключи (фрагмент)
Активности:
actv_title, actv_checkin, actv_profile, actv_bindcard, actv_geocheckin,
actv_claim_ok, actv_cooldown, actv_rule_disabled, actv_geo_required, actv_out_of_coverage, actv_daily_cap_exceeded.
Рефералы:
ref_title, ref_my_code, ref_my_link, ref_copy_link, ref_counters, ref_list_title,
ref_attach_ok, ref_self_invite_forbidden, ref_already_attached,
ref_activation_ok, ref_activation_pending, ref_activation_failed, ref_daily_cap_exceeded.
Карты (из v3.1):
card_bind_title, card_bind_success, card_bind_already_linked, card_bind_invalid_signature, card_bind_invalid_token, card_bind_token_used, card_bind_blocked, card_bind_rate_limited, card_bind_help, profile_bind_card_cta.

20) Структура репозитория (добавления)
/app
  /core
    /services
      card_service.py
      activity_service.py         # новое
      referral_service.py         # новое
  /api
    /routes
      cards.py                    # /api/cards/bind
      loyalty_activity.py         # /api/loyalty/activity/claim
      referral.py                 # /api/referral/*
      admin_referral.py           # /api/admin/referral/*
  /bot
    /routers
      start.py
      activity.py                 # ^actv:*
      referral.py                 # ^ref:*
    /constants
      buttons.py
  /db
    migrations/...(cards_*.py, activity_*.py, referral_*.py, loyalty_enum_reason_expand.py)
  /tests
    test_cards_bind.py
    test_activity_claim.py
    test_referral_flow.py
    # + существующие тесты v3


21) Единый контракт кнопок
Старые ярлыки — без изменений. Новые ярлыки («🎯 Активность», «👥 Рефералы») — новые i18n-ключи, добавлены в buttons.py.
test_buttons_contract_matrix.py валидирует консистентность.

22) История изменений (2025-08-27)
Добавлено: Активности (правила, лог, API, UX, i18n, мониторинг, тесты).
Добавлено: Рефералы (коды, ссылки, связь, активация, бонусы, API/UX/i18n, мониторинг, тесты).
Сохранено: Пластиковая карта (v3.1), все инварианты v3 (regex, UX, лояльность, контракт кнопок).
