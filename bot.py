import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from datetime import datetime
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
MINI_APP_URL = os.environ.get("MINI_APP_URL", "https://your-miniapp-url.vercel.app")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))

# Простая in-memory база (потом заменим на реальную БД)
businesses = {}  # {user_id: {name, category, bot_token, stats, plan}}

PLANS = {
    "free": {"name": "🆓 Free", "price": 0, "limit": 100},
    "starter": {"name": "⚡ Starter", "price": 29, "limit": 1000},
    "pro": {"name": "🚀 Pro", "price": 79, "limit": 10000},
}

# ─── ГЛАВНОЕ МЕНЮ ───────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = user.id

    if uid in businesses:
        await show_dashboard(update, context)
        return

    keyboard = [
        [InlineKeyboardButton("🚀 Создать AI-бота для бизнеса", callback_data="register")],
        [InlineKeyboardButton("📖 Как это работает?", callback_data="how_it_works")],
        [InlineKeyboardButton("💰 Тарифы", callback_data="plans")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"👋 Привет, {user.first_name}!\n\n"
        f"*Zevo* — платформа для создания AI-ботов для вашего бизнеса.\n\n"
        f"✅ Бот отвечает клиентам 24/7\n"
        f"✅ Принимает заказы и вопросы\n"
        f"✅ Статистика в реальном времени\n"
        f"✅ Настройка без кода\n\n"
        f"Тысячи кафе, магазинов и салонов уже используют Zevo 🔥",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

async def how_it_works(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [[InlineKeyboardButton("🚀 Начать", callback_data="register"),
                 InlineKeyboardButton("◀️ Назад", callback_data="back_start")]]
    await query.edit_message_text(
        "📖 *Как работает Zevo?*\n\n"
        "1️⃣ Регистрируете свой бизнес\n"
        "2️⃣ Настраиваете бота под себя\n"
        "3️⃣ Даёте ссылку клиентам\n"
        "4️⃣ Бот работает сам — отвечает, принимает заказы\n"
        "5️⃣ Вы видите всю статистику здесь\n\n"
        "⏱ Настройка занимает *5 минут*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_plans(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [[InlineKeyboardButton("🚀 Начать бесплатно", callback_data="register")],
                [InlineKeyboardButton("◀️ Назад", callback_data="back_start")]]
    await query.edit_message_text(
        "💰 *Тарифы Zevo*\n\n"
        "🆓 *Free* — $0/мес\n"
        "• До 100 сообщений/мес\n"
        "• 1 бот\n\n"
        "⚡ *Starter* — $29/мес\n"
        "• До 1,000 сообщений/мес\n"
        "• 3 бота\n"
        "• Статистика\n\n"
        "🚀 *Pro* — $79/мес\n"
        "• До 10,000 сообщений/мес\n"
        "• Неограниченно ботов\n"
        "• Приоритетная поддержка\n"
        "• Кастомный AI",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ─── РЕГИСТРАЦИЯ БИЗНЕСА ─────────────────────────────────────

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["state"] = "awaiting_business_name"
    keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="back_start")]]
    await query.edit_message_text(
        "🏢 *Регистрация бизнеса*\n\n"
        "Как называется ваш бизнес?\n\n"
        "_Например: Кафе Уют, Салон красоты Лиза, Магазин TechStore_",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    state = context.user_data.get("state")
    text = update.message.text

    if state == "awaiting_business_name":
        context.user_data["business_name"] = text
        context.user_data["state"] = "awaiting_category"
        keyboard = [
            [InlineKeyboardButton("🍕 Кафе/Ресторан", callback_data="cat_cafe"),
             InlineKeyboardButton("💇 Салон красоты", callback_data="cat_salon")],
            [InlineKeyboardButton("🛍 Магазин", callback_data="cat_shop"),
             InlineKeyboardButton("🏋️ Фитнес/Спорт", callback_data="cat_fitness")],
            [InlineKeyboardButton("🏥 Медицина", callback_data="cat_medical"),
             InlineKeyboardButton("📦 Другое", callback_data="cat_other")],
        ]
        await update.message.reply_text(
            f"✅ Отлично! *{text}*\n\nВыберите категорию вашего бизнеса:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif state == "awaiting_description":
        context.user_data["description"] = text
        await finish_registration(update, context)

async def select_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cat_map = {
        "cat_cafe": "🍕 Кафе/Ресторан",
        "cat_salon": "💇 Салон красоты",
        "cat_shop": "🛍 Магазин",
        "cat_fitness": "🏋️ Фитнес/Спорт",
        "cat_medical": "🏥 Медицина",
        "cat_other": "📦 Другое",
    }
    context.user_data["category"] = cat_map[query.data]
    context.user_data["state"] = "awaiting_description"
    await query.edit_message_text(
        f"*{cat_map[query.data]}* — хороший выбор!\n\n"
        "Опишите ваш бизнес в 2–3 предложениях.\n\n"
        "_Это поможет AI лучше отвечать вашим клиентам._",
        parse_mode="Markdown"
    )

async def finish_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    name = context.user_data.get("business_name", "Мой бизнес")
    category = context.user_data.get("category", "📦 Другое")
    description = context.user_data.get("description", "")

    businesses[uid] = {
        "name": name,
        "category": category,
        "description": description,
        "plan": "free",
        "created_at": datetime.now().isoformat(),
        "stats": {
            "total_messages": 0,
            "today_messages": 0,
            "total_users": 0,
            "orders": 0,
        }
    }
    context.user_data["state"] = None

    await update.message.reply_text(
        f"🎉 *Бизнес зарегистрирован!*\n\n"
        f"🏢 {name}\n"
        f"📂 {category}\n\n"
        f"Ваш AI-бот готов к настройке!",
        parse_mode="Markdown"
    )
    await show_dashboard_message(update, context, uid)

# ─── ДАШБОРД ─────────────────────────────────────────────────

async def show_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    await show_dashboard_message(update, context, uid)

async def show_dashboard_message(update, context, uid):
    biz = businesses.get(uid)
    if not biz:
        return

    stats = biz["stats"]
    plan = PLANS[biz["plan"]]

    keyboard = [
        [InlineKeyboardButton("📊 Статистика", callback_data="stats"),
         InlineKeyboardButton("⚙️ Настройки бота", callback_data="settings")],
        [InlineKeyboardButton("✏️ Заказать правки", callback_data="request_edit"),
         InlineKeyboardButton("💰 Тариф", callback_data="my_plan")],
        [InlineKeyboardButton("🔗 Ссылка на моего бота", callback_data="my_bot_link")],
        [InlineKeyboardButton("📱 Открыть панель управления", web_app=WebAppInfo(url=MINI_APP_URL))],
    ]

    text = (
        f"🏢 *{biz['name']}*\n"
        f"📂 {biz['category']} | {plan['name']}\n\n"
        f"📈 *Статистика сегодня:*\n"
        f"💬 Сообщений: {stats['today_messages']}\n"
        f"👥 Пользователей: {stats['total_users']}\n"
        f"🛒 Заказов: {stats['orders']}\n\n"
        f"За всё время: {stats['total_messages']} сообщений"
    )

    if hasattr(update, 'message') and update.message:
        await update.message.reply_text(text, parse_mode="Markdown",
                                         reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.callback_query.edit_message_text(text, parse_mode="Markdown",
                                                       reply_markup=InlineKeyboardMarkup(keyboard))

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    biz = businesses.get(uid)
    if not biz:
        return
    stats = biz["stats"]
    keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="dashboard")]]
    await query.edit_message_text(
        f"📊 *Статистика — {biz['name']}*\n\n"
        f"📅 Сегодня:\n"
        f"  💬 Сообщений: {stats['today_messages']}\n"
        f"  👥 Новых пользователей: 0\n\n"
        f"📆 За всё время:\n"
        f"  💬 Сообщений: {stats['total_messages']}\n"
        f"  👥 Всего пользователей: {stats['total_users']}\n"
        f"  🛒 Заказов: {stats['orders']}\n\n"
        f"_Статистика обновляется в реальном времени_",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    biz = businesses.get(uid)
    keyboard = [
        [InlineKeyboardButton("✏️ Изменить описание", callback_data="edit_description")],
        [InlineKeyboardButton("🕐 Часы работы", callback_data="edit_hours")],
        [InlineKeyboardButton("📋 Меню/Услуги", callback_data="edit_menu")],
        [InlineKeyboardButton("◀️ Назад", callback_data="dashboard")],
    ]
    await query.edit_message_text(
        f"⚙️ *Настройки бота — {biz['name']}*\n\n"
        f"Что хотите настроить?",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def request_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["state"] = "awaiting_edit_request"
    keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="dashboard")]]
    await query.edit_message_text(
        "✏️ *Заказать правки*\n\n"
        "Опишите что нужно изменить в вашем боте.\n\n"
        "_Например: добавить новые блюда в меню, изменить часы работы, добавить кнопку записи_",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def my_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    biz = businesses.get(uid)
    plan = PLANS[biz["plan"]]
    keyboard = [
        [InlineKeyboardButton("⚡ Upgrade на Starter — $29", callback_data="upgrade_starter")],
        [InlineKeyboardButton("🚀 Upgrade на Pro — $79", callback_data="upgrade_pro")],
        [InlineKeyboardButton("◀️ Назад", callback_data="dashboard")],
    ]
    await query.edit_message_text(
        f"💰 *Ваш тариф: {plan['name']}*\n\n"
        f"Лимит сообщений: {plan['limit']}/мес\n\n"
        f"Upgrade для снятия ограничений 👇",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def back_to_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    if uid in businesses:
        await show_dashboard_message(update, context, uid)
    else:
        await back_to_start(update, context)

async def back_to_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("🚀 Создать AI-бота для бизнеса", callback_data="register")],
        [InlineKeyboardButton("📖 Как это работает?", callback_data="how_it_works")],
        [InlineKeyboardButton("💰 Тарифы", callback_data="plans")],
    ]
    await query.edit_message_text(
        "👋 Добро пожаловать в *Zevo*!\n\n"
        "✅ Бот отвечает клиентам 24/7\n"
        "✅ Принимает заказы и вопросы\n"
        "✅ Статистика в реальном времени\n"
        "✅ Настройка без кода",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ─── ЗАПУСК ───────────────────────────────────────────────────

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("dashboard", show_dashboard))

    app.add_handler(CallbackQueryHandler(how_it_works, pattern="^how_it_works$"))
    app.add_handler(CallbackQueryHandler(show_plans, pattern="^plans$"))
    app.add_handler(CallbackQueryHandler(register, pattern="^register$"))
    app.add_handler(CallbackQueryHandler(select_category, pattern="^cat_"))
    app.add_handler(CallbackQueryHandler(show_stats, pattern="^stats$"))
    app.add_handler(CallbackQueryHandler(show_settings, pattern="^settings$"))
    app.add_handler(CallbackQueryHandler(request_edit, pattern="^request_edit$"))
    app.add_handler(CallbackQueryHandler(my_plan, pattern="^my_plan$"))
    app.add_handler(CallbackQueryHandler(back_to_dashboard, pattern="^dashboard$"))
    app.add_handler(CallbackQueryHandler(back_to_start, pattern="^back_start$"))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🚀 Zevo Bot запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
