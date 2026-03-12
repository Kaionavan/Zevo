# 🚀 Zevo

AI-боты для бизнеса. Платформа на Vercel + Telegram.

## Структура
```
zevo/
├── api/
│   └── webhook.py       ← Telegram бот (Vercel Serverless)
├── public/
│   └── index.html       ← Mini App дашборд
├── vercel.json          ← Конфиг Vercel
└── setup_webhook.py     ← Подключение webhook (запустить 1 раз)
```

## Деплой

### 1. GitHub
Создай репо и загрузи все файлы.

### 2. Vercel
- vercel.com → New Project → выбери репо
- Environment Variables:
  - `BOT_TOKEN`    = токен от @BotFather
  - `MINI_APP_URL` = https://твой-проект.vercel.app

### 3. Webhook (один раз после деплоя)
```bash
python setup_webhook.py ВАШ_ТОКЕН https://твой-проект.vercel.app
```

### 4. Готово!
Пиши боту /start 🎉
