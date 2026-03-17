import json
import os
import urllib.request
from http.server import BaseHTTPRequestHandler

TOKEN        = os.environ.get("BOT_TOKEN", "")
MINI_APP_URL = os.environ.get("MINI_APP_URL", "")
CARD_VISA    = os.environ.get("CARD_VISA", "")
CARD_HUMO    = os.environ.get("CARD_HUMO", "")
ADMIN_ID     = int(os.environ.get("ADMIN_ID", "7732138103"))
KV_URL       = os.environ.get("KV_REST_API_URL", "")
KV_TOKEN     = os.environ.get("KV_REST_API_TOKEN", "")
API          = f"https://api.telegram.org/bot{TOKEN}"

PLANS = {
    "free":    {"emoji": "🆓", "name": "Free",    "price": 0,   "limit": 100},
    "starter": {"emoji": "⚡", "name": "Starter", "price": 29,  "limit": 1000},
    "pro":     {"emoji": "🚀", "name": "Pro",     "price": 79,  "limit": 99999},
}

CATEGORIES_RU = {
    "cat_cafe": "🍕 Кафе/Ресторан", "cat_salon": "💇 Салон красоты",
    "cat_shop": "🛍 Магазин",        "cat_fitness": "🏋️ Фитнес",
    "cat_medical": "🏥 Медицина",    "cat_other": "📦 Другое",
}

LANGS = {
    "ru": "🇷🇺 Русский", "en": "🇬🇧 English", "uz": "🇺🇿 O'zbek",
    "kz": "🇰🇿 Қазақша", "zh": "🇨🇳 中文",    "ko": "🇰🇷 한국어",
}

# ── Upstash KV ────────────────────────────────────────────────────────────────

def kv_get(key):
    if not KV_URL: return None
    try:
        req = urllib.request.Request(
            f"{KV_URL}/get/{key}",
            headers={"Authorization": f"Bearer {KV_TOKEN}"}
        )
        res = json.loads(urllib.request.urlopen(req, timeout=3).read())
        val = res.get("result")
        return json.loads(val) if val else None
    except:
        return None

def kv_set(key, value, ex=None):
    if not KV_URL: return
    try:
        args = [key, json.dumps(value)]
        if ex:
            args += ["EX", str(ex)]
        req = urllib.request.Request(
            f"{KV_URL}/set/{'/'.join(str(a) for a in args)}",
            headers={"Authorization": f"Bearer {KV_TOKEN}"},
            method="POST"
        )
        urllib.request.urlopen(req, timeout=3)
    except Exception as e:
        print(f"KV set error: {e}")

def kv_del(key):
    if not KV_URL: return
    try:
        req = urllib.request.Request(
            f"{KV_URL}/del/{key}",
            headers={"Authorization": f"Bearer {KV_TOKEN}"},
            method="POST"
        )
        urllib.request.urlopen(req, timeout=3)
    except:
        pass

def get_user(uid):
    return kv_get(f"user:{uid}") or {}

def set_user(uid, data):
    kv_set(f"user:{uid}", data)

def get_state(uid):
    return kv_get(f"state:{uid}") or {}

def set_state(uid, data):
    kv_set(f"state:{uid}", data, ex=3600)

def del_state(uid):
    kv_del(f"state:{uid}")

def get_pending(uid):
    return kv_get(f"pending:{uid}")

def set_pending(uid, plan):
    kv_set(f"pending:{uid}", plan, ex=86400)

# ── Telegram helpers ──────────────────────────────────────────────────────────

