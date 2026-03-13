import json
import os
import urllib.request
from http.server import BaseHTTPRequestHandler

TOKEN        = os.environ.get("BOT_TOKEN", "")
MINI_APP_URL = os.environ.get("MINI_APP_URL", "")
CARD_VISA    = os.environ.get("CARD_VISA", "")
CARD_HUMO    = os.environ.get("CARD_HUMO", "")
ADMIN_ID     = int(os.environ.get("ADMIN_ID", "7732138103"))
API          = f"https://api.telegram.org/bot{TOKEN}"

db               = {}
states           = {}
pending_payments = {}
user_lang        = {}  # {uid: lang_code}

# ── Переводы ──────────────────────────────────────────────────────────────────

LANGS = {
    "ru": "🇷🇺 Русский",
    "en": "🇬🇧 English",
    "uz": "🇺🇿 O'zbek",
    "kz": "🇰🇿 Қазақша",
    "zh": "🇨🇳 中文",
    "ko": "🇰🇷 한국어",
}

T = {
    "welcome": {
        "ru": "👋 Привет, *{name}*!\n\n*Zevo* — платформа AI-ботов для вашего бизнеса.\n\n✅ Отвечает клиентам 24/7\n✅ Принимает заказы и бронирования\n✅ Статистика в реальном времени\n✅ Настройка за 5 минут — без кода",
        "en": "👋 Hello, *{name}*!\n\n*Zevo* — AI bot platform for your business.\n\n✅ Replies to clients 24/7\n✅ Accepts orders & bookings\n✅ Real-time statistics\n✅ Setup in 5 minutes — no code",
        "uz": "👋 Salom, *{name}*!\n\n*Zevo* — biznesingiz uchun AI-bot platformasi.\n\n✅ Mijozlarga 24/7 javob beradi\n✅ Buyurtma va bronlarni qabul qiladi\n✅ Real vaqtda statistika\n✅ 5 daqiqada sozlash — kodsiz",
        "kz": "👋 Сәлем, *{name}*!\n\n*Zevo* — бизнесіңіз үшін AI-бот платформасы.\n\n✅ Клиенттерге 24/7 жауап береді\n✅ Тапсырыстар мен брондауларды қабылдайды\n✅ Нақты уақытта статистика\n✅ 5 минутта баптау — коссыз",
        "zh": "👋 你好, *{name}*!\n\n*Zevo* — 企业AI机器人平台。\n\n✅ 24/7回复客户\n✅ 接受订单和预订\n✅ 实时统计\n✅ 5分钟设置 — 无需代码",
        "ko": "👋 안녕하세요, *{name}*!\n\n*Zevo* — 비즈니스를 위한 AI 봇 플랫폼입니다.\n\n✅ 24/7 고객 응답\n✅ 주문 및 예약 수락\n✅ 실시간 통계\n✅ 5분 설정 — 코드 없이",
    },
    "choose_lang": {
        "ru": "🌍 Выберите язык:",
        "en": "🌍 Choose language:",
        "uz": "🌍 Tilni tanlang:",
        "kz": "🌍 Тілді таңдаңыз:",
        "zh": "🌍 选择语言：",
        "ko": "🌍 언어를 선택하세요:",
    },
    "register_btn": {
        "ru": "🚀 Подключить бота для бизнеса",
        "en": "🚀 Connect bot for business",
        "uz": "🚀 Biznes uchun bot ulash",
        "kz": "🚀 Бизнес үшін бот қосу",
        "zh": "🚀 为企业接入机器人",
        "ko": "🚀 비즈니스 봇 연결",
    },
    "how_btn": {
        "ru": "📖 Как это работает",
        "en": "📖 How it works",
        "uz": "📖 Qanday ishlaydi",
        "kz": "📖 Қалай жұмыс істейді",
        "zh": "📖 如何使用",
        "ko": "📖 사용 방법",
    },
    "plans_btn": {
        "ru": "💰 Тарифы",
        "en": "💰 Plans",
        "uz": "💰 Tariflar",
        "kz": "💰 Тарифтер",
        "zh": "💰 套餐",
        "ko": "💰 요금제",
    },
    "back_btn": {
        "ru": "◀️ Назад",
        "en": "◀️ Back",
        "uz": "◀️ Orqaga",
        "kz": "◀️ Артқа",
        "zh": "◀️ 返回",
        "ko": "◀️ 뒤로",
    },
    "how_text": {
        "ru": "📖 *Как работает Zevo?*\n\n1️⃣ Регистрируете бизнес\n2️⃣ Настраиваете бота под себя\n3️⃣ Даёте ссылку клиентам\n4️⃣ Бот работает сам 24/7\n5️⃣ Видите статистику в дашборде\n\n⏱ Настройка занимает *5 минут*",
        "en": "📖 *How does Zevo work?*\n\n1️⃣ Register your business\n2️⃣ Customize your bot\n3️⃣ Share the link with clients\n4️⃣ Bot works 24/7 automatically\n5️⃣ View stats in dashboard\n\n⏱ Setup takes *5 minutes*",
        "uz": "📖 *Zevo qanday ishlaydi?*\n\n1️⃣ Biznesingizni ro'yxatdan o'tkazing\n2️⃣ Botni sozlang\n3️⃣ Mijozlarga havola bering\n4️⃣ Bot 24/7 o'zi ishlaydi\n5️⃣ Statistikani ko'ring\n\n⏱ Sozlash *5 daqiqa* oladi",
        "kz": "📖 *Zevo қалай жұмыс істейді?*\n\n1️⃣ Бизнесті тіркеңіз\n2️⃣ Ботты баптаңыз\n3️⃣ Клиенттерге сілтеме беріңіз\n4️⃣ Бот 24/7 жұмыс істейді\n5️⃣ Статистиканы көріңіз\n\n⏱ Баптау *5 минут* алады",
        "zh": "📖 *Zevo如何工作？*\n\n1️⃣ 注册您的企业\n2️⃣ 自定义您的机器人\n3️⃣ 与客户分享链接\n4️⃣ 机器人24/7自动工作\n5️⃣ 在仪表板查看统计\n\n⏱ 设置只需*5分钟*",
        "ko": "📖 *Zevo는 어떻게 작동하나요?*\n\n1️⃣ 비즈니스 등록\n2️⃣ 봇 커스터마이징\n3️⃣ 고객에게 링크 공유\n4️⃣ 봇이 24/7 자동 작동\n5️⃣ 대시보드에서 통계 확인\n\n⏱ 설정은 *5분* 소요",
    },
    "plans_text": {
        "ru": "💰 *Тарифы Zevo*\n\n🆓 *Free* — бесплатно\n  • До 100 сообщений/мес\n\n⚡ *Starter* — $29/мес\n  • До 1 000 сообщений/мес\n  • 3 бота\n\n🚀 *Pro* — $79/мес\n  • Безлимит\n  • Кастомный AI",
        "en": "💰 *Zevo Plans*\n\n🆓 *Free* — free\n  • Up to 100 messages/mo\n\n⚡ *Starter* — $29/mo\n  • Up to 1,000 messages/mo\n  • 3 bots\n\n🚀 *Pro* — $79/mo\n  • Unlimited\n  • Custom AI",
        "uz": "💰 *Zevo Tariflari*\n\n🆓 *Free* — bepul\n  • Oyiga 100 ta xabargacha\n\n⚡ *Starter* — $29/oy\n  • Oyiga 1 000 ta xabar\n  • 3 ta bot\n\n🚀 *Pro* — $79/oy\n  • Cheksiz\n  • Maxsus AI",
        "kz": "💰 *Zevo Тарифтері*\n\n🆓 *Free* — тегін\n  • Айына 100 хабарға дейін\n\n⚡ *Starter* — $29/ай\n  • Айына 1 000 хабар\n  • 3 бот\n\n🚀 *Pro* — $79/ай\n  • Шексіз\n  • Арнайы AI",
        "zh": "💰 *Zevo套餐*\n\n🆓 *免费版* — 免费\n  • 每月最多100条消息\n\n⚡ *入门版* — $29/月\n  • 每月最多1,000条消息\n  • 3个机器人\n\n🚀 *专业版* — $79/月\n  • 无限制\n  • 自定义AI",
        "ko": "💰 *Zevo 요금제*\n\n🆓 *무료* — 무료\n  • 월 100개 메시지\n\n⚡ *스타터* — $29/월\n  • 월 1,000개 메시지\n  • 봇 3개\n\n🚀 *프로* — $79/월\n  • 무제한\n  • 커스텀 AI",
    },
    "reg_ask_name": {
        "ru": "🏢 *Регистрация*\n\nКак называется ваш бизнес?",
        "en": "🏢 *Registration*\n\nWhat is your business name?",
        "uz": "🏢 *Ro'yxatdan o'tish*\n\nBiznesingiz nomi nima?",
        "kz": "🏢 *Тіркеу*\n\nБизнесіңіздің атауы қандай?",
        "zh": "🏢 *注册*\n\n您的企业名称是什么？",
        "ko": "🏢 *등록*\n\n비즈니스 이름이 무엇인가요?",
    },
    "choose_category": {
        "ru": "Выберите категорию:",
        "en": "Choose category:",
        "uz": "Kategoriyani tanlang:",
        "kz": "Санатты таңдаңыз:",
        "zh": "选择类别：",
        "ko": "카테고리를 선택하세요:",
    },
    "ask_desc": {
        "ru": "Опишите ваш бизнес в 2–3 предложениях.\n\n_AI будет использовать это для ответов клиентам._",
        "en": "Describe your business in 2–3 sentences.\n\n_AI will use this to answer clients._",
        "uz": "Biznesingizni 2–3 jumlada tasvirlab bering.\n\n_AI bu ma'lumotdan foydalanadi._",
        "kz": "Бизнесіңізді 2–3 сөйлеммен сипаттаңыз.\n\n_AI бұны клиенттерге жауап беруге пайдаланады._",
        "zh": "用2-3句话描述您的企业。\n\n_AI将用此回答客户。_",
        "ko": "비즈니스를 2-3문장으로 설명해 주세요.\n\n_AI가 고객 응답에 사용합니다._",
    },
    "registered_ok": {
        "ru": "🎉 *{name}* зарегистрирован!\n\nВаш AI-бот готов к работе 👇",
        "en": "🎉 *{name}* registered!\n\nYour AI bot is ready 👇",
        "uz": "🎉 *{name}* ro'yxatdan o'tdi!\n\nAI-botingiz tayyor 👇",
        "kz": "🎉 *{name}* тіркелді!\n\nAI-ботыңыз дайын 👇",
        "zh": "🎉 *{name}* 已注册！\n\n您的AI机器人已就绪 👇",
        "ko": "🎉 *{name}* 등록 완료!\n\nAI 봇이 준비되었습니다 👇",
    },
    "stats_btn": {
        "ru": "📊 Статистика", "en": "📊 Statistics", "uz": "📊 Statistika",
        "kz": "📊 Статистика", "zh": "📊 统计", "ko": "📊 통계",
    },
    "settings_btn": {
        "ru": "⚙️ Настройки", "en": "⚙️ Settings", "uz": "⚙️ Sozlamalar",
        "kz": "⚙️ Параметрлер", "zh": "⚙️ 设置", "ko": "⚙️ 설정",
    },
    "edit_btn": {
        "ru": "✏️ Заказать правки", "en": "✏️ Request changes", "uz": "✏️ O'zgarish so'rash",
        "kz": "✏️ Өзгерту сұрау", "zh": "✏️ 请求修改", "ko": "✏️ 수정 요청",
    },
    "plan_btn": {
        "ru": "💰 Тариф", "en": "💰 Plan", "uz": "💰 Tarif",
        "kz": "💰 Тариф", "zh": "💰 套餐", "ko": "💰 요금제",
    },
    "open_app_btn": {
        "ru": "📱 Открыть панель управления", "en": "📱 Open dashboard",
        "uz": "📱 Boshqaruv panelini ochish", "kz": "📱 Басқару панелін ашу",
        "zh": "📱 打开控制面板", "ko": "📱 대시보드 열기",
    },
    "payment_text": {
        "ru": "💳 *Оплата — {plan}*\n\nСумма: *${price}/мес*\n\nПереведите на одну из карт:\n{cards}\nПосле оплаты нажмите кнопку и отправьте скрин чека 👇",
        "en": "💳 *Payment — {plan}*\n\nAmount: *${price}/mo*\n\nTransfer to one of the cards:\n{cards}\nAfter payment, press the button and send receipt screenshot 👇",
        "uz": "💳 *To'lov — {plan}*\n\nSumma: *${price}/oy*\n\nQuyidagi kartalardan biriga o'tkazing:\n{cards}\nTo'lovdan so'ng tugmani bosing va chek rasmini yuboring 👇",
        "kz": "💳 *Төлем — {plan}*\n\nСома: *${price}/ай*\n\nКарталардың біріне аударыңыз:\n{cards}\nТөлегеннен кейін түймені басып, чек скриншотын жіберіңіз 👇",
        "zh": "💳 *付款 — {plan}*\n\n金额: *${price}/月*\n\n转账到以下卡片之一:\n{cards}\n付款后，点击按钮发送收据截图 👇",
        "ko": "💳 *결제 — {plan}*\n\n금액: *${price}/월*\n\n다음 카드 중 하나로 이체하세요:\n{cards}\n결제 후 버튼을 누르고 영수증 스크린샷을 보내주세요 👇",
    },
    "check_sent_btn": {
        "ru": "✅ Я отправил чек", "en": "✅ I sent the receipt",
        "uz": "✅ Chekni yubordim", "kz": "✅ Чекті жібердім",
        "zh": "✅ 我已发送收据", "ko": "✅ 영수증 보냄",
    },
    "send_check": {
        "ru": "📸 Отправьте скрин или фото чека об оплате 👇\n\n_Проверим и активируем тариф в течение 10 минут_",
        "en": "📸 Send a screenshot or photo of the payment receipt 👇\n\n_We'll verify and activate your plan within 10 minutes_",
        "uz": "📸 To'lov chekining skrinshot yoki rasmini yuboring 👇\n\n_10 daqiqa ichida tarifni faollashtiramiz_",
        "kz": "📸 Төлем чегінің скриншотын немесе фотосын жіберіңіз 👇\n\n_10 минут ішінде тарифті іске қосамыз_",
        "zh": "📸 发送付款收据的截图或照片 👇\n\n_我们将在10分钟内验证并激活您的套餐_",
        "ko": "📸 결제 영수증의 스크린샷이나 사진을 보내주세요 👇\n\n_10분 내에 확인하고 요금제를 활성화합니다_",
    },
    "check_received": {
        "ru": "✅ *Чек получен!*\n\nПроверяем оплату — обычно до 10 минут.\nПосле подтверждения тариф активируется автоматически 🎉",
        "en": "✅ *Receipt received!*\n\nChecking payment — usually up to 10 minutes.\nAfter confirmation, the plan activates automatically 🎉",
        "uz": "✅ *Chek qabul qilindi!*\n\nTo'lovni tekshiramiz — odatda 10 daqiqagacha.\nTasdiqlangandan so'ng tarif avtomatik faollashadi 🎉",
        "kz": "✅ *Чек алынды!*\n\nТөлемді тексеруде — әдетте 10 минутқа дейін.\nРастаудан кейін тариф автоматты түрде іске қосылады 🎉",
        "zh": "✅ *收到收据！*\n\n正在检查付款 — 通常最多10分钟。\n确认后，套餐将自动激活 🎉",
        "ko": "✅ *영수증 수령!*\n\n결제 확인 중 — 보통 10분 이내.\n확인 후 요금제가 자동으로 활성화됩니다 🎉",
    },
    "plan_confirmed": {
        "ru": "🎉 *Оплата подтверждена!*\n\nТариф *{plan}* активирован. Спасибо! 🙏",
        "en": "🎉 *Payment confirmed!*\n\nPlan *{plan}* activated. Thank you! 🙏",
        "uz": "🎉 *To'lov tasdiqlandi!*\n\n*{plan}* tarifi faollashtirildi. Rahmat! 🙏",
        "kz": "🎉 *Төлем расталды!*\n\n*{plan}* тарифі іске қосылды. Рахмет! 🙏",
        "zh": "🎉 *付款已确认！*\n\n*{plan}* 套餐已激活。谢谢！🙏",
        "ko": "🎉 *결제 확인!*\n\n*{plan}* 요금제가 활성화되었습니다. 감사합니다! 🙏",
    },
    "plan_rejected": {
        "ru": "❌ *Оплата не подтверждена*\n\nЧек не прошёл проверку. Свяжитесь с поддержкой.",
        "en": "❌ *Payment not confirmed*\n\nReceipt failed verification. Please contact support.",
        "uz": "❌ *To'lov tasdiqlanmadi*\n\nChek tekshiruvdan o'tmadi. Qo'llab-quvvatlash bilan bog'laning.",
        "kz": "❌ *Төлем расталмады*\n\nЧек тексеруден өтпеді. Қолдау қызметіне хабарласыңыз.",
        "zh": "❌ *付款未确认*\n\n收据验证失败。请联系支持。",
        "ko": "❌ *결제 미확인*\n\n영수증 확인 실패. 지원팀에 문의하세요.",
    },
    "edit_req_text": {
        "ru": "✏️ *Заказать правки*\n\nОпишите что нужно изменить:",
        "en": "✏️ *Request changes*\n\nDescribe what needs to be changed:",
        "uz": "✏️ *O'zgarish so'rash*\n\nNimani o'zgartirish kerakligini tasvirlab bering:",
        "kz": "✏️ *Өзгерту сұрау*\n\nНені өзгерту керектігін сипаттаңыз:",
        "zh": "✏️ *请求修改*\n\n描述需要更改的内容：",
        "ko": "✏️ *수정 요청*\n\n변경이 필요한 사항을 설명해 주세요:",
    },
    "edit_accepted": {
        "ru": "✅ *Заявка принята!*\n\nСвяжемся в течение 24 часов.",
        "en": "✅ *Request accepted!*\n\nWe'll contact you within 24 hours.",
        "uz": "✅ *So'rov qabul qilindi!*\n\n24 soat ichida bog'lanamiz.",
        "kz": "✅ *Сұраныс қабылданды!*\n\n24 сағат ішінде хабарласамыз.",
        "zh": "✅ *请求已接受！*\n\n我们将在24小时内联系您。",
        "ko": "✅ *요청 수락!*\n\n24시간 내에 연락드리겠습니다.",
    },
    "settings_text": {
        "ru": "⚙️ *Настройки*\n\nЧто хотите изменить?",
        "en": "⚙️ *Settings*\n\nWhat would you like to change?",
        "uz": "⚙️ *Sozlamalar*\n\nNimani o'zgartirmoqchisiz?",
        "kz": "⚙️ *Параметрлер*\n\nНені өзгерткіңіз келеді?",
        "zh": "⚙️ *设置*\n\n您想更改什么？",
        "ko": "⚙️ *설정*\n\n무엇을 변경하시겠습니까?",
    },
    "saved": {
        "ru": "✅ Сохранено!", "en": "✅ Saved!", "uz": "✅ Saqlandi!",
        "kz": "✅ Сақталды!", "zh": "✅ 已保存！", "ko": "✅ 저장됨!",
    },
    "change_lang_btn": {
        "ru": "🌍 Язык", "en": "🌍 Language", "uz": "🌍 Til",
        "kz": "🌍 Тіл", "zh": "🌍 语言", "ko": "🌍 언어",
    },
}

