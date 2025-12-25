# main.py
import os
import logging
from typing import Optional
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

# ===== Настройка логов =====
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ===== Конфигурация =====
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    logger.error("BOT_TOKEN не задан. Установи переменную окружения BOT_TOKEN.")
    raise SystemExit("BOT_TOKEN не задан")

CHANNEL_USERNAME = "@MoonTea48"

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
        "desc": "Даёт ясную бодрость, хорошо собирает внимание и не перегружает. Подходит для утра и первой половины дня, особенно когда нужно включиться в работу."
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
        "desc": "Глубокий, плотный и требовательный чай. Лучше подойдёт тем, кто уже знаком с пуэрами и любит выраженный характер."
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
        "desc": "Хорош для дневного чаепития, когда нужна собранность без резкой стимуляции. Вкус плотный, с характерной шеновой горчинкой."
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
        "desc": "Мягко согревает, расслабляет и создаёт ощущение устойчивости. Отличный вариант для вечера или спокойного завершения дня."
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
        "desc": "Подходит для вечернего чаепития и расслабленного состояния. Хороший вариант, если хочется тепла и комфорта."
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
        "desc": "Плотный, многослойный вкус, хорошо держит внимание. Подходит для дневного чаепития и вдумчивого состояния."
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
        "desc": "Сохраняет глубину вкуса, но действует мягче и спокойнее. Подходит для концентрации без напряжения."
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
        "desc": "Хорош для неспешного чаепития без конкретной задачи. Лёгкий, комфортный и ненавязчивый."
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
        "desc": "Свежий, лёгкий и понятный по вкусу. Хорош для утра и для тех, кто только начинает знакомство с китайским чаем."
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
        "desc": "Подходит для утреннего чаепития и спокойного начала дня. Хороший вариант для новичков."
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
        "desc": "Очень деликатный, спокойный и чистый по вкусу. Подходит для любого времени дня, когда не хочется перегрузки."
    }
]


# ===== Простая in-memory память (на будущее можно заменить DB) =====
USERS = {}  # chat_id -> {time,state,experience,taste,shown:[]}

# ===== Вспомогательные функции =====
EXP_ORDER = {"rare": 0, "regular": 1, "expert": 2}
TASTE_ORDER = {"soft": 0, "dense": 1, "bitter": 2}

def get_user(chat_id: int):
    if chat_id not in USERS:
        USERS[chat_id] = {"time": None, "state": None, "experience": None, "taste": None, "shown": []}
    return USERS[chat_id]

def deterministic_sort_key(t):
    exp_rank = min((EXP_ORDER.get(e, 99) for e in t.get("exp", [])), default=99)
    taste_rank = TASTE_ORDER.get(t.get("taste","soft"), 9)
    base_index = TEAS.index(t)
    return (exp_rank, taste_rank, base_index)

def pick_tea(user: dict):
    # helpers
    def unseen(ts):
        return [t for t in ts if t["name_ru"] not in user.get("shown", [])]

    def strict_pred(t):
        return (user["time"] in t["times"]) and (user["state"] in t["states"]) and (user["experience"] in t["exp"])

    # 1. strict filter
    candidates = unseen([t for t in TEAS if strict_pred(t)])

    # 2. prefer taste if possible
    if candidates:
        taste_pref = user.get("taste")
        if taste_pref:
            taste_match = [t for t in candidates if t.get("taste") == taste_pref]
            if taste_match:
                candidates = taste_match

    # choose deterministically
    if candidates:
        chosen = sorted(candidates, key=deterministic_sort_key)[0]
        user.setdefault("shown", []).append(chosen["name_ru"])
        return chosen

    # 3. progressive relaxations
    # a) expand experience upward
    levels = ["rare","regular","expert"]
    if user.get("experience") in levels:
        start_idx = levels.index(user["experience"])
        for idx in range(start_idx+1, len(levels)):
            exp_allowed = levels[idx]
            c = unseen([t for t in TEAS if (user["time"] in t["times"]) and (user["state"] in t["states"]) and (exp_allowed in t["exp"])])
            if c:
                chosen = sorted(c, key=deterministic_sort_key)[0]
                user.setdefault("shown", []).append(chosen["name_ru"])
                return chosen

    # b) allow any experience for same time/state
    c = unseen([t for t in TEAS if (user["time"] in t["times"]) and (user["state"] in t["states"])])
    if c:
        chosen = sorted(c, key=deterministic_sort_key)[0]
        user.setdefault("shown", []).append(chosen["name_ru"])
        return chosen

    # c) allow any state, same time
    c = unseen([t for t in TEAS if (user["time"] in t["times"])])
    if c:
        chosen = sorted(c, key=deterministic_sort_key)[0]
        user.setdefault("shown", []).append(chosen["name_ru"])
        return chosen

    # d) allow any time/state (unseen)
    c = unseen(TEAS)
    if c:
        chosen = sorted(c, key=deterministic_sort_key)[0]
        user.setdefault("shown", []).append(chosen["name_ru"])
        return chosen

    # e) fallback: first tea (if even unseen exhausted)
    chosen = TEAS[0]
    user.setdefault("shown", []).append(chosen["name_ru"])
    return chosen

