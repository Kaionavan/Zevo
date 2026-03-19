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
    "free":  {"emoji": "🆓", "name": "Free",  "price": 0,  "desc": {"ru":"30 дней бесплатно","en":"30 days free","uz":"30 kun bepul","kz":"30 күн тегін","zh":"30天免费","ko":"30일 무료"}},
    "basic": {"emoji": "⚡", "name": "Basic", "price": 19, "desc": {"ru":"Бот 24/7 + поддержка","en":"Bot 24/7 + support","uz":"Bot 24/7 + qo'llab","kz":"Бот 24/7 + қолдау","zh":"机器人24/7+支持","ko":"봇 24/7+지원"}},
    "pro":   {"emoji": "🚀", "name": "Pro",   "price": 39, "desc": {"ru":"AI + отчёты + приоритет","en":"AI + reports + priority","uz":"AI + hisobotlar","kz":"AI + есептер","zh":"AI+报告+优先","ko":"AI+보고서+우선"}},
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
        val = json.dumps(value)
        cmd = ["SET", key, val]
        if ex:
            cmd += ["EX", ex]
        req = urllib.request.Request(
            f"{KV_URL}/pipeline",
            data=json.dumps([cmd]).encode(),
            headers={"Authorization": f"Bearer {KV_TOKEN}", "Content-Type": "application/json"},
            method="POST"
        )
        urllib.request.urlopen(req, timeout=3)
    except Exception as e:
        print(f"KV set error: {e}")