def t(key, uid, **kwargs):
    lang = user_lang.get(uid, "ru")
    text = T.get(key, {}).get(lang, T.get(key, {}).get("ru", ""))
    return text.format(**kwargs) if kwargs else text

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
    if kb: kw["reply_markup"] = json.dumps(kb)
    tg("sendMessage", **kw)

def edit(chat_id, msg_id, text, kb=None, parse_mode="Markdown"):
    kw = dict(chat_id=chat_id, message_id=msg_id, text=text, parse_mode=parse_mode)
    if kb: kw["reply_markup"] = json.dumps(kb)
    tg("editMessageText", **kw)

def answer(cq_id):
    tg("answerCallbackQuery", callback_query_id=cq_id)

# ── Keyboards ─────────────────────────────────────────────────────────────────

def kb_lang():
    return {"inline_keyboard": [
        [{"text": "🇷🇺 Русский",  "callback_data": "lang_ru"},
         {"text": "🇬🇧 English",  "callback_data": "lang_en"}],
        [{"text": "🇺🇿 O'zbek",   "callback_data": "lang_uz"},
         {"text": "🇰🇿 Қазақша", "callback_data": "lang_kz"}],
        [{"text": "🇨🇳 中文",     "callback_data": "lang_zh"},
         {"text": "🇰🇷 한국어",   "callback_data": "lang_ko"}],
    ]}