# ===== Проверка подписки на канал =====
async def is_subscribed(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ("member", "administrator", "creator")
    except Exception:
        return False

# ===== Универсальные отправки (защищают от NoneType) =====
async def send_text(update: Update, text: str, keyboard: Optional[InlineKeyboardMarkup]=None, edit: bool=False):
    try:
        if update.message:
            await update.message.reply_text(text, reply_markup=keyboard)
        elif update.callback_query:
            msg = update.callback_query.message
            if edit:
                await msg.edit_text(text, reply_markup=keyboard)
            else:
                await msg.reply_text(text, reply_markup=keyboard)
        else:
            # редкий случай: используем context.bot
            await update.get_bot().send_message(chat_id=update.effective_chat.id, text=text, reply_markup=keyboard)
    except Exception as e:
        logger.exception("send_text error: %s", e)

async def send_tea_with_photo(update: Update, context: ContextTypes.DEFAULT_TYPE, tea: dict, keyboard: Optional[InlineKeyboardMarkup]=None, edit: bool=False):
    caption = f"{tea['name_ru']}\n\n{tea.get('desc','')}"
    # try to send image by URL if exists in tea record, otherwise fallback to text
    image = tea.get("image")  # optional field in TEAS, could be URL
    try:
        chat_id = None
        if update.callback_query:
            chat_id = update.callback_query.message.chat.id
        elif update.message:
            chat_id = update.message.chat.id
        else:
            chat_id = update.effective_chat.id

        if image:
            # async send_photo via context.bot
            await context.bot.send_photo(chat_id=chat_id, photo=image, caption=caption, reply_markup=keyboard)
        else:
            # no image - use text
            if edit and update.callback_query:
                await update.callback_query.message.edit_text(caption, reply_markup=keyboard)
            else:
                await context.bot.send_message(chat_id=chat_id, text=caption, reply_markup=keyboard)
    except Exception as e:
        logger.exception("send_tea_with_photo error: %s", e)
        # fallback to simple text
        await send_text(update, caption, keyboard, edit=edit)

# ===== Хэндлеры =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # проверяем подписку
    user_id = update.effective_user.id
    if not await is_subscribed(context, user_id):
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Подписаться на канал", url=f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}")],
            [InlineKeyboardButton("Я подписался, проверить", callback_data="check_sub")]
        ])
        await send_text(update, "Чтобы пройти подбор чая, подпишись на канал.", keyboard)
        return

    chat = update.effective_chat.id
    USERS[chat] = {
        "time": None,
        "state": None,
        "experience": None,
        "taste": None,
        "shown": []
    }

    text = (
        "Я помогу индивидуально подобрать чай.\n"
        "Ответьте на несколько простых вопросов — в конце предложу конкретный чай из моего ассортимента.\n\n"
        "В какое время дня ты хочешь пить чай?"
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Утро", callback_data="time_morning")],
        [InlineKeyboardButton("День", callback_data="time_day")],
        [InlineKeyboardButton("Вечер", callback_data="time_evening")]
    ])

    await send_text(update, text, keyboard)


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        if not query:
            # защита - если это текст или что-то ещё, игнорируем
            return

        # кнопка проверки подписки
        if query.data == "check_sub":
            user_id = query.from_user.id
            if await is_subscribed(context, user_id):
                # запускаем старт заново для этого пользователя
                await start(update, context)
            else:
                await query.answer("Подписка не найдена", show_alert=True)
            return

        await query.answer()
        chat = query.message.chat.id
        user = get_user(chat)
        data = query.data

        if data.startswith("time_"):
            user["time"] = data.split("_",1)[1]
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("Собраться и сфокусироваться", callback_data="state_focus")],
                [InlineKeyboardButton("Расслабиться", callback_data="state_relax")],
                [InlineKeyboardButton("Просто пить без задачи", callback_data="state_no_task")]
            ])
            await send_text(update, "Какое состояние ты хочешь получить от чая?", keyboard, edit=True)
            return

        if data.startswith("state_"):
            user["state"] = data.split("_",1)[1]
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("Только перестал пить чай с сахаром", callback_data="exp_rare")],
                [InlineKeyboardButton("Уже не пью чай в пакетиках", callback_data="exp_regular")],
                [InlineKeyboardButton("Хорошо разбираюсь", callback_data="exp_expert")]
            ])
            await send_text(update, "Насколько ты знаком с китайским чаем?", keyboard, edit=True)
            return

        if data.startswith("exp_"):
            user["experience"] = data.split("_",1)[1]
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("Лёгкое и свежее", callback_data="taste_soft")],
                [InlineKeyboardButton("Насыщенное и глубокое", callback_data="taste_dense")],
                [InlineKeyboardButton("Не знаю, доверюсь подбору", callback_data="taste_any")]
            ])
            await send_text(update, "По вкусу тебе сейчас ближе что-то…", keyboard, edit=True)
            return

        if data.startswith("taste_"):
            user["taste"] = data.split("_", 1)[1]
            tea = pick_tea(user)
            
            keyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton("Вот ещё вариант, который может подойти", callback_data="another")],
    [InlineKeyboardButton("Спросить про этот чай", url=tea.get("order_url"))]
])
            await send_tea_with_photo(update, context, tea, keyboard, edit=True)
            return

        if data == "another":
            tea = pick_tea(user)

            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("Вот ещё вариант, который может подойти", callback_data="another")],
                [InlineKeyboardButton("Спросить про этот чай", url=tea["order_url"])]
            ])

            await send_tea_with_photo(update, context, tea, keyboard, edit=True)
            return

        if data == "another":
    tea = pick_tea(user)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Вот ещё вариант, который может подойти", callback_data="another")],
        [InlineKeyboardButton("Спросить про этот чай", url=tea["order_url"])]
    ])

    await send_tea_with_photo(update, context, tea, keyboard, edit=True)
    return

        if data == "restart":
            await start(update, context)
            return

    except Exception as e:
        logger.exception("Error in handle: %s", e)
        # вежливое сообщение пользователю, без деталей
        try:
            await send_text(update, "Что-то пошло не так. Попробуй снова.", edit=True)
        except Exception:
            pass

# ===== Запуск приложения =====
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle))
    logger.info("Bot starting...")
    app.run_polling(allowed_updates=["message","callback_query"])

if __name__ == "__main__":
    main()