def tg(method, **kwargs):
    req = urllib.request.Request(
        f"{API}/{method}",
        data=json.dumps(kwargs).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        urllib.request.urlopen(req, timeout=5)
    except Exception as e:
        print(f"TG error [{method}]: {e}")

def send(chat_id, text, kb=None, parse_mode="Markdown"):
    kw = dict(chat_id=chat_id, text=text, parse_mode=parse_mode)
    if kb: kw["reply_markup"] = json.dumps(kb)
    tg("sendMessage", **kw)

def edit(chat_id, msg_id, text, kb=None, parse_mode="Markdown"):
    kw = dict(chat_id=chat_id, message_id=msg_id, text=text, parse_mode=parse_mode)
    if kb: kw["reply_markup"] = json.dumps(kb)
    tg("editMessageText", **kw)

def answer(cq_id):
    tg("answerCallbackQuery", callback_query_id=cq_id)

# ── Translations ──────────────────────────────────────────────────────────────

T = {
    "welcome": {
        "ru": "👋 Привет, *{name}*!\n\n*Zevo* — платформа AI-ботов для вашего бизнеса.\n\n✅ Отвечает клиентам 24/7\n✅ Принимает заказы и бронирования\n✅ Статистика в реальном времени\n✅ Настройка за 5 минут — без кода",
        "en": "👋 Hello, *{name}*!\n\n*Zevo* — AI bot platform for your business.\n\n✅ Replies to clients 24/7\n✅ Accepts orders & bookings\n✅ Real-time statistics\n✅ Setup in 5 minutes — no code",
        "uz": "👋 Salom, *{name}*!\n\n*Zevo* — biznesingiz uchun AI-bot platformasi.\n\n✅ Mijozlarga 24/7 javob beradi\n✅ Buyurtma va bronlarni qabul qiladi\n✅ Real vaqtda statistika\n✅ 5 daqiqada sozlash — kodsiz",
        "kz": "👋 Сәлем, *{name}*!\n\n*Zevo* — бизнесіңіз үшін AI-бот платформасы.\n\n✅ Клиенттерге 24/7 жауап береді\n✅ Тапсырыстар мен брондауларды қабылдайды\n✅ Нақты уақытта статистика\n✅ 5 минутта баптау — коссыз",
        "zh": "👋 你好, *{name}*!\n\n*Zevo* — 企业AI机器人平台。\n\n✅ 24/7回复客户\n✅ 接受订单和预订\n✅ 实时统计\n✅ 5分钟设置",
        "ko": "👋 안녕하세요, *{name}*!\n\n*Zevo* — 비즈니스를 위한 AI 봇 플랫폼.\n\n✅ 24/7 고객 응답\n✅ 주문 및 예약 수락\n✅ 실시간 통계\n✅ 5분 설정",
    },
    "register_btn": {"ru":"🚀 Подключить бота","en":"🚀 Connect bot","uz":"🚀 Bot ulash","kz":"🚀 Бот қосу","zh":"🚀 接入机器人","ko":"🚀 봇 연결"},
    "how_btn":      {"ru":"📖 Как это работает","en":"📖 How it works","uz":"📖 Qanday ishlaydi","kz":"📖 Қалай жұмыс","zh":"📖 如何使用","ko":"📖 사용 방법"},
    "plans_btn":    {"ru":"💰 Тарифы","en":"💰 Plans","uz":"💰 Tariflar","kz":"💰 Тарифтер","zh":"💰 套餐","ko":"💰 요금제"},
    "back_btn":     {"ru":"◀️ Назад","en":"◀️ Back","uz":"◀️ Orqaga","kz":"◀️ Артқа","zh":"◀️ 返回","ko":"◀️ 뒤로"},
    "lang_btn":     {"ru":"🌍 Язык","en":"🌍 Language","uz":"🌍 Til","kz":"🌍 Тіл","zh":"🌍 语言","ko":"🌍 언어"},
    "stats_btn":    {"ru":"📊 Статистика","en":"📊 Statistics","uz":"📊 Statistika","kz":"📊 Статистика","zh":"📊 统计","ko":"📊 통계"},
    "settings_btn": {"ru":"⚙️ Настройки","en":"⚙️ Settings","uz":"⚙️ Sozlamalar","kz":"⚙️ Параметрлер","zh":"⚙️ 设置","ko":"⚙️ 설정"},
    "edit_btn":     {"ru":"✏️ Заказать правки","en":"✏️ Request changes","uz":"✏️ O'zgarish","kz":"✏️ Өзгерту","zh":"✏️ 请求修改","ko":"✏️ 수정 요청"},
    "plan_btn":     {"ru":"💰 Тариф","en":"💰 Plan","uz":"💰 Tarif","kz":"💰 Тариф","zh":"💰 套餐","ko":"💰 요금제"},
    "open_btn":     {"ru":"📱 Открыть панель","en":"📱 Open dashboard","uz":"📱 Panelni ochish","kz":"📱 Панельді ашу","zh":"📱 打开面板","ko":"📱 대시보드 열기"},
    "reg_name":     {"ru":"🏢 *Регистрация*\n\nКак называется ваш бизнес?","en":"🏢 *Registration*\n\nWhat is your business name?","uz":"🏢 *Ro'yxatdan o'tish*\n\nBiznesingiz nomi?","kz":"🏢 *Тіркеу*\n\nБизнесіңіздің атауы?","zh":"🏢 *注册*\n\n企业名称？","ko":"🏢 *등록*\n\n비즈니스 이름?"},
    "reg_cat":      {"ru":"Выберите категорию:","en":"Choose category:","uz":"Kategoriya tanlang:","kz":"Санатты таңдаңыз:","zh":"选择类别：","ko":"카테고리 선택:"},
    "reg_desc":     {"ru":"Опишите ваш бизнес в 2–3 предложениях.\n\n_AI будет использовать это для ответов клиентам._","en":"Describe your business in 2-3 sentences.\n\n_AI will use this to answer clients._","uz":"Biznesingizni 2-3 jumlada tasvirlab bering.\n\n_AI bu ma'lumotdan foydalanadi._","kz":"Бизнесіңізді 2-3 сөйлеммен сипаттаңыз.","zh":"用2-3句话描述您的企业。","ko":"비즈니스를 2-3문장으로 설명해 주세요."},
    "registered":   {"ru":"🎉 *{name}* зарегистрирован!\n\nВаш AI-бот готов 👇","en":"🎉 *{name}* registered!\n\nYour AI bot is ready 👇","uz":"🎉 *{name}* ro'yxatdan o'tdi!\n\nBot tayyor 👇","kz":"🎉 *{name}* тіркелді!\n\nБот дайын 👇","zh":"🎉 *{name}* 已注册！\n\n机器人就绪 👇","ko":"🎉 *{name}* 등록!\n\n봇 준비 완료 👇"},
    "payment_text": {"ru":"💳 *Оплата — {plan}*\n\nСумма: *${price}/мес*\n\nПереведите на карту:\n{cards}\nПосле оплаты отправьте скрин чека 👇","en":"💳 *Payment — {plan}*\n\nAmount: *${price}/mo*\n\nTransfer to card:\n{cards}\nSend receipt screenshot 👇","uz":"💳 *To'lov — {plan}*\n\nSumma: *${price}/oy*\n\nKartaga o'tkazing:\n{cards}\nChek rasmini yuboring 👇","kz":"💳 *Төлем — {plan}*\n\nСома: *${price}/ай*\n\nКартаға аударыңыз:\n{cards}\nЧек жіберіңіз 👇","zh":"💳 *付款 — {plan}*\n\n金额: *${price}/月*\n\n转账到卡片:\n{cards}\n发送收据截图 👇","ko":"💳 *결제 — {plan}*\n\n금액: *${price}/월*\n\n카드로 이체:\n{cards}\n영수증 스크린샷 보내기 👇"},
    "check_sent_btn":{"ru":"✅ Я отправил чек","en":"✅ I sent receipt","uz":"✅ Chekni yubordim","kz":"✅ Чекті жібердім","zh":"✅ 已发送收据","ko":"✅ 영수증 보냄"},
    "send_check":   {"ru":"📸 Отправьте скрин чека об оплате 👇\n\n_Проверим в течение 10 минут_","en":"📸 Send payment receipt screenshot 👇\n\n_We'll verify within 10 minutes_","uz":"📸 To'lov chekini yuboring 👇\n\n_10 daqiqa ichida tekshiramiz_","kz":"📸 Чек скриншотын жіберіңіз 👇","zh":"📸 发送付款收据截图 👇","ko":"📸 결제 영수증 보내기 👇"},
    "check_received":{"ru":"✅ *Чек получен!*\n\nПроверяем — до 10 минут. После подтверждения тариф активируется 🎉","en":"✅ *Receipt received!*\n\nChecking — up to 10 min. Plan activates after confirmation 🎉","uz":"✅ *Chek qabul qilindi!*\n\nTekshiruv — 10 daqiqa. Tarif faollashadi 🎉","kz":"✅ *Чек алынды!*\n\nТексеру — 10 мин. Тариф іске қосылады 🎉","zh":"✅ *收到收据！*\n\n检查中 — 最多10分钟 🎉","ko":"✅ *영수증 수령!*\n\n확인 중 — 최대 10분 🎉"},
    "confirmed":    {"ru":"🎉 *Оплата подтверждена!*\n\nТариф *{plan}* активирован. Спасибо! 🙏","en":"🎉 *Payment confirmed!*\n\n*{plan}* activated. Thank you! 🙏","uz":"🎉 *To'lov tasdiqlandi!*\n\n*{plan}* faollashdi. Rahmat! 🙏","kz":"🎉 *Төлем расталды!*\n\n*{plan}* іске қосылды. Рахмет! 🙏","zh":"🎉 *付款已确认！*\n\n*{plan}* 已激活。谢谢！🙏","ko":"🎉 *결제 확인!*\n\n*{plan}* 활성화. 감사합니다! 🙏"},
    "rejected":     {"ru":"❌ *Оплата не подтверждена*\n\nЧек не прошёл проверку. Свяжитесь с поддержкой.","en":"❌ *Payment not confirmed*\n\nReceipt failed. Contact support.","uz":"❌ *To'lov tasdiqlanmadi*\n\nQo'llab-quvvatlash bilan bog'laning.","kz":"❌ *Төлем расталмады*\n\nҚолдауға хабарласыңыз.","zh":"❌ *付款未确认*\n\n请联系支持。","ko":"❌ *결제 미확인*\n\n지원팀에 문의하세요."},
    "edit_req_text":{"ru":"✏️ *Заказать правки*\n\nОпишите что нужно изменить:","en":"✏️ *Request changes*\n\nDescribe what to change:","uz":"✏️ *O'zgarish*\n\nNimani o'zgartirish kerak:","kz":"✏️ *Өзгерту*\n\nНені өзгерту керек:","zh":"✏️ *请求修改*\n\n描述需要更改的内容：","ko":"✏️ *수정 요청*\n\n변경 사항 설명:"},
    "edit_ok":      {"ru":"✅ *Заявка принята!*\n\nСвяжемся в течение 24 часов.","en":"✅ *Request accepted!*\n\nWe'll contact within 24 hours.","uz":"✅ *So'rov qabul qilindi!*\n\n24 soat ichida bog'lanamiz.","kz":"✅ *Сұраныс қабылданды!*\n\n24 сағат ішінде хабарласамыз.","zh":"✅ *已接受！*\n\n24小时内联系。","ko":"✅ *요청 수락!*\n\n24시간 내 연락."},
    "saved":        {"ru":"✅ Сохранено!","en":"✅ Saved!","uz":"✅ Saqlandi!","kz":"✅ Сақталды!","zh":"✅ 已保存！","ko":"✅ 저장됨!"},
    "settings_text":{"ru":"⚙️ *Настройки*\n\nЧто изменить?","en":"⚙️ *Settings*\n\nWhat to change?","uz":"⚙️ *Sozlamalar*\n\nNimani o'zgartirish?","kz":"⚙️ *Параметрлер*\n\nНені өзгерту?","zh":"⚙️ *设置*\n\n更改什么？","ko":"⚙️ *설정*\n\n무엇을 변경?"},
}

def t(key, uid, **kwargs):
    user = get_user(uid)
    lang = user.get("lang", "ru")
    text = T.get(key, {}).get(lang) or T.get(key, {}).get("ru", "")
    return text.format(**kwargs) if kwargs else text

def get_lang(uid):
    user = get_user(uid)
    return user.get("lang", "ru")

# ── Keyboards ─────────────────────────────────────────────────────────────────

def kb_lang():
    return {"inline_keyboard": [
        [{"text":"🇷🇺 Русский","callback_data":"lang_ru"},{"text":"🇬🇧 English","callback_data":"lang_en"}],
        [{"text":"🇺🇿 O'zbek","callback_data":"lang_uz"},{"text":"🇰🇿 Қазақша","callback_data":"lang_kz"}],
        [{"text":"🇨🇳 中文","callback_data":"lang_zh"},{"text":"🇰🇷 한국어","callback_data":"lang_ko"}],
    ]}

def kb_back(uid, to):
    return {"inline_keyboard": [[{"text": t("back_btn",uid), "callback_data": to}]]}

def kb_start(uid):
    return {"inline_keyboard": [
        [{"text": t("register_btn",uid), "callback_data": "register"}],
        [{"text": t("how_btn",uid), "callback_data": "how"},
         {"text": t("plans_btn",uid), "callback_data": "plans"}],
        [{"text": t("lang_btn",uid), "callback_data": "choose_lang"}],
    ]}

def kb_categories(uid):
    lang = get_lang(uid)
    cats = {
        "ru":[["🍕 Кафе","💇 Салон"],["🛍 Магазин","🏋️ Фитнес"],["🏥 Медицина","📦 Другое"]],
        "en":[["🍕 Cafe","💇 Salon"],["🛍 Shop","🏋️ Fitness"],["🏥 Medical","📦 Other"]],
        "uz":[["🍕 Kafe","💇 Salon"],["🛍 Do'kon","🏋️ Fitnes"],["🏥 Tibbiyot","📦 Boshqa"]],
        "kz":[["🍕 Кафе","💇 Салон"],["🛍 Дүкен","🏋️ Фитнес"],["🏥 Медицина","📦 Басқа"]],
        "zh":[["🍕 咖啡馆","💇 美容院"],["🛍 商店","🏋️ 健身"],["🏥 医疗","📦 其他"]],
        "ko":[["🍕 카페","💇 미용실"],["🛍 상점","🏋️ 피트니스"],["🏥 의료","📦 기타"]],
    }
    keys=[["cat_cafe","cat_salon"],["cat_shop","cat_fitness"],["cat_medical","cat_other"]]
    lb = cats.get(lang, cats["ru"])
    return {"inline_keyboard":[[{"text":lb[i][j],"callback_data":keys[i][j]} for j in range(2)] for i in range(3)]}

def kb_dashboard(uid):
    rows = [
        [{"text":t("stats_btn",uid),"callback_data":"stats"},{"text":t("settings_btn",uid),"callback_data":"settings"}],
        [{"text":t("edit_btn",uid),"callback_data":"edit_req"},{"text":t("plan_btn",uid),"callback_data":"plan"}],
        [{"text":t("lang_btn",uid),"callback_data":"choose_lang"}],
    ]
    if MINI_APP_URL:
        rows.insert(2,[{"text":t("open_btn",uid),"web_app":{"url":MINI_APP_URL}}])
    return {"inline_keyboard": rows}

def kb_settings(uid):
    lang = get_lang(uid)
    d={"ru":"📝 Описание","en":"📝 Description","uz":"📝 Tavsif","kz":"📝 Сипаттама","zh":"📝 描述","ko":"📝 설명"}
    h={"ru":"🕐 Часы работы","en":"🕐 Hours","uz":"🕐 Ish vaqti","kz":"🕐 Жұмыс уақыты","zh":"🕐 营业时间","ko":"🕐 영업시간"}
    m={"ru":"📋 Меню/Услуги","en":"📋 Menu/Services","uz":"📋 Menyu","kz":"📋 Мәзір","zh":"📋 菜单","ko":"📋 메뉴"}
    return {"inline_keyboard":[
        [{"text":d.get(lang,"📝"),"callback_data":"set_desc"}],
        [{"text":h.get(lang,"🕐"),"callback_data":"set_hours"}],
        [{"text":m.get(lang,"📋"),"callback_data":"set_menu"}],
        [{"text":t("back_btn",uid),"callback_data":"dashboard"}],
    ]}

def kb_plans_upgrade(uid):
    return {"inline_keyboard":[
        [{"text":"⚡ Starter — $29/мес","callback_data":"buy_starter"}],
        [{"text":"🚀 Pro — $79/мес","callback_data":"buy_pro"}],
        [{"text":t("back_btn",uid),"callback_data":"dashboard"}],
    ]}

# ── Dashboard text ────────────────────────────────────────────────────────────

def text_dashboard(uid):
    user = get_user(uid)
    s = user.get("stats", {"today":0,"total":0,"users":0,"orders":0})
    p = PLANS[user.get("plan","free")]
    lang = user.get("lang","ru")
    lb = {
        "ru":("Сегодня","Сообщений","Клиентов","Заказов","Всего"),
        "en":("Today","Messages","Clients","Orders","Total"),
        "uz":("Bugun","Xabarlar","Mijozlar","Buyurtmalar","Jami"),
        "kz":("Бүгін","Хабарлар","Клиенттер","Тапсырыстар","Барлығы"),
        "zh":("今天","消息","客户","订单","总计"),
        "ko":("오늘","메시지","고객","주문","전체"),
    }.get(lang, ("Сегодня","Сообщений","Клиентов","Заказов","Всего"))
    return (
        f"🏢 *{user.get('name','Бизнес')}*\n"
        f"📂 {user.get('category','—')}  •  {p['emoji']} {p['name']}\n\n"
        f"📈 *{lb[0]}:*\n"
        f"  💬 {lb[1]}: *{s['today']}*\n"
        f"  👥 {lb[2]}: *{s['users']}*\n"
        f"  🛒 {lb[3]}: *{s['orders']}*\n\n"
        f"{lb[4]}: {s['total']} {lb[1].lower()}"
    )

# ── Handlers ──────────────────────────────────────────────────────────────────

def on_start(uid, name, chat_id, tg_lang):
    user = get_user(uid)
    if not user.get("lang"):
        # Автоопределение языка
        auto = tg_lang[:2] if tg_lang else "ru"
        if auto not in LANGS: auto = "ru"
        user["lang"] = auto
        set_user(uid, user)
    if user.get("registered"):
        send(chat_id, text_dashboard(uid), kb_dashboard(uid))
    else:
        send(chat_id, t("welcome", uid, name=name), kb_start(uid))

def on_callback(uid, chat_id, msg_id, data, cq_id, username, name):
    answer(cq_id)
    user = get_user(uid)

    if data.startswith("lang_"):
        lang = data.split("_")[1]
        user["lang"] = lang
        set_user(uid, user)
        if user.get("registered"):
            edit(chat_id, msg_id, text_dashboard(uid), kb_dashboard(uid))
        else:
            edit(chat_id, msg_id, t("welcome", uid, name=name), kb_start(uid))
        return

    if data == "choose_lang":
        edit(chat_id, msg_id, "🌍 Choose language:", kb_lang())
        return

    if data == "how":
        lang = user.get("lang","ru")
        how = {
            "ru":"📖 *Как работает Zevo?*\n\n1️⃣ Регистрируете бизнес\n2️⃣ Настраиваете бота\n3️⃣ Даёте ссылку клиентам\n4️⃣ Бот работает 24/7\n5️⃣ Видите статистику\n\n⏱ *5 минут*",
            "en":"📖 *How does Zevo work?*\n\n1️⃣ Register business\n2️⃣ Customize bot\n3️⃣ Share link\n4️⃣ Bot works 24/7\n5️⃣ View stats\n\n⏱ *5 minutes*",
            "uz":"📖 *Zevo qanday ishlaydi?*\n\n1️⃣ Biznesni ro'yxatdan o'tkaz\n2️⃣ Botni sozla\n3️⃣ Havolani ulash\n4️⃣ Bot 24/7 ishlaydi\n5️⃣ Statistikani ko'r\n\n⏱ *5 daqiqa*",
        }.get(lang, "📖 *How does Zevo work?*\n\n1-5 steps → Bot works 24/7\n\n⏱ *5 min*")
        edit(chat_id, msg_id, how, {"inline_keyboard":[[{"text":t("register_btn",uid),"callback_data":"register"},{"text":t("back_btn",uid),"callback_data":"start"}]]})

    elif data == "plans":
        lang = user.get("lang","ru")
        plans_text = {
            "ru":"💰 *Тарифы Zevo*\n\n🆓 *Free* — бесплатно\n  • 100 сообщений/мес\n\n⚡ *Starter* — $29/мес\n  • 1 000 сообщений\n  • 3 бота\n\n🚀 *Pro* — $79/мес\n  • Безлимит\n  • Кастомный AI",
            "en":"💰 *Zevo Plans*\n\n🆓 *Free*\n  • 100 msg/mo\n\n⚡ *Starter* — $29/mo\n  • 1,000 msg\n  • 3 bots\n\n🚀 *Pro* — $79/mo\n  • Unlimited\n  • Custom AI",
        }.get(lang, "💰 *Plans*\n\n🆓 Free | ⚡ $29 | 🚀 $79")
        edit(chat_id, msg_id, plans_text, {"inline_keyboard":[[{"text":t("register_btn",uid),"callback_data":"register"}],[{"text":t("back_btn",uid),"callback_data":"start"}]]})

    elif data == "start":
        if user.get("registered"):
            edit(chat_id, msg_id, text_dashboard(uid), kb_dashboard(uid))
        else:
            edit(chat_id, msg_id, t("welcome",uid,name=name), kb_start(uid))

    elif data == "register":
        set_state(uid, {"step":"name"})
        edit(chat_id, msg_id, t("reg_name",uid), kb_back(uid,"start"))

    elif data.startswith("cat_") and data in CATEGORIES_RU:
        st = get_state(uid)
        st["category"] = CATEGORIES_RU[data]
        st["step"] = "desc"
        set_state(uid, st)
        edit(chat_id, msg_id, f"✅ *{CATEGORIES_RU[data]}*\n\n{t('reg_desc',uid)}")

    elif data == "dashboard":
        if user.get("registered"):
            edit(chat_id, msg_id, text_dashboard(uid), kb_dashboard(uid))

    elif data == "stats":
        if not user.get("registered"): return
        s = user.get("stats",{"today":0,"total":0,"users":0,"orders":0})
        edit(chat_id, msg_id,
             f"📊 *{user['name']}*\n\n"
             f"💬 Сегодня: {s['today']}\n"
             f"💬 Всего: {s['total']}\n"
             f"👥 Клиентов: {s['users']}\n"
             f"🛒 Заказов: {s['orders']}",
             kb_back(uid,"dashboard"))

    elif data == "settings":
        if user.get("registered"):
            edit(chat_id, msg_id, t("settings_text",uid), kb_settings(uid))

    elif data in ("set_desc","set_hours","set_menu"):
        step = {"set_desc":"s_desc","set_hours":"s_hours","set_menu":"s_menu"}[data]
        set_state(uid, {"step": step})
        edit(chat_id, msg_id, t("settings_text",uid), kb_back(uid,"settings"))

    elif data == "edit_req":
        set_state(uid, {"step":"edit_req"})
        edit(chat_id, msg_id, t("edit_req_text",uid), kb_back(uid,"dashboard"))

    elif data == "plan":
        if not user.get("registered"): return
        p = PLANS[user.get("plan","free")]
        edit(chat_id, msg_id,
             f"💰 {p['emoji']} *{p['name']}* — {p['limit']} msg/mo",
             kb_plans_upgrade(uid))

    elif data in ("buy_starter","buy_pro"):
        plan_key = "starter" if data == "buy_starter" else "pro"
        plan = PLANS[plan_key]
        cards = ""
        if CARD_VISA: cards += f"💳 *Visa:* `{CARD_VISA}`\n"
        if CARD_HUMO: cards += f"🟠 *Humo:* `{CARD_HUMO}`\n"
        set_pending(uid, plan_key)
        send(chat_id,
             t("payment_text",uid,plan=f"{plan['emoji']} {plan['name']}",price=plan['price'],cards=cards),
             {"inline_keyboard":[
                 [{"text":t("check_sent_btn",uid),"callback_data":"check_sent"}],
                 [{"text":t("back_btn",uid),"callback_data":"plan"}],
             ]})

    elif data == "check_sent":
        plan_key = get_pending(uid) or "starter"
        set_state(uid, {"step":"awaiting_check","plan":plan_key})
        plan = PLANS[plan_key]
        send(ADMIN_ID,
             f"💰 *Новая оплата!*\n\n"
             f"👤 @{username} (ID: `{uid}`)\n"
             f"🏢 {user.get('name','?')}\n"
             f"📦 {plan['emoji']} {plan['name']} — ${plan['price']}\n"
             f"🌍 {LANGS.get(user.get('lang','ru'),'?')}",
             {"inline_keyboard":[[
                 {"text":"✅ Подтвердить","callback_data":f"confirm_{uid}_{plan_key}"},
                 {"text":"❌ Отклонить","callback_data":f"reject_{uid}"},
             ]]})
        send(chat_id, t("send_check",uid))

    elif data.startswith("confirm_") and uid == ADMIN_ID:
        parts = data.split("_")
        target_uid, plan_key = int(parts[1]), parts[2]
        target = get_user(target_uid)
        target["plan"] = plan_key
        set_user(target_uid, target)
        plan = PLANS[plan_key]
        send(target_uid, t("confirmed",target_uid,plan=f"{plan['emoji']} {plan['name']}"), kb_back(target_uid,"dashboard"))
        edit(chat_id, msg_id, f"✅ {plan['name']} активирован для {target_uid}")

    elif data.startswith("reject_") and uid == ADMIN_ID:
        target_uid = int(data.split("_")[1])
        send(target_uid, t("rejected",target_uid), kb_back(target_uid,"plan"))
        edit(chat_id, msg_id, "❌ Отклонено")

def on_message(uid, chat_id, text, username, message_id, msg_type, name, tg_lang):
    user = get_user(uid)
    if not user.get("lang"):
        auto = tg_lang[:2] if tg_lang else "ru"
        if auto not in LANGS: auto = "ru"
        user["lang"] = auto
        set_user(uid, user)

    st = get_state(uid)
    step = st.get("step")

    if msg_type == "photo" and step == "awaiting_check":
        plan_key = st.get("plan","starter")
        plan = PLANS[plan_key]
        del_state(uid)
        tg("forwardMessage", chat_id=ADMIN_ID, from_chat_id=chat_id, message_id=message_id)
        send(ADMIN_ID,
             f"📸 Чек от @{username} (ID: `{uid}`)\n{plan['emoji']} {plan['name']} — ${plan['price']}",
             {"inline_keyboard":[[
                 {"text":"✅ Подтвердить","callback_data":f"confirm_{uid}_{plan_key}"},
                 {"text":"❌ Отклонить","callback_data":f"reject_{uid}"},
             ]]})
        send(chat_id, t("check_received",uid))
        return

    if step == "name":
        st["name"] = text
        st["step"] = "category"
        set_state(uid, st)
        send(chat_id, f"✅ *{text}*\n\n{t('reg_cat',uid)}", kb_categories(uid))

    elif step == "desc":
        n = st.get("name","Бизнес")
        cat = st.get("category","📦")
        user.update({
            "name": n, "category": cat, "description": text,
            "plan": "free", "registered": True,
            "stats": {"today":0,"total":0,"users":0,"orders":0},
        })
        set_user(uid, user)
        del_state(uid)
        send(ADMIN_ID, f"🆕 *Новый клиент!*\n\n👤 @{username}\n🏢 {n}\n📂 {cat}\n🌍 {LANGS.get(user.get('lang','ru'),'?')}")
        send(chat_id, t("registered",uid,name=n), kb_dashboard(uid))

    elif step == "edit_req":
        del_state(uid)
        send(ADMIN_ID, f"✏️ *Запрос правок*\n\n👤 @{username}\n🏢 {user.get('name','?')}\n\n📝 {text}")
        send(chat_id, t("edit_ok",uid), kb_back(uid,"dashboard"))

    elif step in ("s_desc","s_hours","s_menu"):
        del_state(uid)
        send(chat_id, t("saved",uid), kb_back(uid,"settings"))

    else:
        # Считаем статистику
        if user.get("registered"):
            s = user.get("stats",{"today":0,"total":0,"users":0,"orders":0})
            s["total"] = s.get("total",0) + 1
            s["today"] = s.get("today",0) + 1
            user["stats"] = s
            set_user(uid, user)
            send(chat_id, text_dashboard(uid), kb_dashboard(uid))
        else:
            send(chat_id, t("welcome",uid,name=name), kb_start(uid))

# ── Vercel handler ────────────────────────────────────────────────────────────

class handler(BaseHTTPRequestHandler):

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length))
        try:
            if "callback_query" in body:
                cq       = body["callback_query"]
                uid      = cq["from"]["id"]
                username = cq["from"].get("username","unknown")
                name     = cq["from"].get("first_name","")
                cid      = cq["message"]["chat"]["id"]
                mid      = cq["message"]["message_id"]
                on_callback(uid, cid, mid, cq["data"], cq["id"], username, name)
            elif "message" in body:
                msg      = body["message"]
                uid      = msg["from"]["id"]
                cid      = msg["chat"]["id"]
                text     = msg.get("text","")
                username = msg["from"].get("username","unknown")
                name     = msg["from"].get("first_name","друг")
                mid      = msg["message_id"]
                tg_lang  = msg["from"].get("language_code","ru")
                msg_type = "photo" if "photo" in msg else "text"
                if text.startswith("/start"):
                    on_start(uid, name, cid, tg_lang)
                else:
                    on_message(uid, cid, text, username, mid, msg_type, name, tg_lang)
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