def kb_start(uid):
    return {"inline_keyboard": [
        [{"text": t("register_btn", uid), "callback_data": "register"}],
        [{"text": t("how_btn", uid),      "callback_data": "how"},
         {"text": t("plans_btn", uid),    "callback_data": "plans"}],
        [{"text": t("change_lang_btn", uid), "callback_data": "choose_lang"}],
    ]}

def kb_back(uid, to):
    return {"inline_keyboard": [[{"text": t("back_btn", uid), "callback_data": to}]]}

def kb_categories(uid):
    lang = user_lang.get(uid, "ru")
    cats = {
        "ru": [["🍕 Кафе/Ресторан","💇 Салон красоты"],["🛍 Магазин","🏋️ Фитнес"],["🏥 Медицина","📦 Другое"]],
        "en": [["🍕 Cafe/Restaurant","💇 Beauty salon"],["🛍 Shop","🏋️ Fitness"],["🏥 Medical","📦 Other"]],
        "uz": [["🍕 Kafe/Restoran","💇 Go'zallik saloni"],["🛍 Do'kon","🏋️ Fitnes"],["🏥 Tibbiyot","📦 Boshqa"]],
        "kz": [["🍕 Кафе/Мейрамхана","💇 Сұлулық салоны"],["🛍 Дүкен","🏋️ Фитнес"],["🏥 Медицина","📦 Басқа"]],
        "zh": [["🍕 咖啡馆/餐厅","💇 美容院"],["🛍 商店","🏋️ 健身"],["🏥 医疗","📦 其他"]],
        "ko": [["🍕 카페/레스토랑","💇 미용실"],["🛍 상점","🏋️ 피트니스"],["🏥 의료","📦 기타"]],
    }
    keys = [["cat_cafe","cat_salon"],["cat_shop","cat_fitness"],["cat_medical","cat_other"]]
    labels = cats.get(lang, cats["ru"])
    return {"inline_keyboard": [
        [{"text": labels[i][j], "callback_data": keys[i][j]} for j in range(2)]
        for i in range(3)
    ]}

