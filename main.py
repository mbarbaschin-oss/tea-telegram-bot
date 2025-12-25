import os
import logging
from typing import Optional
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

# ===== ЛОГИ =====
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===== КОНФИГ =====
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise SystemExit("BOT_TOKEN не задан")

CHANNEL_USERNAME = "@MoonTea48"
CAT_PHOTO_URL = "https://t.me/zapiskiychaynika/35?comment=32"

# ===== БАЗА ЧАЁВ =====
TEAS = [
    {
        "name_ru": "Шен пуэр 2023, Рассыпной, Юньнань",
        "year": 2023,
        "order_url": "https://t.me/m/0ytUIqIgNWE6",
        "name_cn": {"chars": "生普洱（临沧）", "pinyin": "Shēng Pǔ'ěr (Líncāng)"},
        "times": ["morning", "day"],
        "states": ["tired", "focus"],
        "exp": ["regular"],
        "taste": "bitter",
        "desc": "Даёт ясную бодрость, хорошо собирает внимание и не перегружает. Подходит для утра и первой половины дня."
    },
    {
        "name_ru": "Шен пуэр Биндао 2015, древние деревья",
        "year": 2015,
        "order_url": "https://t.me/m/kTVZxtvEMGFi",
        "name_cn": {"chars": "冰岛古树普洱", "pinyin": "Bīngdǎo gǔshù Pǔ'ěr"},
        "times": ["morning"],
        "states": ["tired"],
        "exp": ["expert"],
        "taste": "bitter",
        "desc": "Глубокий, плотный, интересный чай."
    },
    {
        "name_ru": "Шен пуэр Бо Хэ Тан",
        "year": 2017,
        "order_url": "https://t.me/m/hVeOrGytYmQy",
        "name_cn": {"chars": "(транслит)", "pinyin": "Bo He Tan"},
        "times": ["day"],
        "states": ["focus"],
        "exp": ["regular", "expert"],
        "taste": "bitter",
        "desc": "Хорош для дневной концентрации."
    },
    {
        "name_ru": "Шу пуэр 7592, Menghai",
        "year": 2019,
        "order_url": "https://t.me/m/luTjaZ5LOTcy",
        "name_cn": {"chars": "勐海 7592 熟普洱", "pinyin": "Měnghǎi 7592 Shú Pǔ'ěr"},
        "times": ["evening"],
        "states": ["calm"],
        "exp": ["rare", "regular", "expert"],
        "taste": "dense",
        "desc": "Мягко согревает и расслабляет."
    },
    {
        "name_ru": "Шу пуэр Brown Peacock",
        "year": 2008,
        "order_url": "https://t.me/m/EVBYr97CMGEy",
        "name_cn": {"chars": "(транслит)", "pinyin": "Brown Peacock"},
        "times": ["evening"],
        "states": ["calm"],
        "exp": ["rare", "regular", "expert"],
        "taste": "dense",
        "desc": "Комфортный вечерний шу."
    },
    {
        "name_ru": "Да Хун Пао",
        "year": 2025,
        "order_url": "https://t.me/m/swZVyMAFMTA6",
        "name_cn": {"chars": "大红袍", "pinyin": "Dà Hóng Páo"},
        "times": ["day"],
        "states": ["focus", "no_task"],
        "exp": ["regular", "expert"],
        "taste": "dense",
        "desc": "Плотный базовый уишаньский улун."
    },
    {
        "name_ru": "ГАББА Да Хун Пао, Уишань",
        "year": 2025,
        "order_url": "https://t.me/m/u0hTd7ESMDli",
        "name_cn": {"chars": "GABA 大红袍", "pinyin": "GABA Dà Hóng Páo"},
        "times": ["day"],
        "states": ["focus"],
        "exp": ["regular", "expert"],
        "taste": "dense",
        "desc": "Мягкая концентрация без перегруза."
    },
    {
        "name_ru": "ГАББА улун Чёрный жемчуг",
        "year": 2025,
        "order_url": "https://t.me/m/h7y1E7scYzAy",
        "name_cn": {"chars": "GABA 乌龙·黑珍珠", "pinyin": "GABA Hēi Zhēnzhū"},
        "times": ["day", "evening"],
        "states": ["no_task"],
        "exp": ["rare", "regular", "expert"],
        "taste": "soft",
        "desc": "Неспешный, комфортный улун."
    },
    {
        "name_ru": "Лунцзин",
        "year": 2025,
        "order_url": "https://t.me/m/wIx8_EZsOWU6",
        "name_cn": {"chars": "龙井", "pinyin": "Lóngjǐng"},
        "times": ["morning"],
        "states": ["tired"],
        "exp": ["rare", "regular"],
        "taste": "soft",
        "desc": "Лёгкий утренний зелёный."
    },
    {
        "name_ru": "Шугэнди",
        "year": 2025,
        "order_url": "https://t.me/m/LkPLv3d-ZDEy",
        "name_cn": {"chars": "(транслит)", "pinyin": "Shugendi"},
        "times": ["morning"],
        "states": ["tired"],
        "exp": ["rare"],
        "taste": "soft",
        "desc": "Спокойный старт дня."
    },
    {
        "name_ru": "Бай Хао Инь Чжень",
        "year": 2023,
        "order_url": "https://t.me/m/s87arDRuMDEy",
        "name_cn": {"chars": "白毫银针", "pinyin": "Bái Háo Yín Zhēn"},
        "times": ["morning", "day", "evening"],
        "states": ["no_task"],
        "exp": ["rare", "regular", "expert"],
        "taste": "soft",
        "desc": "Деликатный белый чай."
    }
]

