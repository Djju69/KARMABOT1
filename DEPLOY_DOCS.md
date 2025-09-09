# 🚀 Развертывание документации на docs.karma-system.com

## ✅ **ЧТО ГОТОВО:**
- HTML файлы созданы в папке `karma-docs/`
- Ссылки в боте настроены на `https://docs.karma-system.com`
- Структура папок соответствует требуемым путям

## 🔧 **ЧТО НУЖНО СДЕЛАТЬ:**

### **Вариант 1: GitBook (рекомендуется)**
1. Зайдите на https://app.gitbook.com
2. Создайте новое пространство
3. Импортируйте содержимое `EXTERNAL_DOCUMENTATION_TEMPLATES.md`
4. Разбейте на страницы по разделам:
   - `/user/start` - Регистрация и первые шаги
   - `/user/discounts` - Как работают скидки
   - `/user/points` - Баллы: копить и тратить
   - `/user/qr` - Оплата через QR
   - `/partner/become` - Как стать партнёром
   - `/partner/create-place` - Создание заведений
   - `/partner/qr-scan` - Сканирование QR-кодов
   - `/faq` - FAQ
   - `/troubleshooting` - Решение проблем
5. Включите Public access
6. Подключите кастомный домен `docs.karma-system.com`
7. Настройте DNS: CNAME `docs` → (CNAME от GitBook)

### **Вариант 2: Cloudflare Pages**
1. Зайдите на https://pages.cloudflare.com
2. Создайте новый проект
3. Загрузите папку `karma-docs/`
4. Подключите домен `docs.karma-system.com`
5. Настройте DNS: CNAME `docs` → (CNAME от Cloudflare)

### **Вариант 3: Vercel**
1. Зайдите на https://vercel.com
2. Создайте новый проект
3. Загрузите папку `karma-docs/`
4. Подключите домен `docs.karma-system.com`
5. Настройте DNS: CNAME `docs` → (CNAME от Vercel)

## ✅ **ПРОВЕРКА:**
После развертывания проверьте:
```bash
curl -I https://docs.karma-system.com/user/start
curl -I https://docs.karma-system.com/user/discounts
curl -I https://docs.karma-system.com/user/points
curl -I https://docs.karma-system.com/user/qr
curl -I https://docs.karma-system.com/partner/become
curl -I https://docs.karma-system.com/partner/create-place
curl -I https://docs.karma-system.com/partner/qr-scan
curl -I https://docs.karma-system.com/faq
curl -I https://docs.karma-system.com/troubleshooting
```

Все должны возвращать `200 OK` или `301/302 → 200`.

## 🎯 **РЕЗУЛЬТАТ:**
После развертывания ссылки в боте будут работать:
- `/help` - покажет справку с рабочими ссылками
- Все ссылки будут вести на `https://docs.karma-system.com/...`
- Только поддержка ведёт на `https://t.me/karma_system_official`