def kb_dashboard(uid):
    rows = [
        [{"text": t("stats_btn", uid),    "callback_data": "stats"},
         {"text": t("settings_btn", uid), "callback_data": "settings"}],
        [{"text": t("edit_btn", uid),     "callback_data": "edit_req"},
         {"text": t("plan_btn", uid),     "callback_data": "plan"}],
        [{"text": t("change_lang_btn", uid), "callback_data": "choose_lang"}],
    ]
    if MINI_APP_URL:
        rows.insert(2, [{"text": t("open_app_btn", uid), "web_app": {"url": MINI_APP_URL}}])
    return {"inline_keyboard": rows}

def kb_settings(uid):
    lang = user_lang.get(uid, "ru")
    desc_labels = {"ru":"📝 Описание","en":"📝 Description","uz":"📝 Tavsif","kz":"📝 Сипаттама","zh":"📝 描述","ko":"📝 설명"}
    hours_labels = {"ru":"🕐 Часы работы","en":"🕐 Working hours","uz":"🕐 Ish vaqti","kz":"🕐 Жұмыс уақыты","zh":"🕐 营业时间","ko":"🕐 영업시간"}
    menu_labels = {"ru":"📋 Меню/Услуги","en":"📋 Menu/Services","uz":"📋 Menyu/Xizmatlar","kz":"📋 Мәзір/Қызметтер","zh":"📋 菜单/服务","ko":"📋 메뉴/서비스"}
    return {"inline_keyboard": [
        [{"text": desc_labels.get(lang,"📝"), "callback_data": "set_desc"}],
        [{"text": hours_labels.get(lang,"🕐"), "callback_data": "set_hours"}],
        [{"text": menu_labels.get(lang,"📋"), "callback_data": "set_menu"}],
        [{"text": t("back_btn", uid), "callback_data": "dashboard"}],
    ]}