# ===== ПАМЯТЬ =====
USERS = {}

EXP_ORDER = {"rare": 0, "regular": 1, "expert": 2}
TASTE_ORDER = {"soft": 0, "dense": 1, "bitter": 2}

def get_user(chat_id: int):
    if chat_id not in USERS:
        USERS[chat_id] = {
            "time": None,
            "state": None,
            "experience": None,
            "taste": None,
            "shown": []
        }
    return USERS[chat_id]

def deterministic_sort_key(t):
    exp_rank = min(EXP_ORDER.get(e, 99) for e in t.get("exp", []))
    taste_rank = TASTE_ORDER.get(t.get("taste", "soft"), 9)
    return (exp_rank, taste_rank, TEAS.index(t))

def pick_tea(user):
    def unseen(ts):
        return [t for t in ts if t["name_ru"] not in user["shown"]]

    candidates = unseen([
        t for t in TEAS
        if user["time"] in t["times"]
        and user["state"] in t["states"]
        and user["experience"] in t["exp"]
    ])

    if not candidates:
        candidates = unseen(TEAS)

    tea = sorted(candidates, key=deterministic_sort_key)[0]
    user["shown"].append(tea["name_ru"])
    return tea

async def is_subscribed(context, user_id):
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ("member", "administrator", "creator")
    except Exception:
        return False

async def send_text(update, text, keyboard=None, edit=False):
    if update.callback_query:
        msg = update.callback_query.message
        if edit:
            await msg.edit_text(text, reply_markup=keyboard)
        else:
            await msg.reply_text(text, reply_markup=keyboard)
    else:
        await update.message.reply_text(text, reply_markup=keyboard)

async def send_tea(update, context, tea, keyboard):
    text = f"{tea['name_ru']} ({tea['year']})\n\n{tea['desc']}"
    await send_text(update, text, keyboard, edit=True)

async def start(update, context):
    user_id = update.effective_user.id
    if not await is_subscribed(context, user_id):
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Подписаться", url="https://t.me/MoonTea48")],
            [InlineKeyboardButton("Я подписался", callback_data="check_sub")]
        ])
        await send_text(update, "Чтобы бот работал, нужно быть подписанным на канал.", keyboard)
        return

    USERS[update.effective_chat.id] = {
        "time": None,
        "state": None,
        "experience": None,
        "taste": None,
        "shown": []
    }

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Утро", callback_data="time_morning")],
        [InlineKeyboardButton("День", callback_data="time_day")],
        [InlineKeyboardButton("Вечер", callback_data="time_evening")]
    ])
    await update.message.reply_photo(
    photo=CAT_PHOTO_URL,
    caption="Привет. Давай подберем чай под твой день.\nСкажи, когда ты планируешь пить чай.",
    reply_markup=keyboard
)

async def handle(update, context):
    query = update.callback_query
    if not query:
        return

    await query.answer()
    chat = query.message.chat.id
    user = get_user(chat)
    data = query.data

    if data == "check_sub":
        await start(update, context)
        return

    if data.startswith("time_"):
        user["time"] = data.split("_")[1]
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Собраться и сфокусироваться", callback_data="state_focus")],
            [InlineKeyboardButton("Переключиться", callback_data="state_calm")],
            [InlineKeyboardButton("Просто без цели", callback_data="state_no_task")]
        ])
        await send_text(update, "Чего бы ты сейчас хотел?", keyboard, edit=True)
        return

    if data.startswith("state_"):
        user["state"] = data.split("_")[1]
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Я только начинаю", callback_data="exp_rare")],
            [InlineKeyboardButton("Пробовал разное", callback_data="exp_regular")],
            [InlineKeyboardButton("Хорошо разбираюсь", callback_data="exp_expert")]
        ])
        await send_text(update, "Твой опыт с чаем?", keyboard, edit=True)
        return

    if data.startswith("exp_"):
        user["experience"] = data.split("_")[1]
        tea = pick_tea(user)

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Попробовать другой", callback_data="another")],
            [InlineKeyboardButton("Узнать больше", url=tea["order_url"])]
        ])
        await send_tea(update, context, tea, keyboard)
        return

    if data == "another":
        tea = pick_tea(user)
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Попробовать другой", callback_data="another")],
            [InlineKeyboardButton("Узнать больше о чае и получить скидку 10%", url=tea["order_url"])]
        ])
        await send_tea(update, context, tea, keyboard)

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle))
    app.run_polling()

if __name__ == "__main__":
    main()

