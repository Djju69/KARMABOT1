# 🚨 ОТЛАДКА WEBAPP ПРОБЛЕМЫ

## 🔍 ПРОВЕРКА КОДА

### 1. ПРОВЕРИТЬ ЛОГИ БОТА
После нажатия кнопки "🌐 Открыть Личный кабинет" в логах должно быть:
```
WebApp URL created for user XXXX (user): https://webbot-production-42fe.up.railway.app/user-cabinet.html
```

### 2. ПРОВЕРИТЬ ДОСТУПНОСТЬ ФАЙЛОВ
- `https://webbot-production-42fe.up.railway.app/` - основная страница
- `https://webbot-production-42fe.up.railway.app/user-cabinet.html` - кабинет
- `https://webbot-production-42fe.up.railway.app/webapp/` - WebApp папка

### 3. ПРОВЕРИТЬ НАСТРОЙКИ
- WEBAPP_BASE_URL = https://webbot-production-42fe.up.railway.app
- Порт 8080 настроен
- Домен активен

## 🛠️ ВОЗМОЖНЫЕ ПРОБЛЕМЫ

### A. ПРОБЛЕМА С СТАТИЧЕСКОЙ РАЗДАЧЕЙ
В `web/main.py` должно быть:
```python
app.mount("/webapp", StaticFiles(directory="webapp", html=True), name="webapp")
```

### B. ПРОБЛЕМА С ПУТЯМИ
WebApp файлы должны быть в папке `webapp/`:
- `webapp/user-cabinet.html`
- `webapp/partner-cabinet.html` 
- `webapp/admin-cabinet.html`

### C. ПРОБЛЕМА С ПОРТОМ
Бот должен слушать порт 8080 и раздавать статические файлы

## 🧪 ТЕСТИРОВАНИЕ

### 1. ПРОВЕРИТЬ ОСНОВНУЮ СТРАНИЦУ
Открой `https://webbot-production-42fe.up.railway.app/`
- Должна загружаться страница бота
- НЕ должно быть 502 ошибки

### 2. ПРОВЕРИТЬ WEBAPP ПАПКУ
Открой `https://webbot-production-42fe.up.railway.app/webapp/`
- Должен показывать список файлов
- Или автоматически открывать index.html

### 3. ПРОВЕРИТЬ КАБИНЕТЫ
- `https://webbot-production-42fe.up.railway.app/user-cabinet.html`
- `https://webbot-production-42fe.up.railway.app/partner-cabinet.html`
- `https://webbot-production-42fe.up.railway.app/admin-cabinet.html`

## ⚠️ ВАЖНО

Если основная страница не работает - проблема в настройках домена
Если основная страница работает, но кабинеты нет - проблема в коде