def kb_plans_upgrade(uid):
    return {"inline_keyboard": [
        [{"text": "⚡ Starter — $29/мес", "callback_data": "buy_starter"}],
        [{"text": "🚀 Pro — $79/мес",     "callback_data": "buy_pro"}],
        [{"text": t("back_btn", uid),      "callback_data": "dashboard"}],
    ]}

CATEGORIES_RU = {
    "cat_cafe": "🍕 Кафе/Ресторан", "cat_salon": "💇 Салон красоты",
    "cat_shop": "🛍 Магазин",        "cat_fitness": "🏋️ Фитнес",
    "cat_medical": "🏥 Медицина",    "cat_other": "📦 Другое",
}
CATEGORIES_LOCAL = {
    "cat_cafe":    {"ru":"🍕 Кафе/Ресторан","en":"🍕 Cafe/Restaurant","uz":"🍕 Kafe/Restoran","kz":"🍕 Кафе/Мейрамхана","zh":"🍕 咖啡馆","ko":"🍕 카페"},
    "cat_salon":   {"ru":"💇 Салон","en":"💇 Beauty salon","uz":"💇 Salon","kz":"💇 Салон","zh":"💇 美容院","ko":"💇 미용실"},
    "cat_shop":    {"ru":"🛍 Магазин","en":"🛍 Shop","uz":"🛍 Do'kon","kz":"🛍 Дүкен","zh":"🛍 商店","ko":"🛍 상점"},
    "cat_fitness": {"ru":"🏋️ Фитнес","en":"🏋️ Fitness","uz":"🏋️ Fitnes","kz":"🏋️ Фитнес","zh":"🏋️ 健身","ko":"🏋️ 피트니스"},
    "cat_medical": {"ru":"🏥 Медицина","en":"🏥 Medical","uz":"🏥 Tibbiyot","kz":"🏥 Медицина","zh":"🏥 医疗","ko":"🏥 의료"},
    "cat_other":   {"ru":"📦 Другое","en":"📦 Other","uz":"📦 Boshqa","kz":"📦 Басқа","zh":"📦 其他","ko":"📦 기타"},
}

