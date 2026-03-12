# 🚀 Zevo — AI Bot Platform

Платформа для создания AI-ботов для бизнеса.

## Структура
```
zevo/
├── bot.py          # Главный бот платформы
├── requirements.txt
└── miniapp/
    └── index.html  # Mini App дашборд
```

## Деплой

### 1. Railway (бот)
1. Создай новый проект на railway.app
2. Подключи GitHub репо
3. Добавь переменные окружения:
   - `BOT_TOKEN` — токен от BotFather
   - `MINI_APP_URL` — URL задеплоенного Mini App
   - `ADMIN_ID` — твой Telegram ID

### 2. Vercel / GitHub Pages (Mini App)
1. Загрузи папку `miniapp/` на Vercel или GitHub Pages
2. Скопируй URL и вставь в `MINI_APP_URL` на Railway

## Следующие шаги
- [ ] Подключить реальную БД (PostgreSQL)
- [ ] Добавить генерацию клиентских ботов
- [ ] Подключить Groq AI для ответов
- [ ] Система оплаты (Telegram Stars / Stripe)
