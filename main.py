import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# ===== НАСТРОЙКИ =====
TOKEN = os.getenv(8396818379:AAFMD0H3-PofHRPNMxElKxsBChgPfDvGROg)
ORDER_URL = "https://t.me/@moontea48tg"  

# ===== БАЗА ЧАЁВ =====
TEAS = [
    {"name": "Шен пуэр 2023, Линцан", "times": ["morning","day"], "states": ["tired","focus"], "exp": ["regular","expert"], "taste": "bitter"},
    {"name": "Шен пуэр Бо Хэ Тан", "times": ["day"], "states": ["focus"], "exp": ["regular","expert"], "taste": "bitter"},
    {"name": "Шу пуэр 7592, Menghai", "times": ["evening"], "states": ["calm"], "exp": ["rare","regular","expert"], "taste": "dense"},
    {"name": "Шу пуэр Brown Peacock", "times": ["evening"], "states": ["calm"], "exp": ["rare","regular","expert"], "taste": "dense"},
    {"name": "Да Хун Пао", "times": ["day"], "states": ["focus","no_task"], "exp": ["regular","expert"], "taste": "dense"},
    {"name": "ГАББА Да Хун Пао, Уишань", "times": ["day"], "states": ["focus"], "exp": ["regular","expert"], "taste": "dense"},
    {"name": "ГАББА улун Чёрный жемчуг", "times": ["day","evening"], "states": ["no_task"], "exp": ["rare","regular","expert"], "taste": "soft"},
    {"name": "ГАББА улун Дикий мёд", "times": ["day"], "states": ["no_task"], "exp": ["regular","expert"], "taste": "dense"},
    {"name": "Лунцзин", "times": ["morning"], "states": ["tired"], "exp": ["rare","regular"], "taste": "soft"},
    {"name": "Шугэнди", "times": ["morning"], "states": ["tired"], "exp": ["rare"], "taste": "soft"},
    {"name": "Бай Хао Инь Чжень", "times": ["morning","day","evening"], "states": ["no_task"], "exp": ["rare","regular","expert"], "taste": "soft"}
]
# ===== ХРАНЕНИЕ СОСТОЯНИЯ (ПАМЯТЬ ПРОЦЕССА) =====
USERS = {}

# ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====
def get_user(chat_id):
    if chat_id not in USERS:
        USERS[chat_id] = {
            "time": None,
            "state": None,
            "exp": None,
            "taste": None,
            "shown": []
        }
    return USERS[chat_id]

def choose_tea(user):
    candidates = []
    for t in TEAS:
        if (
            user["time"] in t["times"] and
            user["state"] in t["states"] and
            user["exp"] in t["exp"] and
            t["name"] not in user["shown"]
        ):
            candidates.append(t)

    if not candidates:
        return None, False

    taste_match = [t for t in candidates if t["taste"] == user["taste"]]
    if taste_match:
        candidates = taste_match

    chosen = candidates[0]
    has_alt = len(candidates) > 1
    user["shown"].append(chosen["name"])
    return chosen, has_alt

def build_text(user, tea_name):
    if user["state"] == "focus":
        return f"{tea_name}\nПодходит для дневного времени и концентрации. Плотный характер."
    if user["state"] == "tired":
        return f"{tea_name}\nПодходит для утреннего времени и мягкого бодрствования."
    if user["state"] == "calm":
        return f"{tea_name}\nПодходит для вечера и спокойного состояния."
    return f"{tea_name}\nПросто вкусный чай без задачи."

# ===== ХЭНДЛЕРЫ =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat.id
    USERS[chat] = {"time": None, "state": None, "exp": None, "taste": None, "shown": []}

    keyboard = [
        [InlineKeyboardButton("утро", callback_data="time_morning")],
        [InlineKeyboardButton("день", callback_data="time_day")],
        [InlineKeyboardButton("вечер", callback_data="time_evening")]
    ]
    await update.message.reply_text(
        "Когда ты хочешь пить чай?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat = query.message.chat.id
    user = get_user(chat)
    data = query.data

    if data.startswith("time_"):
        user["time"] = data.split("_")[1]
        keyboard = [
            [InlineKeyboardButton("устал", callback_data="state_tired")],
            [InlineKeyboardButton("сосредоточиться", callback_data="state_focus")],
            [InlineKeyboardButton("спокойно", callback_data="state_calm")],
            [InlineKeyboardButton("без задачи", callback_data="state_no_task")]
        ]
        await query.edit_message_text(
            "Какое состояние ближе?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    if data.startswith("state_"):
        user["state"] = data.split("_")[1]
        keyboard = [
            [InlineKeyboardButton("пью редко", callback_data="exp_rare")],
            [InlineKeyboardButton("пью регулярно", callback_data="exp_regular")],
            [InlineKeyboardButton("разбираюсь", callback_data="exp_expert")]
        ]
        await query.edit_message_text(
            "Опыт с чаем?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    if data.startswith("exp_"):
        user["exp"] = data.split("_")[1]
        keyboard = [
            [InlineKeyboardButton("мягкий", callback_data="taste_soft")],
            [InlineKeyboardButton("плотный", callback_data="taste_dense")],
            [InlineKeyboardButton("терпкий", callback_data="taste_bitter")]
        ]
        await query.edit_message_text(
            "Какой вкус?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    if data.startswith("taste_"):
        user["taste"] = data.split("_")[1]

    if data == "another" or data.startswith("taste_"):
        tea, has_alt = choose_tea(user)

        if tea is None:
            await query.edit_message_text(
                "Подходящего чая не нашёл. Можно начать заново.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("начать заново", callback_data="restart")]
                ])
            )
            return

        buttons = [
            [InlineKeyboardButton("написать для заказа", url=ORDER_URL)]
        ]
        if has_alt:
            buttons.append([InlineKeyboardButton("попробовать другое", callback_data="another")])

        await query.edit_message_text(
            build_text(user, tea["name"]),
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return

    if data == "restart":
        USERS[chat] = {"time": None, "state": None, "exp": None, "taste": None, "shown": []}
        await start(update, context)

# ===== ЗАПУСК =====
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(handle))
app.run_polling()