PLANS = {
    "free":    {"emoji": "🆓", "name": "Free",    "price": 0,   "limit": 100},
    "starter": {"emoji": "⚡", "name": "Starter", "price": 29,  "limit": 1000},
    "pro":     {"emoji": "🚀", "name": "Pro",     "price": 79,  "limit": 99999},
}

def text_dashboard(uid):
    biz = db[uid]
    s = biz["stats"]
    p = PLANS[biz["plan"]]
    lang = user_lang.get(uid, "ru")
    cat_local = CATEGORIES_LOCAL.get(biz.get("cat_key","cat_other"),{}).get(lang, biz["category"])
    labels = {
        "ru": ("Сегодня","Сообщений","Пользователей","Заказов","За всё время","сообщений"),
        "en": ("Today","Messages","Users","Orders","All time","messages"),
        "uz": ("Bugun","Xabarlar","Foydalanuvchilar","Buyurtmalar","Jami","xabar"),
        "kz": ("Бүгін","Хабарлар","Пайдаланушылар","Тапсырыстар","Барлық уақыт","хабар"),
        "zh": ("今天","消息","用户","订单","总计","条消息"),
        "ko": ("오늘","메시지","사용자","주문","전체","메시지"),
    }
    lb = labels.get(lang, labels["ru"])
    return (
        f"🏢 *{biz['name']}*\n"
        f"📂 {cat_local}  •  {p['emoji']} {p['name']}\n\n"
        f"📈 *{lb[0]}:*\n"
        f"  💬 {lb[1]}: *{s['today']}*\n"
        f"  👥 {lb[2]}: *{s['users']}*\n"
        f"  🛒 {lb[3]}: *{s['orders']}*\n\n"
        f"{lb[4]}: {s['total']} {lb[5]}"
    )

def show_payment(chat_id, uid, plan_key):
    plan = PLANS[plan_key]
    cards = ""
    if CARD_VISA: cards += f"💳 *Visa:* `{CARD_VISA}`\n"
    if CARD_HUMO: cards += f"🟠 *Humo:* `{CARD_HUMO}`\n"
    pending_payments[uid] = plan_key
    send(chat_id,
         t("payment_text", uid, plan=f"{plan['emoji']} {plan['name']}", price=plan['price'], cards=cards),
         {"inline_keyboard": [
             [{"text": t("check_sent_btn", uid), "callback_data": "check_sent"}],
             [{"text": t("back_btn", uid),        "callback_data": "plan"}],
         ]})

