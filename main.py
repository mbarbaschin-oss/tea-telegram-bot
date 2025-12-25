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

ORDER_URL = "https://t.me/moontea48tg"  # замени на свой ник

# ===== БАЗА ЧАЁВ =====
TEAS = [
    {"name_ru":"Шен пуэр 2023, Линцан","year":2023,"name_cn":{"chars":"生普洱（临沧）","pinyin":"Shēng Pǔ'ěr (Líncāng)"},"times":["morning","day"],"states":["tired","focus"],"exp":["regular"],"taste":"bitter","desc":"Шен пуэр, бодрит и даёт структуру."},
    {"name_ru":"Шен пуэр Биндао, древние деревья","year":None,"name_cn":{"chars":"冰岛古树普洱","pinyin":"Bīngdǎo gǔshù Pǔ'ěr"},"times":["morning"],"states":["tired"],"exp":["expert"],"taste":"bitter","desc":"Интересный шен пуэр из Биндао."},
    {"name_ru":"Шен пуэр Бо Хэ Тан","year":None,"name_cn":{"chars":"(транслит)","pinyin":"Bo He Tan"},"times":["day"],"states":["focus"],"exp":["regular","expert"],"taste":"bitter","desc":"Чай для концентрации и бодрости."},
    {"name_ru":"Шу пуэр 7592, Menghai","year":None,"name_cn":{"chars":"勐海 7592 熟普洱","pinyin":"Měnghǎi 7592 Shú Pǔ'ěr"},"times":["evening"],"states":["calm"],"exp":["rare","regular","expert"],"taste":"dense","desc":"Тёплый, мягкий, подходит для вечера."},
    {"name_ru":"Шу пуэр Brown Peacock","year":None,"name_cn":{"chars":"(транслит)","pinyin":"Brown Peacock"},"times":["evening"],"states":["calm"],"exp":["rare","regular","expert"],"taste":"dense","desc":"Мягкий, сладковатый шэн/шу профиль."},
    {"name_ru":"Да Хун Пао","year":None,"name_cn":{"chars":"大红袍","pinyin":"Dà Hóng Páo"},"times":["day"],"states":["focus","no_task"],"exp":["regular","expert"],"taste":"dense","desc":"Классический уишанский улун, плотный и многогранный."},
    {"name_ru":"ГАББА Да Хун Пао, Уишань","year":None,"name_cn":{"chars":"GABA 大红袍","pinyin":"GABA Dà Hóng Páo"},"times":["day"],"states":["focus"],"exp":["regular","expert"],"taste":"dense","desc":"GABA-обработка делает вкус мягче, но плотным."},
    {"name_ru":"ГАББА улун Чёрный жемчуг","year":None,"name_cn":{"chars":"GABA 乌龙·黑珍珠","pinyin":"GABA Hēi Zhēnzhū"},"times":["day","evening"],"states":["no_task"],"exp":["rare","regular","expert"],"taste":"soft","desc":"Лёгкий улун, мягкий послевкусие."},
    {"name_ru":"ГАББА улун Дикий мёд","year":None,"name_cn":{"chars":"GABA 乌龙·野蜜","pinyin":"GABA Yěmì"},"times":["day"],"states":["no_task"],"exp":["regular","expert"],"taste":"dense","desc":"Сладковатый, насыщенный улун."},
    {"name_ru":"Лунцзин","year":None,"name_cn":{"chars":"龙井","pinyin":"Lóngjǐng"},"times":["morning"],"states":["tired"],"exp":["rare","regular"],"taste":"soft","desc":"Свежий и лёгкий, хорош для утра."},
    {"name_ru":"Шугэнди","year":None,"name_cn":{"chars":"(транслит)","pinyin":"Shugendi"},"times":["morning"],"states":["tired"],"exp":["rare"],"taste":"soft","desc":"Нежный утренний чай."},
    {"name_ru":"Бай Хао Инь Чжень","year":None,"name_cn":{"chars":"白毫银针","pinyin":"Bái Háo Yín Zhēn"},"times":["morning","day","evening"],"states":["no_task"],"exp":["rare","regular","expert"],"taste":"soft","desc":"Белый чай, деликатный, универсальный."}
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
    caption = f"{tea['name_ru']}\n{tea.get('desc','')}"
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
    chat = update.effective_chat.id
    USERS[chat] = {"time": None, "state": None, "experience": None, "taste": None, "shown": []}

   text = (
    "Подберу чай под твоё состояние.\n"
    "Ответь на несколько вопросов.\n\n"
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
        await query.answer()
        chat = query.message.chat.id
        user = get_user(chat)
        data = query.data

        if data.startswith("time_"):
            user["time"] = data.split("_",1)[1]
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("Собраться и сфокусироваться", callback_data="state_focus")],
                [InlineKeyboardButton("Расслабиться", callback_data="state_relax")],
                [InlineKeyboardButton("Просто для удовольствия", callback_data="state_easy")]
            ])
            await send_text(update, "Какое состояние ты хочешь получить от чая?", keyboard, edit=True)
            return

        if data.startswith("state_"):
            user["state"] = data.split("_",1)[1]
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("Только начинаю", callback_data="exp_beginner")],
                [InlineKeyboardButton("Иногда пью", callback_data="exp_middle")],
                [InlineKeyboardButton("Хорошо разбираюсь", callback_data="exp_advanced")]
            ])
            await send_text(update, "Какой у тебя опыт с китайским чаем?", keyboard, edit=True)
            return

        if data.startswith("exp_"):
            user["experience"] = data.split("_",1)[1]
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("Лёгкий и свежий", callback_data="taste_light")],
                [InlineKeyboardButton("Насыщенный и глубокий", callback_data="taste_deep")],
                [InlineKeyboardButton("Не знаю, доверюсь подбору", callback_data="taste_any")]
            ])
            await send_text(update, "Что тебе ближе по вкусу?", keyboard, edit=True)
            return

        if data.startswith("taste_"):
            user["taste"] = data.split("_",1)[1]
            tea = pick_tea(user)
            # кнопки результата
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("Попробовать другое", callback_data="another")],
                [InlineKeyboardButton("Написать для заказа", url=ORDER_URL)]
            ])
            # отправляем с фото если есть (в базе можно добавить поле image: "https://...")
            await send_tea_with_photo(update, context, tea, keyboard, edit=True)
            return

        if data == "another":
            # показать другой чай по той же логике - просто повторно вызываем pick_tea
            tea = pick_tea(user)
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("Попробовать другое", callback_data="another")],
                [InlineKeyboardButton("Написать для заказа", url=ORDER_URL)]
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
