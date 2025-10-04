# Быстрая настройка тестирования KARMABOT1

## Шаг 1: Получить токен бота
```bash
python get_bot_token.py
```
Следуй инструкциям и вставь токен от @BotFather

## Шаг 2: Получить свой Telegram ID
```bash
python get_user_id.py
```
Следуй инструкциям и вставь ID от @userinfobot

## Шаг 3: Настроить Railway
1. Зайди на railway.app
2. Открой проект KARMABOT1
3. Variables → New Variable
4. DISABLE_WEBHOOK = true
5. Подожди 1 минуту

## Шаг 4: Запустить тесты
```bash
python test_karmabot_full.py
```

## Шаг 5: Вернуть webhook
Railway → Variables → DISABLE_WEBHOOK = false

---