def kv_del(key):
    if not KV_URL: return
    try:
        req = urllib.request.Request(
            f"{KV_URL}/pipeline",
            data=json.dumps([["DEL", key]]).encode(),
            headers={"Authorization": f"Bearer {KV_TOKEN}", "Content-Type": "application/json"},
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
        [{"text":"🤖 Мой бот","callback_data":"my_bot_status"}],
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
    av={"ru":"🖼 Аватарка бота","en":"🖼 Bot avatar","uz":"🖼 Bot avatari","kz":"🖼 Бот аватары","zh":"🖼 机器人头像","ko":"🖼 봇 아바타"}
    return {"inline_keyboard":[
        [{"text":d.get(lang,"📝"),"callback_data":"set_desc"}],
        [{"text":h.get(lang,"🕐"),"callback_data":"set_hours"}],
        [{"text":m.get(lang,"📋"),"callback_data":"set_menu"}],
        [{"text":av.get(lang,"🖼"),"callback_data":"set_avatar"}],
        [{"text":t("back_btn",uid),"callback_data":"dashboard"}],
    ]}

def kb_plans_upgrade(uid):
    return {"inline_keyboard":[
        [{"text":"⚡ Basic — $19/мес","callback_data":"buy_basic"}],
        [{"text":"🚀 Pro — $39/мес","callback_data":"buy_pro"}],
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


# ── Onboarding ────────────────────────────────────────────────────────────────

ONBOARDING_STEPS = [
    ("menu",     {"ru":"🍽 Меню и цены",      "en":"🍽 Menu & prices",    "uz":"🍽 Menyu va narxlar",  "kz":"🍽 Мәзір мен бағалар", "zh":"🍽 菜单和价格",    "ko":"🍽 메뉴 및 가격"}),
    ("hours",    {"ru":"🕐 Часы работы",       "en":"🕐 Working hours",    "uz":"🕐 Ish vaqti",         "kz":"🕐 Жұмыс уақыты",      "zh":"🕐 营业时间",      "ko":"🕐 영업시간"}),
    ("location", {"ru":"📍 Адрес и локация",   "en":"📍 Address",          "uz":"📍 Manzil",            "kz":"📍 Мекенжай",          "zh":"📍 地址位置",      "ko":"📍 주소 위치"}),
    ("contacts", {"ru":"📞 Контакты",          "en":"📞 Contacts",         "uz":"📞 Kontaktlar",        "kz":"📞 Байланыс",          "zh":"📞 联系方式",      "ko":"📞 연락처"}),
    ("promo",    {"ru":"🎁 Акции и бонусы",    "en":"🎁 Promotions",       "uz":"🎁 Aksiyalar",         "kz":"🎁 Акциялар",          "zh":"🎁 促销优惠",      "ko":"🎁 프로모션"}),
    ("faq",      {"ru":"❓ Частые вопросы",    "en":"❓ FAQ",              "uz":"❓ Ko'p so'raladigan", "kz":"❓ Жиі сұрақтар",      "zh":"❓ 常见问题",      "ko":"❓ 자주 묻는 질문"}),
]

ONBOARDING_HINTS = {
    "menu":     {"ru":"Напишите ваше меню с ценами.\n\nНапример:\n🍕 Пицца Маргарита — 45 000 сум\n🍔 Бургер классик — 35 000 сум\n☕ Кофе латте — 18 000 сум\n🥗 Салат Цезарь — 28 000 сум",
                 "en":"Write your menu with prices.\n\nExample:\n🍕 Pizza — $8\n🍔 Burger — $6\n☕ Latte — $3",
                 "uz":"Menyu va narxlarni yozing.\n\nMasalan:\n🍕 Pizza — 45 000 so'm\n🍔 Burger — 35 000 so'm\n☕ Kofe — 18 000 so'm",
                 "kz":"Мәзір мен бағаларды жазыңыз.\n\nМысалы:\n🍕 Пицца — 45 000 сум\n🍔 Бургер — 35 000 сум",
                 "zh":"请写下您的菜单和价格。\n\n例如：\n🍕 披萨 — ¥45\n🍔 汉堡 — ¥35\n☕ 拿铁 — ¥18",
                 "ko":"메뉴와 가격을 작성하세요.\n\n예시:\n🍕 피자 — 45,000원\n🍔 버거 — 35,000원"},
    "hours":    {"ru":"Напишите часы работы.\n\nНапример:\n📅 Пн–Пт: 09:00 – 22:00\n📅 Сб–Вс: 10:00 – 23:00\n🚫 Понедельник — выходной",
                 "en":"Write your working hours.\n\nExample:\n📅 Mon–Fri: 9am – 10pm\n📅 Sat–Sun: 10am – 11pm",
                 "uz":"Ish vaqtini yozing.\n\nMasalan:\n📅 Du–Ju: 09:00 – 22:00\n📅 Shan–Yak: 10:00 – 23:00",
                 "kz":"Жұмыс уақытын жазыңыз.\n\nМысалы:\n📅 Дс–Жм: 09:00 – 22:00",
                 "zh":"请写下营业时间。\n\n例如：\n📅 周一至周五：9:00 – 22:00\n📅 周末：10:00 – 23:00",
                 "ko":"영업시간을 작성하세요.\n\n예시:\n📅 월–금: 09:00 – 22:00\n📅 토–일: 10:00 – 23:00"},
    "location": {"ru":"Напишите адрес и как добраться.\n\nНапример:\nул. Амира Темура 15, Ташкент\nОриентир: рядом с ТЦ Mega Planet\nПарковка: бесплатная\nМетро: Bunyodkor (5 мин пешком)",
                 "en":"Write your address and how to get there.\n\nExample:\n15 Amir Temur St, Tashkent\nNearby: Mega Planet Mall\nParking: free",
                 "uz":"Manzil va qanday borish haqida yozing.\n\nMasalan:\nAmir Temur ko'chasi 15, Toshkent\nMo'ljal: Mega Planet yonida",
                 "kz":"Мекенжай мен қалай жетуді жазыңыз.",
                 "zh":"请写下地址和交通方式。\n\n例如：\n帖木儿大街15号，塔什干\n地标：Mega Plaza附近",
                 "ko":"주소와 찾아오는 방법을 작성하세요."},
    "contacts": {"ru":"Напишите контакты для связи.\n\nНапример:\n📱 Telegram: @your_cafe\n📞 Телефон: +998 90 123 45 67\n📸 Instagram: @your_cafe\n🌐 Сайт: yourcafe.uz",
                 "en":"Write your contact information.\n\nExample:\n📱 Telegram: @your_cafe\n📞 Phone: +1 234 567 8900\n📸 Instagram: @your_cafe",
                 "uz":"Kontakt ma'lumotlarini yozing.\n\nMasalan:\n📱 Telegram: @your_cafe\n📞 Telefon: +998 90 123 45 67",
                 "kz":"Байланыс ақпаратын жазыңыз.",
                 "zh":"请写下联系方式。\n\n例如：\n📱 微信：your_cafe\n📞 电话：+86 123 4567",
                 "ko":"연락처 정보를 작성하세요."},
    "promo":    {"ru":"Напишите ваши акции и специальные предложения.\n\nНапример:\n🎁 Счастливые часы: 14:00–17:00 скидка 20%\n☕ Каждый 5-й кофе в подарок\n👥 Для компании от 5 человек — десерт бесплатно\n🎂 В день рождения — скидка 15%",
                 "en":"Write your promotions and special offers.\n\nExample:\n🎁 Happy hours: 2pm–5pm 20% off\n☕ Every 5th coffee free\n🎂 Birthday discount: 15% off",
                 "uz":"Aksiya va maxsus takliflarni yozing.\n\nMasalan:\n🎁 Baxtli soatlar: 14:00–17:00 da 20% chegirma",
                 "kz":"Акциялар мен арнайы ұсыныстарды жазыңыз.",
                 "zh":"请写下您的促销和特别优惠。\n\n例如：\n🎁 欢乐时光：14:00–17:00 打八折",
                 "ko":"프로모션과 특별 혜택을 작성하세요."},
    "faq":      {"ru":"Напишите частые вопросы клиентов и ответы.\n\nНапример:\n❓ Есть ли доставка? — Да, от 50 000 сум бесплатно\n❓ Можно бронировать столик? — Да, пишите нам\n❓ Есть ли детское меню? — Да\n❓ Принимаете карты? — Visa, Humo, UzCard",
                 "en":"Write frequently asked questions and answers.\n\nExample:\n❓ Do you deliver? — Yes, free over $20\n❓ Can I book a table? — Yes, message us\n❓ Do you accept cards? — Yes",
                 "uz":"Ko'p so'raladigan savollar va javoblar.\n\nMasalan:\n❓ Yetkazib berish bormi? — Ha, 50 000 so'mdan bepul",
                 "kz":"Жиі қойылатын сұрақтар мен жауаптар.",
                 "zh":"请写下常见问题和答案。\n\n例如：\n❓ 有外卖吗？— 有，50元以上免费配送",
                 "ko":"자주 묻는 질문과 답변을 작성하세요."},
}

def onboarding_progress(user):
    filled = sum(1 for step, _ in ONBOARDING_STEPS if user.get(f"info_{step}"))
    total = len(ONBOARDING_STEPS)
    bar = "●" * filled + "○" * (total - filled)
    pct = int(filled / total * 100)
    return filled, total, bar, pct

def onboarding_text(uid, user):
    lang = user.get("lang","ru")
    filled, total, bar, pct = onboarding_progress(user)
    labels = {
        "ru": ("🚀 Настройка AI-бота", "Заполните информацию — чем больше, тем умнее бот отвечает клиентам", "Готово", "Заполнено"),
        "en": ("🚀 AI Bot Setup", "Fill in the info — the more you add, the smarter your bot answers", "Done", "Filled"),
        "uz": ("🚀 AI-bot sozlash", "Ma'lumot to'ldiring — ko'proq bo'lsa, bot aqlliroq javob beradi", "Tayyor", "To'ldirildi"),
        "kz": ("🚀 AI-ботты баптау", "Ақпарат толтырыңыз — көбірек болса, бот ақылды жауап береді", "Дайын", "Толтырылды"),
        "zh": ("🚀 AI机器人设置", "填写信息 — 信息越多，机器人回答越智能", "完成", "已填写"),
        "ko": ("🚀 AI 봇 설정", "정보를 채울수록 봇이 더 스마트하게 답변합니다", "완료", "작성됨"),
    }.get(lang, ("🚀 AI Bot Setup", "Fill info for smarter bot", "Done", "Filled"))
    
    steps_text = ""
    for step, names in ONBOARDING_STEPS:
        name = names.get(lang, names["ru"])
        done = "✅" if user.get(f"info_{step}") else "○"
        steps_text += f"{done} {name}\n"
    
    return (
        f"*{labels[0]}*\n\n"
        f"{labels[1]}\n\n"
        f"{steps_text}\n"
        f"`{bar}` {pct}% {labels[3]}"
    )

def onboarding_kb(uid):
    user = get_user(uid)
    lang = user.get("lang","ru")
    rows = []
    for step, names in ONBOARDING_STEPS:
        name = names.get(lang, names["ru"])
        done = "✅ " if user.get(f"info_{step}") else ""
        rows.append([{"text": f"{done}{name}", "callback_data": f"ob_{step}"}])
    rows.append([{"text": t("open_btn",uid) if MINI_APP_URL else "📊 Дашборд", "callback_data": "dashboard"}])
    return {"inline_keyboard": rows}


def kb_admin_dashboard(uid):
    """Специальный дашборд для администратора Zevo"""
    rows = [
        [{"text":"📊 Статистика","callback_data":"stats"},{"text":"⚙️ Настройки","callback_data":"settings"}],
        [{"text":"👥 Все клиенты","callback_data":"admin_clients"},{"text":"💰 Тариф","callback_data":"plan"}],
        [{"text":"🔗 Моя ссылка","callback_data":"my_link"}],
        [{"text":"🌍 Язык","callback_data":"choose_lang"}],
    ]
    if MINI_APP_URL:
        rows.insert(2,[{"text":"📱 Открыть панель","web_app":{"url":MINI_APP_URL}}])
    return {"inline_keyboard": rows}

# ── Handlers ──────────────────────────────────────────────────────────────────

def on_start(uid, name, chat_id, tg_lang, payload=""):
    user = get_user(uid)
    if user.get("blocked"):
        send(chat_id, "⛔ Ваш доступ приостановлен. Обратитесь в поддержку: @Nurali0369")
        return
    if not user.get("lang"):
        auto = tg_lang[:2] if tg_lang else "ru"
        if auto not in LANGS: auto = "ru"
        user["lang"] = auto
        set_user(uid, user)

    # Если это клиент бизнеса (payload = business_id)
    if payload and payload.startswith("biz_"):
        biz_id = payload[4:]
        biz = get_user(int(biz_id)) if biz_id.isdigit() else None
        if biz and biz.get("registered"):
            handle_client(uid, name, chat_id, biz_id, biz, user)
            return

    # Обычный владелец бизнеса
    if user.get("registered"):
        if uid == ADMIN_ID:
            send(chat_id, text_dashboard(uid), kb_admin_dashboard(uid))
        else:
            send(chat_id, text_dashboard(uid), kb_dashboard(uid))
    else:
        send(chat_id, t("welcome", uid, name=name), kb_start(uid))

def handle_client(uid, name, chat_id, biz_id, biz, client_user):
    """Клиент кафе/бизнеса пишет боту"""
    lang = client_user.get("lang", "ru")
    biz_name = biz.get("name", "Бизнес")
    desc = biz.get("description", "")
    menu = biz.get("info_menu", "")
    hours = biz.get("info_hours", "")
    location = biz.get("info_location", "")
    contacts = biz.get("info_contacts", "")
    promo = biz.get("info_promo", "")

    # Сохраняем что клиент принадлежит этому бизнесу
    client_user["client_of"] = biz_id
    client_user["lang"] = lang
    set_user(uid, client_user)

    # Обновляем статистику бизнеса
    biz_data = get_user(int(biz_id))
    s = biz_data.get("stats", {"today":0,"total":0,"users":0,"orders":0})
    
    # Проверяем новый ли пользователь
    known = kv_get(f"client:{biz_id}:{uid}")
    if not known:
        kv_set(f"client:{biz_id}:{uid}", 1, ex=86400*365)
        s["users"] = s.get("users", 0) + 1
    s["today"] = s.get("today", 0) + 1
    s["total"] = s.get("total", 0) + 1
    biz_data["stats"] = s
    set_user(int(biz_id), biz_data)

    greetings = {
        "ru": f"👋 Добро пожаловать в *{biz_name}*!",
        "en": f"👋 Welcome to *{biz_name}*!",
        "uz": f"👋 *{biz_name}*ga xush kelibsiz!",
        "kz": f"👋 *{biz_name}*-ға қош келдіңіз!",
        "zh": f"👋 欢迎来到 *{biz_name}*！",
        "ko": f"👋 *{biz_name}*에 오신 것을 환영합니다!",
    }
    
    info_parts = []
    if desc: info_parts.append(f"📋 {desc}")
    if hours: info_parts.append(f"🕐 {hours}")
    if location: info_parts.append(f"📍 {location}")
    if contacts: info_parts.append(f"📞 {contacts}")
    if promo: info_parts.append(f"🎁 {promo}")
    if menu: info_parts.append(f"🍽 *Меню:*\n{menu}")

    greeting = greetings.get(lang, greetings["ru"])
    info_text = "\n\n".join(info_parts) if info_parts else ""
    
    ask_labels = {
        "ru": "Чем могу помочь? Задайте вопрос 👇",
        "en": "How can I help? Ask a question 👇",
        "uz": "Qanday yordam bera olaman? Savol bering 👇",
        "kz": "Қалай көмектесе аламын? Сұрақ қойыңыз 👇",
        "zh": "我能帮助您什么？请提问 👇",
        "ko": "어떻게 도와드릴까요? 질문하세요 👇",
    }
    
    full_text = greeting
    if info_text:
        full_text += f"\n\n{info_text}"
    full_text += f"\n\n{ask_labels.get(lang, ask_labels['ru'])}"
    
    # Кнопки для клиента
    btn_labels = {
        "ru": ["🍽 Меню", "🕐 Часы", "📍 Адрес", "📞 Контакты", "🎁 Акции"],
        "en": ["🍽 Menu", "🕐 Hours", "📍 Location", "📞 Contacts", "🎁 Promos"],
        "uz": ["🍽 Menyu", "🕐 Vaqt", "📍 Manzil", "📞 Kontakt", "🎁 Aksiya"],
        "kz": ["🍽 Мәзір", "🕐 Уақыт", "📍 Мекен", "📞 Байланыс", "🎁 Акция"],
        "zh": ["🍽 菜单", "🕐 时间", "📍 地址", "📞 联系", "🎁 优惠"],
        "ko": ["🍽 메뉴", "🕐 시간", "📍 위치", "📞 연락처", "🎁 혜택"],
    }
    btns = btn_labels.get(lang, btn_labels["ru"])
    kb = {"inline_keyboard": [
        [{"text": btns[0], "callback_data": f"c_menu_{biz_id}"},
         {"text": btns[1], "callback_data": f"c_hours_{biz_id}"}],
        [{"text": btns[2], "callback_data": f"c_loc_{biz_id}"},
         {"text": btns[3], "callback_data": f"c_cont_{biz_id}"}],
        [{"text": btns[4], "callback_data": f"c_promo_{biz_id}"}],
    ]}
    send(chat_id, full_text, kb)

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
            "ru":"💰 *Тарифы Zevo*\n\n🆓 *Free* — бесплатно\n  • 30 дней пробный период\n  • Полный функционал\n\n⚡ *Basic* — $19/мес\n  • Бот работает 24/7\n  • Мы следим за работой\n  • Обновление данных\n\n🚀 *Pro* — $39/мес\n  • Всё из Basic\n  • Умный AI\n  • Ежемесячный отчёт\n  • Приоритетная поддержка",
            "en":"💰 *Zevo Plans*\n\n🆓 *Free*\n  • 30 day trial\n  • Full features\n\n⚡ *Basic* — $19/mo\n  • Bot works 24/7\n  • We monitor it\n  • Data updates\n\n🚀 *Pro* — $39/mo\n  • Everything in Basic\n  • Smart AI\n  • Monthly report\n  • Priority support",
            "uz":"💰 *Zevo Tariflari*\n\n🆓 *Free* — bepul\n  • 30 kunlik sinov\n\n⚡ *Basic* — $19/oy\n  • Bot 24/7 ishlaydi\n  • Monitoring\n\n🚀 *Pro* — $39/oy\n  • Aqlli AI\n  • Oylik hisobot",
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


    elif data.startswith("ob_"):
        step = data[3:]
        hint = ONBOARDING_HINTS.get(step, {})
        lang = user.get("lang","ru")
        hint_text = hint.get(lang, hint.get("ru",""))
        step_names = dict(ONBOARDING_STEPS)
        step_name = step_names.get(step, {}).get(lang, step) if step_names.get(step) else step
        set_state(uid, {"step": f"ob_{step}"})
        done = "✅ " if user.get(f"info_{step}") else ""
        current = user.get(f"info_{step}", "")
        current_text = f"\n\n_Текущее значение:_\n{current[:200]}" if current else ""
        edit(chat_id, msg_id,
             f"*{done}{step_name}*{current_text}\n\n{hint_text}",
             {"inline_keyboard": [
                 [{"text": "🗑 Очистить", "callback_data": f"ob_clear_{step}"}] if current else [],
                 [{"text": t("back_btn",uid), "callback_data": "ob_menu"}],
             ] if current else [[{"text": t("back_btn",uid), "callback_data": "ob_menu"}]]})


    elif data == "my_bot_status":
        if not user.get("registered"): return
        lang = user.get("lang","ru")
        bot_link = user.get("bot_link")
        if bot_link:
            # Бот готов — показываем ссылку
            labels = {
                "ru": f"🤖 *Ваш бот готов!*\n\nСсылка для ваших клиентов:\n`{bot_link}`\n\nОтправьте эту ссылку клиентам — они смогут писать боту 24/7",
                "en": f"🤖 *Your bot is ready!*\n\nClient link:\n`{bot_link}`\n\nShare this with your clients",
                "uz": f"🤖 *Botingiz tayyor!*\n\nMijozlar uchun havola:\n`{bot_link}`\n\nBu havolani mijozlaringizga yuboring",
                "kz": f"🤖 *Ботыңыз дайын!*\n\nКлиенттер үшін сілтеме:\n`{bot_link}`",
                "zh": f"🤖 *您的机器人已准备好！*\n\n客户链接:\n`{bot_link}`",
                "ko": f"🤖 *봇 준비 완료!*\n\n고객 링크:\n`{bot_link}`",
            }
            edit(chat_id, msg_id, labels.get(lang, labels["ru"]), kb_back(uid,"dashboard"))
        else:
            # Бот ещё не готов
            labels = {
                "ru": "🤖 *Ваш бот*\n\n⏳ Мы готовим вашего бота!\n\nКак только будет готов — вы получите ссылку прямо сюда.\n\n_Обычно это занимает до 24 часов_ 🚀",
                "en": "🤖 *Your bot*\n\n⏳ We're setting up your bot!\n\nOnce ready, you'll receive the link here.\n\n_Usually within 24 hours_ 🚀",
                "uz": "🤖 *Botingiz*\n\n⏳ Botingizni tayyorlamoqdamiz!\n\nTayyor bo'lgach, havola shu yerga yuboriladi.\n\n_Odatda 24 soat ichida_ 🚀",
                "kz": "🤖 *Ботыңыз*\n\n⏳ Ботыңызды дайындаудамыз!\n\nДайын болғанда сілтеме осында жіберіледі.\n\n_Әдетте 24 сағат ішінде_ 🚀",
                "zh": "🤖 *您的机器人*\n\n⏳ 我们正在为您设置机器人！\n\n准备好后，链接将发送到这里。\n\n_通常在24小时内_ 🚀",
                "ko": "🤖 *봇 상태*\n\n⏳ 봇을 준비 중입니다!\n\n준비되면 링크가 여기로 전송됩니다.\n\n_보통 24시간 이내_ 🚀",
            }
            edit(chat_id, msg_id, labels.get(lang, labels["ru"]), kb_back(uid,"dashboard"))

    elif data == "ob_menu":
        user = get_user(uid)
        edit(chat_id, msg_id, onboarding_text(uid, user), onboarding_kb(uid))

    elif data.startswith("ob_clear_"):
        step = data[9:]
        user.pop(f"info_{step}", None)
        set_user(uid, user)
        edit(chat_id, msg_id, onboarding_text(uid, user), onboarding_kb(uid))


    elif data == "set_avatar":
        set_state(uid, {"step":"upload_avatar"})
        lang = user.get("lang","ru")
        labels = {
            "ru": "🖼 *Аватарка бота*\n\nОтправьте фото логотипа вашего бизнеса.\nЭто фото будет отображаться в профиле бота.",
            "en": "🖼 *Bot avatar*\n\nSend a photo of your business logo.",
            "uz": "🖼 *Bot avatari*\n\nBiznes logotipingiz rasmini yuboring.",
            "kz": "🖼 *Бот аватары*\n\nБизнес логотипіңіздің суретін жіберіңіз.",
            "zh": "🖼 *机器人头像*\n\n请发送您的业务标志照片。",
            "ko": "🖼 *봇 아바타*\n\n비즈니스 로고 사진을 보내주세요.",
        }
        edit(chat_id, msg_id, labels.get(lang, labels["ru"]), kb_back(uid,"settings"))

    elif data == "edit_req":
        set_state(uid, {"step":"edit_req"})
        edit(chat_id, msg_id, t("edit_req_text",uid), kb_back(uid,"dashboard"))

    elif data == "plan":
        if not user.get("registered"): return
        p = PLANS[user.get("plan","free")]
        edit(chat_id, msg_id,
             f"💰 {p['emoji']} *{p['name']}* — {9999} msg/mo",
             kb_plans_upgrade(uid))

    elif data in ("buy_basic","buy_pro"):
        plan_key = "basic" if data == "buy_basic" else "pro"
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


    # ── Клиент бизнеса ──
    elif data.startswith("c_"):
        parts = data.split("_", 2)
        if len(parts) >= 3:
            action = parts[1]
            biz_id = parts[2]
            biz = get_user(int(biz_id)) if biz_id.isdigit() else {}
            lang = user.get("lang","ru")
            
            field_map = {
                "menu":  ("info_menu",  {"ru":"🍽 *Меню:*","en":"🍽 *Menu:*","uz":"🍽 *Menyu:*","kz":"🍽 *Мәзір:*","zh":"🍽 *菜单:*","ko":"🍽 *메뉴:*"}),
                "hours": ("info_hours", {"ru":"🕐 *Часы работы:*","en":"🕐 *Working hours:*","uz":"🕐 *Ish vaqti:*","kz":"🕐 *Жұмыс уақыты:*","zh":"🕐 *营业时间:*","ko":"🕐 *영업시간:*"}),
                "loc":   ("info_location",{"ru":"📍 *Адрес:*","en":"📍 *Address:*","uz":"📍 *Manzil:*","kz":"📍 *Мекенжай:*","zh":"📍 *地址:*","ko":"📍 *주소:*"}),
                "cont":  ("info_contacts",{"ru":"📞 *Контакты:*","en":"📞 *Contacts:*","uz":"📞 *Kontaktlar:*","kz":"📞 *Байланыс:*","zh":"📞 *联系方式:*","ko":"📞 *연락처:*"}),
                "promo": ("info_promo",  {"ru":"🎁 *Акции:*","en":"🎁 *Promotions:*","uz":"🎁 *Aksiyalar:*","kz":"🎁 *Акциялар:*","zh":"🎁 *促销:*","ko":"🎁 *프로모션:*"}),
            }
            
            if action in field_map:
                field, title_map = field_map[action]
                val = biz.get(field)
                title = title_map.get(lang, title_map["ru"])
                empty_labels = {"ru":"Информация пока не добавлена","en":"No info yet","uz":"Ma'lumot yo'q","kz":"Ақпарат жоқ","zh":"暂无信息","ko":"정보 없음"}
                text = f"{title}\n\n{val}" if val else empty_labels.get(lang,"—")
                edit(chat_id, msg_id, text, kb_back(uid, "start"))

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


    # Админ отправляет ссылку клиенту
    if step and step.startswith("send_link_") and uid == ADMIN_ID:
        target_uid = int(step.split("_")[2])
        bot_link = text.strip()
        # Сохраняем ссылку клиенту
        target = get_user(target_uid)
        target["bot_link"] = bot_link
        set_user(target_uid, target)
        del_state(uid)
        # Уведомляем клиента
        target_lang = target.get("lang","ru")
        msgs = {
            "ru": f"🎉 *Ваш бот готов!*\n\nВот ваша ссылка — поделитесь с клиентами:\n`{bot_link}`\n\nОткройте панель управления чтобы следить за статистикой 📊",
            "en": f"🎉 *Your bot is ready!*\n\nHere's your link — share with clients:\n`{bot_link}`",
            "uz": f"🎉 *Botingiz tayyor!*\n\nHavola — mijozlarga ulashing:\n`{bot_link}`\n\nStatistikani kuzatish uchun boshqaruv panelini oching 📊",
            "kz": f"🎉 *Ботыңыз дайын!*\n\nСілтеме — клиенттерге жіберіңіз:\n`{bot_link}`",
            "zh": f"🎉 *您的机器人已准备好！*\n\n链接 — 与客户分享:\n`{bot_link}`",
            "ko": f"🎉 *봇 준비 완료!*\n\n링크 — 고객과 공유하세요:\n`{bot_link}`",
        }
        send(target_uid, msgs.get(target_lang, msgs["ru"]), kb_dashboard(target_uid))
        send(chat_id, f"✅ Ссылка отправлена клиенту {target.get('name','?')}!")
        return

    # Если пользователь — клиент бизнеса
    if user.get("client_of") and not step:
        biz_id = user["client_of"]
        biz = get_user(int(biz_id)) if str(biz_id).isdigit() else {}
        if biz:
            # Обновляем статистику
            s = biz.get("stats", {"today":0,"total":0,"users":0,"orders":0})
            s["today"] = s.get("today", 0) + 1
            s["total"] = s.get("total", 0) + 1
            biz["stats"] = s
            set_user(int(biz_id), biz)
            
            # Отвечаем данными бизнеса
            lang = user.get("lang","ru")
            info = []
            if biz.get("info_menu"): info.append(f"Меню: {biz['info_menu']}")
            if biz.get("info_hours"): info.append(f"Часы: {biz['info_hours']}")
            if biz.get("info_location"): info.append(f"Адрес: {biz['info_location']}")
            if biz.get("info_contacts"): info.append(f"Контакты: {biz['info_contacts']}")
            
            fallback = {
                "ru": f"Спасибо за вопрос! Мы свяжемся с вами в ближайшее время 🙏",
                "en": f"Thank you! We'll get back to you soon 🙏",
                "uz": f"Savolingiz uchun rahmat! Tez orada bog'lanamiz 🙏",
                "kz": f"Рахмет! Жақын арада хабарласамыз 🙏",
                "zh": f"谢谢您的提问！我们会尽快回复您 🙏",
                "ko": f"질문 감사합니다! 곧 연락드리겠습니다 🙏",
            }
            send(chat_id, fallback.get(lang, fallback["ru"]))
            return




    # Загрузка аватарки бота
    if msg_type == "photo" and step == "upload_avatar":
        del_state(uid)
        # Сохраняем file_id последней фотки
        # (file_id придёт в теле сообщения)
        lang = user.get("lang","ru")
        saved = {"ru":"✅ Аватарка сохранена! Теперь бот будет с вашим логотипом 🎨",
                 "en":"✅ Avatar saved! Your bot now has your logo 🎨",
                 "uz":"✅ Avatar saqlandi! Botingiz endi logotipingiz bilan 🎨",
                 "kz":"✅ Аватар сақталды! Ботыңыз енді логотипіңізбен 🎨",
                 "zh":"✅ 头像已保存！您的机器人现在有了您的标志 🎨",
                 "ko":"✅ 아바타 저장됨! 봇에 로고가 적용되었습니다 🎨"}
        send(chat_id, saved.get(lang, saved["ru"]), kb_dashboard(uid))
        return

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
        # Добавляем в список клиентов
        clients = kv_get("all_clients") or []
        if str(uid) not in clients:
            clients.append(str(uid))
            kv_set("all_clients", clients)

        send(ADMIN_ID,
             f"🆕 *Новый клиент Zevo!*\n\n"
             f"👤 @{username} (ID: `{uid}`)\n"
             f"🏢 {n}\n📂 {cat}\n"
             f"🌍 {LANGS.get(user.get('lang','ru'),'?')}\n\n"
             f"🔗 Ссылка клиента:\n`https://t.me/Zevo_bbot?start=biz_{uid}`",
             {"inline_keyboard": [
                 [{"text":"🔗 Отправить ссылку бота","callback_data":f"send_bot_link_{uid}"}],
                 [{"text":"⛔ Заблокировать","callback_data":f"block_{uid}"}],
             ]})
        # Сначала поздравление
        send(chat_id, t("registered",uid,name=n))
        import time; time.sleep(0.5)
        # Потом сразу ТЗ
        lang = user.get("lang","ru")
        tz_intro = {
            "ru": (
                "📋 *Заполните ТЗ для вашего бота*\n\n"
                "Чем подробнее заполните — тем лучше бот отвечает вашим клиентам.\n\n"
                "Рекомендуем заполнить все разделы 👇"
            ),
            "en": (
                "📋 *Fill in your bot's info*\n\n"
                "The more details you add — the better your bot answers clients.\n\n"
                "We recommend filling all sections 👇"
            ),
            "uz": (
                "📋 *Bot uchun ma\'lumot to\'ldiring*\n\n"
                "Qancha ko\'p ma\'lumot — shuncha aqlli javob beradi.\n\n"
                "Barcha bo\'limlarni to\'ldirishni tavsiya qilamiz 👇"
            ),
            "kz": (
                "📋 *Бот үшін ТЗ толтырыңыз*\n\n"
                "Неғұрлым толық болса — бот соғұрлым жақсы жауап береді.\n\n"
                "Барлық бөлімдерді толтыруды ұсынамыз 👇"
            ),
            "zh": (
                "📋 *填写机器人信息*\n\n"
                "信息越详细 — 机器人回答越准确。\n\n"
                "建议填写所有部分 👇"
            ),
            "ko": (
                "📋 *봇 정보 작성*\n\n"
                "자세할수록 봇이 더 정확하게 답변합니다.\n\n"
                "모든 섹션을 작성하는 것을 권장합니다 👇"
            ),
        }
        send(chat_id, tz_intro.get(lang, tz_intro["ru"]))
        time.sleep(0.3)
        send(chat_id, onboarding_text(uid, user), onboarding_kb(uid))


    elif step and step.startswith("ob_"):
        field = step[3:]
        user[f"info_{field}"] = text
        set_user(uid, user)
        del_state(uid)
        lang = user.get("lang","ru")
        saved_labels = {"ru":"✅ Сохранено!","en":"✅ Saved!","uz":"✅ Saqlandi!","kz":"✅ Сақталды!","zh":"✅ 已保存！","ko":"✅ 저장됨!"}
        send(chat_id, saved_labels.get(lang,"✅"), onboarding_kb(uid))

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
                    payload = text.split(" ")[1] if " " in text else ""
                    on_start(uid, name, cid, tg_lang, payload)
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