# ── Handlers ──────────────────────────────────────────────────────────────────

def on_start(uid, name, chat_id):
    if uid not in user_lang:
        send(chat_id, "🌍 Choose language / Выберите язык:", kb_lang())
        return
    if uid in db:
        send(chat_id, text_dashboard(uid), kb_dashboard(uid))
    else:
        send(chat_id, t("welcome", uid, name=name), kb_start(uid))

def on_callback(uid, chat_id, msg_id, data, cq_id, username, name):
    answer(cq_id)

    # Язык
    if data.startswith("lang_"):
        lang = data.split("_")[1]
        user_lang[uid] = lang
        if uid in db:
            edit(chat_id, msg_id, text_dashboard(uid), kb_dashboard(uid))
        else:
            edit(chat_id, msg_id, t("welcome", uid, name=name), kb_start(uid))
        return

    if data == "choose_lang":
        edit(chat_id, msg_id, "🌍 Choose language:", kb_lang())
        return

    if data == "how":
        edit(chat_id, msg_id, t("how_text", uid),
             {"inline_keyboard": [
                 [{"text": t("register_btn", uid), "callback_data": "register"},
                  {"text": t("back_btn", uid),     "callback_data": "start"}]
             ]})

    elif data == "plans":
        edit(chat_id, msg_id, t("plans_text", uid),
             {"inline_keyboard": [
                 [{"text": t("register_btn", uid), "callback_data": "register"}],
                 [{"text": t("back_btn", uid),     "callback_data": "start"}],
             ]})

    elif data == "start":
        if uid in db:
            edit(chat_id, msg_id, text_dashboard(uid), kb_dashboard(uid))
        else:
            edit(chat_id, msg_id, t("welcome", uid, name=name), kb_start(uid))

    elif data == "register":
        states[uid] = {"step": "name"}
        edit(chat_id, msg_id, t("reg_ask_name", uid), kb_back(uid, "start"))

    elif data.startswith("cat_") and data in CATEGORIES_RU:
        lang = user_lang.get(uid, "ru")
        cat_local = CATEGORIES_LOCAL.get(data, {}).get(lang, CATEGORIES_RU[data])
        cat_ru    = CATEGORIES_RU[data]
        if uid in states:
            states[uid]["category"]    = cat_local
            states[uid]["category_ru"] = cat_ru
            states[uid]["cat_key"]     = data
            states[uid]["step"]        = "desc"
        edit(chat_id, msg_id, f"✅ *{cat_local}*\n\n{t('ask_desc', uid)}")

    elif data == "dashboard":
        if uid in db:
            edit(chat_id, msg_id, text_dashboard(uid), kb_dashboard(uid))

    elif data == "stats":
        if uid not in db: return
        s = db[uid]["stats"]
        edit(chat_id, msg_id,
             f"📊 *{db[uid]['name']}*\n\n"
             f"💬 {s['today']} / 🧑 {s['users']} / 🛒 {s['orders']}",
             kb_back(uid, "dashboard"))

    elif data == "settings":
        if uid in db:
            edit(chat_id, msg_id, t("settings_text", uid), kb_settings(uid))

    elif data in ("set_desc", "set_hours", "set_menu"):
        states[uid] = {"step": {"set_desc":"s_desc","set_hours":"s_hours","set_menu":"s_menu"}[data]}
        edit(chat_id, msg_id, t("settings_text", uid), kb_back(uid, "settings"))

    elif data == "edit_req":
        states[uid] = {"step": "edit_req"}
        edit(chat_id, msg_id, t("edit_req_text", uid), kb_back(uid, "dashboard"))

    elif data == "plan":
        if uid not in db: return
        p = PLANS[db[uid]["plan"]]
        edit(chat_id, msg_id,
             f"💰 {p['emoji']} {p['name']} — {p['limit']} msg/mo",
             kb_plans_upgrade(uid))

    elif data in ("buy_starter", "buy_pro"):
        show_payment(chat_id, uid, "starter" if data == "buy_starter" else "pro")

    elif data == "check_sent":
        plan_key = pending_payments.get(uid, "starter")
        states[uid] = {"step": "awaiting_check", "plan": plan_key}
        biz_name = db[uid]["name"] if uid in db else "Unknown"
        plan = PLANS[plan_key]
        # Уведомление админу — всегда на русском
        send(ADMIN_ID,
             f"💰 *Новая оплата!*\n\n"
             f"👤 @{username} (ID: `{uid}`)\n"
             f"🏢 {biz_name}\n"
             f"📦 {plan['emoji']} {plan['name']} — ${plan['price']}\n"
             f"🌍 Язык: {LANGS.get(user_lang.get(uid,'ru'),'?')}\n\n"
             f"Ожидай скрин чека 👇",
             {"inline_keyboard": [[
                 {"text": "✅ Подтвердить", "callback_data": f"confirm_{uid}_{plan_key}"},
                 {"text": "❌ Отклонить",   "callback_data": f"reject_{uid}"},
             ]]})
        send(chat_id, t("send_check", uid))

    elif data.startswith("confirm_") and uid == ADMIN_ID:
        parts = data.split("_")
        target_uid, plan_key = int(parts[1]), parts[2]
        if target_uid in db:
            db[target_uid]["plan"] = plan_key
        plan = PLANS[plan_key]
        send(target_uid,
             t("plan_confirmed", target_uid, plan=f"{plan['emoji']} {plan['name']}"),
             kb_back(target_uid, "dashboard"))
        edit(chat_id, msg_id, f"✅ {plan['name']} активирован для {target_uid}")

    elif data.startswith("reject_") and uid == ADMIN_ID:
        target_uid = int(data.split("_")[1])
        send(target_uid, t("plan_rejected", target_uid), kb_back(target_uid, "plan"))
        edit(chat_id, msg_id, "❌ Оплата отклонена")

