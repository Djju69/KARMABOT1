# KarmaSystem Documentation

## 🚀 Развертывание на Cloudflare Pages

### 1. Загрузите папку `karma-docs` на Cloudflare Pages

### 2. Настройте домен
- В настройках Pages добавьте кастомный домен: `docs.karma-system.com`
- Cloudflare автоматически выдаст CNAME запись

### 3. DNS настройки
```
Тип: CNAME
Имя: docs
Значение: (CNAME от Cloudflare Pages)
```

### 4. SSL
- Cloudflare автоматически включит SSL
- Домен будет доступен по HTTPS

## 📁 Структура файлов
```
karma-docs/
├── index.html
├── user/
│   ├── start/index.html
│   ├── discounts/index.html
│   ├── points/index.html
│   └── qr/index.html
├── partner/
│   ├── become/index.html
│   ├── create-place/index.html
│   └── qr-scan/index.html
├── faq/index.html
└── troubleshooting/index.html
```

## 🔗 URL после развертывания
- https://docs.karma-system.com/user/start
- https://docs.karma-system.com/user/discounts
- https://docs.karma-system.com/user/points
- https://docs.karma-system.com/user/qr
- https://docs.karma-system.com/partner/become
- https://docs.karma-system.com/partner/create-place
- https://docs.karma-system.com/partner/qr-scan
- https://docs.karma-system.com/faq
- https://docs.karma-system.com/troubleshooting

## ⚡ Быстрый старт
1. Зайдите на https://pages.cloudflare.com
2. Создайте новый проект
3. Загрузите папку `karma-docs`
4. Настройте домен `docs.karma-system.com`
5. Готово!
