import json
import os
import urllib.request
from http.server import BaseHTTPRequestHandler

TOKEN = os.environ.get("BOT_TOKEN", "")
MINI_APP_URL = os.environ.get("MINI_APP_URL", "")
API = f"https://api.telegram.org/bot{TOKEN}"

# --- Простое хранилище (заменить на БД в продакшне) ---
db = {}        # {uid: {name, category, description, plan, stats}}
states = {}    # {uid: {state, ...temp data}}

CATEGORIES = {
    "cat_cafe":    "🍕 Кафе / Ресторан",
    "cat_salon":   "💇 Салон красоты",
    "cat_shop":    "🛍 Магазин",
    "cat_fitness": "🏋️ Фитнес / Спорт",
    "cat_medical": "🏥 Медицина",
    "cat_other":   "📦 Другое",
}

PLANS = {
    "free":    {"emoji": "🆓", "name": "Free",    "price": 0,  "limit": 100},
    "starter": {"emoji": "⚡", "name": "Starter", "price": 29, "limit": 1000},
    "pro":     {"emoji": "🚀", "name": "Pro",     "price": 79, "limit": 99999},
}

# ── Telegram helpers ──────────────────────────────────────────────────────────

def tg(method, **kwargs):
    req = urllib.request.Request(
        f"{API}/{method}",
        data=json.dumps(kwargs).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        urllib.request.urlopen(req)
    except Exception as e:
        print(f"TG error [{method}]: {e}")

def send(chat_id, text, kb=None, parse_mode="Markdown"):
    kw = dict(chat_id=chat_id, text=text, parse_mode=parse_mode)
    if kb:
        kw["reply_markup"] = json.dumps(kb)
    tg("sendMessage", **kw)

def edit(chat_id, msg_id, text, kb=None, parse_mode="Markdown"):
    kw = dict(chat_id=chat_id, message_id=msg_id, text=text, parse_mode=parse_mode)
    if kb:
        kw["reply_markup"] = json.dumps(kb)
    tg("editMessageText", **kw)

def answer(cq_id):
    tg("answerCallbackQuery", callback_query_id=cq_id)

# ── Keyboards ─────────────────────────────────────────────────────────────────

def kb_start():
    return {"inline_keyboard": [
        [{"text": "🚀 Подключить бота для бизнеса", "callback_data": "register"}],
        [{"text": "📖 Как это работает", "callback_data": "how"},
         {"text": "💰 Тарифы", "callback_data": "plans"}],
    ]}

def kb_back(to):
    return {"inline_keyboard": [[{"text": "◀️ Назад", "callback_data": to}]]}

def kb_categories():
    return {"inline_keyboard": [
        [{"text": "🍕 Кафе/Ресторан",  "callback_data": "cat_cafe"},
         {"text": "💇 Салон красоты",   "callback_data": "cat_salon"}],
        [{"text": "🛍 Магазин",         "callback_data": "cat_shop"},
         {"text": "🏋️ Фитнес",         "callback_data": "cat_fitness"}],
        [{"text": "🏥 Медицина",        "callback_data": "cat_medical"},
         {"text": "📦 Другое",          "callback_data": "cat_other"}],
    ]}

def kb_dashboard():
    rows = [
        [{"text": "📊 Статистика",      "callback_data": "stats"},
         {"text": "⚙️ Настройки",       "callback_data": "settings"}],
        [{"text": "✏️ Заказать правки", "callback_data": "edit_req"},
         {"text": "💰 Тариф",           "callback_data": "plan"}],
    ]
    if MINI_APP_URL:
        rows.append([{"text": "📱 Открыть панель управления",
                      "web_app": {"url": MINI_APP_URL}}])
    return {"inline_keyboard": rows}

def kb_settings():
    return {"inline_keyboard": [
        [{"text": "📝 Описание бизнеса", "callback_data": "set_desc"}],
        [{"text": "🕐 Часы работы",      "callback_data": "set_hours"}],
        [{"text": "📋 Меню / Услуги",    "callback_data": "set_menu"}],
        [{"text": "◀️ Назад",            "callback_data": "dashboard"}],
    ]}

# ── Texts ─────────────────────────────────────────────────────────────────────

def text_welcome(name):
    return (
        f"👋 Привет, *{name}*!\n\n"
        "*Zevo* — платформа AI-ботов для вашего бизнеса.\n\n"
        "✅ Отвечает клиентам 24/7\n"
        "✅ Принимает заказы и бронирования\n"
        "✅ Статистика в реальном времени\n"
        "✅ Настройка за 5 минут — без кода"
    )

def text_dashboard(uid):
    biz = db[uid]
    s = biz["stats"]
    p = PLANS[biz["plan"]]
    return (
        f"🏢 *{biz['name']}*\n"
        f"📂 {biz['category']}  •  {p['emoji']} {p['name']}\n\n"
        f"📈 *Сегодня:*\n"
        f"  💬 Сообщений: *{s['today']}*\n"
        f"  👥 Пользователей: *{s['users']}*\n"
        f"  🛒 Заказов: *{s['orders']}*\n\n"
        f"За всё время: {s['total']} сообщений"
    )

# ── Handlers ──────────────────────────────────────────────────────────────────

def on_start(uid, name, chat_id):
    if uid in db:
        send(chat_id, text_dashboard(uid), kb_dashboard())
    else:
        send(chat_id, text_welcome(name), kb_start())

def on_callback(uid, chat_id, msg_id, data, cq_id):
    answer(cq_id)

    # ── Стартовые экраны ──
    if data == "how":
        edit(chat_id, msg_id,
             "📖 *Как работает Zevo?*\n\n"
             "1️⃣ Регистрируете бизнес\n"
             "2️⃣ Настраиваете бота под себя\n"
             "3️⃣ Даёте ссылку клиентам\n"
             "4️⃣ Бот работает сам — отвечает, принимает заказы\n"
             "5️⃣ Видите всю статистику в дашборде\n\n"
             "⏱ Настройка занимает *5 минут*",
             {"inline_keyboard": [
                 [{"text": "🚀 Начать", "callback_data": "register"},
                  {"text": "◀️ Назад",  "callback_data": "start"}]
             ]})

    elif data == "plans":
        edit(chat_id, msg_id,
             "💰 *Тарифы Zevo*\n\n"
             "🆓 *Free* — бесплатно\n"
             "  • До 100 сообщений/мес\n"
             "  • 1 бот\n\n"
             "⚡ *Starter* — $29/мес\n"
             "  • До 1 000 сообщений/мес\n"
             "  • До 3 ботов\n"
             "  • Расширенная статистика\n\n"
             "🚀 *Pro* — $79/мес\n"
             "  • Безлимит сообщений\n"
             "  • Безлимит ботов\n"
             "  • Кастомный AI-персонаж\n"
             "  • Приоритетная поддержка",
             {"inline_keyboard": [
                 [{"text": "🚀 Начать бесплатно", "callback_data": "register"}],
                 [{"text": "◀️ Назад", "callback_data": "start"}],
             ]})

    elif data == "start":
        if uid in db:
            edit(chat_id, msg_id, text_dashboard(uid), kb_dashboard())
        else:
            edit(chat_id, msg_id, text_welcome(""), kb_start())

    # ── Регистрация ──
    elif data == "register":
        states[uid] = {"step": "name"}
        edit(chat_id, msg_id,
             "🏢 *Регистрация*\n\nКак называется ваш бизнес?\n\n"
             "_Например: Кафе Уют, Магазин TechStore_",
             kb_back("start"))

    elif data.startswith("cat_") and data in CATEGORIES:
        if uid in states:
            states[uid]["category"] = CATEGORIES[data]
            states[uid]["step"] = "desc"
        edit(chat_id, msg_id,
             f"✅ *{CATEGORIES[data]}*\n\n"
             "Опишите ваш бизнес в 2–3 предложениях.\n\n"
             "_AI будет использовать это для ответов клиентам._")

    # ── Дашборд ──
    elif data == "dashboard":
        if uid in db:
            edit(chat_id, msg_id, text_dashboard(uid), kb_dashboard())

    elif data == "stats":
        if uid not in db:
            return
        s = db[uid]["stats"]
        edit(chat_id, msg_id,
             f"📊 *Статистика — {db[uid]['name']}*\n\n"
             f"📅 *Сегодня:*\n"
             f"  💬 Сообщений: {s['today']}\n"
             f"  👥 Новых пользователей: 0\n\n"
             f"📆 *За всё время:*\n"
             f"  💬 Сообщений: {s['total']}\n"
             f"  👥 Всего клиентов: {s['users']}\n"
             f"  🛒 Заказов: {s['orders']}",
             kb_back("dashboard"))

    elif data == "settings":
        if uid in db:
            edit(chat_id, msg_id,
                 f"⚙️ *Настройки — {db[uid]['name']}*\n\nЧто хотите изменить?",
                 kb_settings())

    elif data in ("set_desc", "set_hours", "set_menu"):
        labels = {
            "set_desc":  ("📝 Описание бизнеса", "s_desc"),
            "set_hours": ("🕐 Часы работы",       "s_hours"),
            "set_menu":  ("📋 Меню / Услуги",     "s_menu"),
        }
        label, step = labels[data]
        states[uid] = {"step": step}
        edit(chat_id, msg_id,
             f"*{label}*\n\nНапишите и отправьте текст:",
             kb_back("settings"))

    elif data == "edit_req":
        states[uid] = {"step": "edit_req"}
        edit(chat_id, msg_id,
             "✏️ *Заказать правки*\n\n"
             "Опишите что нужно изменить в боте:\n\n"
             "_Например: добавить новые блюда, изменить часы, добавить кнопку записи_",
             kb_back("dashboard"))

    elif data == "plan":
        if uid not in db:
            return
        p = PLANS[db[uid]["plan"]]
        edit(chat_id, msg_id,
             f"💰 *Ваш тариф: {p['emoji']} {p['name']}*\n\n"
             f"Лимит: {p['limit']} сообщений/мес\n\n"
             "Upgrade для снятия ограничений 👇",
             {"inline_keyboard": [
                 [{"text": "⚡ Starter — $29/мес", "callback_data": "up_starter"}],
                 [{"text": "🚀 Pro — $79/мес",     "callback_data": "up_pro"}],
                 [{"text": "◀️ Назад",              "callback_data": "dashboard"}],
             ]})

    elif data in ("up_starter", "up_pro"):
        if uid in db:
            db[uid]["plan"] = "starter" if data == "up_starter" else "pro"
            p = PLANS[db[uid]["plan"]]
            edit(chat_id, msg_id,
                 f"🎉 *Тариф обновлён: {p['emoji']} {p['name']}*\n\n"
                 "Спасибо за доверие!",
                 kb_back("dashboard"))

def on_message(uid, chat_id, text):
    st = states.get(uid, {})
    step = st.get("step")

    if step == "name":
        states[uid]["name"] = text
        states[uid]["step"] = "category"
        send(chat_id,
             f"✅ *{text}*\n\nВыберите категорию:",
             kb_categories())

    elif step == "desc":
        name = st.get("name", "Бизнес")
        cat  = st.get("category", "📦 Другое")
        db[uid] = {
            "name": name, "category": cat, "description": text,
            "plan": "free",
            "stats": {"today": 0, "total": 0, "users": 0, "orders": 0},
        }
        states.pop(uid, None)
        send(chat_id,
             f"🎉 *{name}* успешно зарегистрирован!\n\n"
             f"📂 {cat}\n\n"
             "Ваш AI-бот готов к работе 👇",
             kb_dashboard())

    elif step == "edit_req":
        states.pop(uid, None)
        send(chat_id,
             "✅ *Заявка принята!*\n\n"
             "Мы свяжемся с вами в течение 24 часов.",
             kb_back("dashboard"))

    elif step in ("s_desc", "s_hours", "s_menu"):
        labels = {"s_desc": "Описание", "s_hours": "Часы работы", "s_menu": "Меню/Услуги"}
        states.pop(uid, None)
        send(chat_id,
             f"✅ *{labels[step]} сохранено!*",
             kb_back("settings"))

    else:
        if uid in db:
            send(chat_id, text_dashboard(uid), kb_dashboard())
        else:
            send(chat_id, "Напиши /start чтобы начать 👋")

# ── Vercel handler ────────────────────────────────────────────────────────────

class handler(BaseHTTPRequestHandler):

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length))

        try:
            if "callback_query" in body:
                cq   = body["callback_query"]
                uid  = cq["from"]["id"]
                cid  = cq["message"]["chat"]["id"]
                mid  = cq["message"]["message_id"]
                data = cq["data"]
                on_callback(uid, cid, mid, data, cq["id"])

            elif "message" in body:
                msg  = body["message"]
                uid  = msg["from"]["id"]
                cid  = msg["chat"]["id"]
                text = msg.get("text", "")
                name = msg["from"].get("first_name", "друг")

                if text.startswith("/start"):
                    on_start(uid, name, cid)
                else:
                    on_message(uid, cid, text)

        except Exception as e:
            print(f"Error: {e}")

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Zevo is alive!")

    def log_message(self, *args):
        pass