def on_message(uid, chat_id, text, username, message_id, msg_type, name):
    if uid not in user_lang:
        send(chat_id, "🌍 Choose language:", kb_lang())
        return

    st   = states.get(uid, {})
    step = st.get("step")

    if msg_type == "photo" and step == "awaiting_check":
        plan_key = st.get("plan", "starter")
        plan     = PLANS[plan_key]
        states.pop(uid, None)
        tg("forwardMessage", chat_id=ADMIN_ID, from_chat_id=chat_id, message_id=message_id)
        send(ADMIN_ID,
             f"📸 Чек от @{username} (ID: `{uid}`)\n"
             f"Тариф: {plan['emoji']} {plan['name']} — ${plan['price']}",
             {"inline_keyboard": [[
                 {"text": "✅ Подтвердить", "callback_data": f"confirm_{uid}_{plan_key}"},
                 {"text": "❌ Отклонить",   "callback_data": f"reject_{uid}"},
             ]]})
        send(chat_id, t("check_received", uid))
        return

    if step == "name":
        states[uid]["name"] = text
        states[uid]["step"] = "category"
        send(chat_id, f"✅ *{text}*\n\n{t('choose_category', uid)}", kb_categories(uid))

    elif step == "desc":
        n   = st.get("name", "Бизнес")
        cat = st.get("category", "📦")
        cat_ru = st.get("category_ru", cat)
        cat_key = st.get("cat_key", "cat_other")
        db[uid] = {
            "name": n, "category": cat, "category_ru": cat_ru,
            "cat_key": cat_key, "description": text,
            "plan": "free",
            "stats": {"today":0,"total":0,"users":0,"orders":0},
        }
        states.pop(uid, None)
        # Уведомляем админа на русском
        send(ADMIN_ID,
             f"🆕 *Новый бизнес!*\n\n"
             f"👤 @{username}\n🏢 {n}\n📂 {cat_ru}\n"
             f"🌍 {LANGS.get(user_lang.get(uid,'ru'),'?')}")
        send(chat_id, t("registered_ok", uid, name=n), kb_dashboard(uid))

    elif step == "edit_req":
        states.pop(uid, None)
        biz_name = db[uid]["name"] if uid in db else "Unknown"
        # Уведомляем админа на русском
        send(ADMIN_ID,
             f"✏️ *Запрос правок*\n\n"
             f"👤 @{username}\n🏢 {biz_name}\n\n📝 {text}")
        send(chat_id, t("edit_accepted", uid), kb_back(uid, "dashboard"))

    elif step in ("s_desc","s_hours","s_menu"):
        states.pop(uid, None)
        send(chat_id, t("saved", uid), kb_back(uid, "settings"))

    else:
        if uid in db:
            send(chat_id, text_dashboard(uid), kb_dashboard(uid))
        else:
            send(chat_id, t("welcome", uid, name=name), kb_start(uid))

# ── Vercel handler ────────────────────────────────────────────────────────────

class handler(BaseHTTPRequestHandler):

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body   = json.loads(self.rfile.read(length))
        try:
            if "callback_query" in body:
                cq       = body["callback_query"]
                uid      = cq["from"]["id"]
                username = cq["from"].get("username", "unknown")
                name     = cq["from"].get("first_name", "")
                cid      = cq["message"]["chat"]["id"]
                mid      = cq["message"]["message_id"]
                on_callback(uid, cid, mid, cq["data"], cq["id"], username, name)
            elif "message" in body:
                msg      = body["message"]
                uid      = msg["from"]["id"]
                cid      = msg["chat"]["id"]
                text     = msg.get("text", "")
                username = msg["from"].get("username", "unknown")
                name     = msg["from"].get("first_name", "друг")
                mid      = msg["message_id"]
                msg_type = "photo" if "photo" in msg else "text"
                if text.startswith("/start"):
                    on_start(uid, name, cid)
                else:
                    on_message(uid, cid, text, username, mid, msg_type, name)
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
