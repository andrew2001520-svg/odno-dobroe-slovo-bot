import os, random, html, json, threading, time
from datetime import datetime
from urllib.parse import quote
import telebot
from telebot import types

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
bot = telebot.TeleBot(TOKEN)
ADMIN_ID = 5844296950
DONATE_URL = "https://pro.selfwork.ru/to/02197162"
SITE_URL = "https://odnodobroeslovo.ru"
SUBS_FILE = "daily_subscribers.json"
BANNERS_FILE = "banners.json"
USERS_FILE = "users.json"
PHRASES_FILE = "suggested_phrases.json"

QUOTES = [
"❤️ Ты справишься.", "🌿 Всё ещё впереди.", "❤️ Ты важен.",
"☀️ После трудных дней обязательно становится светлее.", "🌱 Не сдавайся. Иногда до перемен остаётся совсем немного.",
"❤️ Цени тех, кто рядом.", "✨ Жизнь продолжается.", "❤️ Ты сильнее, чем тебе кажется.",
"🌿 У тебя обязательно всё получится.", "☀️ Новый день — это новая возможность.", "❤️ Помни: ты не один.",
"🌱 Маленькие шаги тоже ведут к большим переменам.", "✨ Самое хорошее ещё может быть впереди.",
"❤️ Береги тех, кого любишь.", "🌿 Иногда достаточно просто продолжать идти.",
"☀️ Даже после самой долгой ночи наступает утро.", "❤️ Верь в себя немного сильнее.",
"🌱 Не бойся начинать сначала.", "✨ Твоя история ещё не закончена.", "❤️ Ты достоин хорошего.",
"🌿 Не забывай говорить близким, что любишь их.", "☀️ Сегодня может стать началом чего-то хорошего.",
"❤️ Один добрый поступок способен изменить чей-то день.", "❤️ Иногда человеку нужно всего одно доброе слово.",
"☀️ Свет обязательно найдёт дорогу.", "❤️ Будь рядом с теми, кто тебе дорог.",
"✨ Впереди ещё много поводов улыбнуться.", "🌿 Доброта всегда имеет значение.",
"☀️ Завтра может оказаться намного лучше.", "✨ Не переставай мечтать.", "❤️ Позвони тому, по кому скучаешь.",
"🌿 Обними тех, кто рядом.", "❤️ Твоё присутствие важно для кого-то.", "✨ Всё приходит в своё время.",
"❤️ Скажи сегодня кому-нибудь доброе слово.", "☀️ Начать заново — тоже смелость.",
"❤️ Ты заслуживаешь быть счастливым.", "❤️ Спасибо, что ты есть.", "✨ Ты уже прошёл многое. Продолжай.",
"❤️ Добро возвращается.", "☀️ Не теряй надежду.", "❤️ Люби. Живи. Цени.", "🌿 Не забывай отдыхать.",
"☀️ Солнце всё равно взойдёт.", "❤️ Ты кому-то очень дорог.", "🌿 Время с близкими бесценно.",
"☀️ Каждый рассвет — ещё один шанс.", "🌱 Ты не обязан решить всё сегодня.",
"✨ Иногда счастье находится совсем рядом.", "☀️ Верь, даже когда трудно.", "🌱 Продолжай верить в хорошее.",
"✨ У каждого тяжёлого периода есть конец.", "❤️ Береги любовь.", "🌱 Иногда медленно — это тоже движение вперёд.",
"❤️ Позвони родителям.", "☀️ После дождя снова появляется солнце.", "❤️ Будь причиной чьей-то улыбки.",
"🌿 Иногда самое ценное — просто быть рядом.", "✨ В мире всё ещё очень много добра.",
"❤️ Береги себя и своих близких.", "☀️ Хороший день ещё впереди.", "❤️ Слова имеют силу. Выбирай добрые.",
"❤️ Людям нужны люди.", "☀️ Не переставай замечать хорошее.", "🌱 Даже самый маленький прогресс имеет значение.",
"✨ Всё не зря.", "☀️ Дай завтрашнему дню шанс.", "🌱 Не бойся перемен.", "❤️ Добрые слова тоже меняют мир.",
"☀️ У тебя есть ещё время.", "🌱 Сделай ещё один шаг.", "✨ Впереди новая глава.", "🌱 Двигайся в своём темпе.",
"❤️ Цени жизнь.", "☀️ Не переставай искать свет.", "✨ Ещё будет много хорошего.", "❤️ Береги настоящее.",
"☀️ Всё постепенно наладится.", "✨ Сегодня — хороший день, чтобы начать.", "❤️ Жизнь ценна.",
"❤️ Ты нужен этому миру.", "✨ Хорошее обязательно случается."
]

def keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("❤️ Поддержать проект", "💬 Доброе слово")
    kb.row("🌅 Добро дня", "✍️ Предложить фразу")
    kb.row("📸 Наши баннеры", "🎯 Следующий баннер")
    kb.row("📊 Отчёты", "🗳 Выбрать фразу")
    kb.row("🌿 О проекте", "🌐 Наш сайт")
    return kb

def quote_buttons():
    kb = types.InlineKeyboardMarkup()
    kb.row(types.InlineKeyboardButton("❤️ Ещё одно", callback_data="more_quote"),
           types.InlineKeyboardButton("📤 Поделиться", callback_data="share_quote"))
    return kb

def load_subscribers():
    try:
        with open(SUBS_FILE, "r", encoding="utf-8") as f: return set(json.load(f))
    except Exception: return set()

def save_subscribers():
    try:
        with open(SUBS_FILE, "w", encoding="utf-8") as f: json.dump(list(subscribers), f)
    except Exception: pass

subscribers = load_subscribers()
waiting_for_phrase = set()

def load_json_list(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data=json.load(f)
            return data if isinstance(data,list) else []
    except Exception:
        return []

def save_json_list(path, data):
    try:
        with open(path,"w",encoding="utf-8") as f:
            json.dump(data,f,ensure_ascii=False,indent=2)
    except Exception:
        pass

users_data=load_json_list(USERS_FILE)
phrases_data=load_json_list(PHRASES_FILE)

def remember_user(message):
    if not message.from_user:
        return
    uid=message.from_user.id
    found=next((x for x in users_data if x.get("id")==uid),None)
    record={
        "id":uid,
        "chat_id":message.chat.id,
        "first_name":message.from_user.first_name or "",
        "username":message.from_user.username or "",
        "last_seen":datetime.utcnow().isoformat(timespec="seconds")
    }
    if found:
        found.update(record)
    else:
        users_data.append(record)
    save_json_list(USERS_FILE,users_data)

@bot.message_handler(commands=["start"])
def start(message):
    remember_user(message)
    bot.send_message(message.chat.id, "❤️ <b>Одно доброе слово</b>\n\nА что, если одна фраза сможет изменить чей-то день?\n\nМы размещаем на улицах баннеры с добрыми словами о надежде, любви, семье и ценности жизни.\n\nВыберите раздел 👇", parse_mode="HTML", reply_markup=keyboard())

@bot.message_handler(commands=["myid"])
def myid(message):
    bot.send_message(message.chat.id, f"Ваш Telegram ID: <code>{message.from_user.id}</code>", parse_mode="HTML")

# 1. Доброе слово + кнопка «Ещё одно»
@bot.message_handler(func=lambda m: m.text == "💬 Доброе слово")
def good_word(message):
    bot.send_message(message.chat.id, f"<b>{html.escape(random.choice(QUOTES))}</b>\n\nПусть эти слова сегодня будут именно для тебя. ❤️", parse_mode="HTML", reply_markup=quote_buttons())

@bot.callback_query_handler(func=lambda c: c.data == "more_quote")
def more_quote(c):
    bot.answer_callback_query(c.id)
    bot.edit_message_text(f"<b>{html.escape(random.choice(QUOTES))}</b>\n\nПусть эти слова сегодня будут именно для тебя. ❤️", c.message.chat.id, c.message.message_id, parse_mode="HTML", reply_markup=quote_buttons())

# 2. Добро дня
@bot.message_handler(func=lambda m: m.text == "🌅 Добро дня")
def daily_kindness(message):
    kb = types.InlineKeyboardMarkup()
    if message.chat.id in subscribers:
        kb.add(types.InlineKeyboardButton("🔕 Отключить", callback_data="daily_off")); text = "🌅 <b>Добро дня включено</b>\n\nВы подписаны на ежедневную добрую фразу ❤️"
    else:
        kb.add(types.InlineKeyboardButton("🔔 Включить", callback_data="daily_on")); text = "🌅 <b>Добро дня</b>\n\nПолучайте одну добрую фразу каждый день ❤️"
    bot.send_message(message.chat.id, text, parse_mode="HTML", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data in ("daily_on", "daily_off"))
def daily_toggle(c):
    if c.data == "daily_on": subscribers.add(c.message.chat.id); text = "❤️ «Добро дня» включено."
    else: subscribers.discard(c.message.chat.id); text = "🔕 «Добро дня» отключено."
    save_subscribers(); bot.answer_callback_query(c.id, text); bot.edit_message_text(text, c.message.chat.id, c.message.message_id)

# 3. Предложить фразу
@bot.message_handler(func=lambda m: m.text == "✍️ Предложить фразу")
def suggest_phrase(message):
    waiting_for_phrase.add(message.chat.id)
    bot.send_message(message.chat.id, "✍️ <b>Предложить свою фразу</b>\n\nНапишите одним сообщением фразу, которую вы хотели бы увидеть на улицах города ❤️\n\nОтмена: /cancel", parse_mode="HTML")

@bot.message_handler(commands=["cancel"])
def cancel(message):
    waiting_for_phrase.discard(message.chat.id); bot.send_message(message.chat.id, "Отменено ❤️", reply_markup=keyboard())

@bot.message_handler(func=lambda m: m.chat.id in waiting_for_phrase, content_types=["text"])
def receive_phrase(message):
    waiting_for_phrase.discard(message.chat.id); phrase = (message.text or "").strip()
    if not phrase or len(phrase) > 500:
        bot.send_message(message.chat.id, "Фраза не принята. Максимум 500 символов.", reply_markup=keyboard()); return
    u = message.from_user; username = "@" + u.username if u.username else "не указан"
    phrases_data.append({"text":phrase,"user_id":u.id,"username":u.username or "","name":u.first_name or "","status":"new","created":datetime.utcnow().isoformat(timespec="seconds")})
    save_json_list(PHRASES_FILE,phrases_data)
    bot.send_message(ADMIN_ID, "💌 <b>Новая предложенная фраза</b>\n\n" + f"«{html.escape(phrase)}»\n\n👤 {html.escape(u.first_name or 'Пользователь')}\n🔗 {html.escape(username)}\n🆔 <code>{u.id}</code>", parse_mode="HTML")
    bot.send_message(message.chat.id, "❤️ <b>Спасибо!</b> Ваша фраза принята. Возможно, однажды именно она появится на улицах города.", parse_mode="HTML", reply_markup=keyboard())

# 4. Поделиться добром
@bot.callback_query_handler(func=lambda c: c.data == "share_quote")
def share_quote(c):
    text = "Одно доброе слово ❤️\n\n" + random.choice(QUOTES)
    url = "https://t.me/share/url?url=" + quote(SITE_URL) + "&text=" + quote(text)
    kb = types.InlineKeyboardMarkup(); kb.add(types.InlineKeyboardButton("📤 Выбрать, кому отправить", url=url))
    bot.answer_callback_query(c.id); bot.send_message(c.message.chat.id, "Поделитесь добрым словом с близким ❤️", reply_markup=kb)

# 5. Наши баннеры
@bot.message_handler(func=lambda m: m.text == "📸 Наши баннеры")
def banners(message):
    show_banner(message.chat.id, 0)

# 6. Следующий баннер
@bot.message_handler(func=lambda m: m.text == "🎯 Следующий баннер")
def next_banner(message):
    kb = types.InlineKeyboardMarkup(); kb.add(types.InlineKeyboardButton("❤️ Помочь разместить", url=DONATE_URL)); kb.add(types.InlineKeyboardButton("🗳 Выбрать фразу", callback_data="open_vote"))
    bot.send_message(message.chat.id, "🎯 <b>Следующий баннер</b>\n\nМы готовим следующий уличный баннер проекта. Вы можете помочь с размещением или принять участие в выборе фразы ❤️", parse_mode="HTML", reply_markup=kb)

# 7. Отчёты
@bot.message_handler(func=lambda m: m.text == "📊 Отчёты")
def reports(message):
    bot.send_message(message.chat.id, "📊 <b>Отчёты проекта</b>\n\nЗдесь будут публиковаться поступления, расходы на печать, аренду и монтаж, чеки и фотографии размещённых баннеров.\n\n❤️ Мы за прозрачность проекта.", parse_mode="HTML")

# 8. Голосование
def send_vote(chat_id):
    bot.send_poll(chat_id, "Какую фразу вы хотели бы увидеть на улице?", ["❤️ Ты справишься", "🌿 Не сдавайся", "☀️ Всё ещё впереди", "❤️ Цени тех, кто рядом", "✨ Ты важен"], is_anonymous=True, allows_multiple_answers=False)

@bot.message_handler(func=lambda m: m.text == "🗳 Выбрать фразу")
def vote_phrase(message): send_vote(message.chat.id)

@bot.callback_query_handler(func=lambda c: c.data == "open_vote")
def open_vote(c): bot.answer_callback_query(c.id); send_vote(c.message.chat.id)

@bot.message_handler(func=lambda m: m.text == "❤️ Поддержать проект")
def donate(message):
    kb = types.InlineKeyboardMarkup(); kb.add(types.InlineKeyboardButton("❤️ Пожертвовать", url=DONATE_URL))
    bot.send_message(message.chat.id, "❤️ <b>Поддержать проект</b>\n\nВаш вклад помогает оплачивать печать, аренду рекламных конструкций, монтаж и размещение баннеров.\n\nНажмите кнопку ниже, чтобы поддержать проект ❤️", parse_mode="HTML", reply_markup=kb)

@bot.message_handler(func=lambda m: m.text == "🌿 О проекте")
def about(message):
    bot.send_message(message.chat.id, "🌿 <b>Одно доброе слово</b>\n\nМы размещаем на улицах слова, которые ничего не продают: поддержку, надежду, любовь и напоминание ценить тех, кто рядом.\n\nИногда одна фраза может встретить человека именно тогда, когда она ему особенно нужна. ❤️", parse_mode="HTML")

@bot.message_handler(func=lambda m: m.text == "🌐 Наш сайт")
def website(message):
    kb = types.InlineKeyboardMarkup(); kb.add(types.InlineKeyboardButton("🌐 Открыть сайт", url=SITE_URL)); bot.send_message(message.chat.id, "🌐 Сайт проекта «Одно доброе слово»", reply_markup=kb)

def daily_worker():
    last_date = None
    while True:
        now = datetime.utcnow()
        if now.hour == 6 and last_date != now.date():
            for chat_id in list(subscribers):
                try: bot.send_message(chat_id, "🌅 <b>Добро дня</b>\n\n" + html.escape(random.choice(QUOTES)), parse_mode="HTML")
                except Exception: pass
            last_date = now.date()
        time.sleep(60)

# 🔐 Админ-панель
admin_waiting_broadcast = set()
admin_banner_state = {}


def load_banners():
    try:
        with open(BANNERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_banners():
    try:
        with open(BANNERS_FILE, "w", encoding="utf-8") as f:
            json.dump(banners_data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


banners_data = load_banners()


def show_banner(chat_id, index=0):
    if not banners_data:
        bot.send_message(chat_id, "📸 <b>Наши баннеры</b>\n\nПока опубликованных баннеров нет. Скоро здесь появятся первые работы ❤️", parse_mode="HTML")
        return
    index = max(0, min(index, len(banners_data)-1))
    b = banners_data[index]
    caption = (
        f"📸 <b>{html.escape(b['phrase'])}</b>\n\n"
        f"📍 {html.escape(b['city'])}\n"
        f"📅 {html.escape(b['date'])}\n\n"
        f"Баннер {index+1} из {len(banners_data)} ❤️"
    )
    kb=types.InlineKeyboardMarkup()
    buttons=[]
    if index>0:
        buttons.append(types.InlineKeyboardButton("◀️ Назад", callback_data=f"banner_{index-1}"))
    if index<len(banners_data)-1:
        buttons.append(types.InlineKeyboardButton("Вперёд ▶️", callback_data=f"banner_{index+1}"))
    if buttons:
        kb.row(*buttons)
    bot.send_photo(chat_id, b["file_id"], caption=caption, parse_mode="HTML", reply_markup=kb)


@bot.callback_query_handler(func=lambda c:c.data.startswith("banner_"))
def banner_nav(c):
    bot.answer_callback_query(c.id)
    try:
        idx=int(c.data.split("_",1)[1])
        show_banner(c.message.chat.id, idx)
    except Exception:
        pass


def admin_menu():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("📊 Статистика", callback_data="admin_stats"),
        types.InlineKeyboardButton("📢 Рассылка", callback_data="admin_broadcast"),
        types.InlineKeyboardButton("🗳 Голосование", callback_data="admin_vote"),
        types.InlineKeyboardButton("💬 Добро дня", callback_data="admin_daily"),
        types.InlineKeyboardButton("📸 Баннеры", callback_data="admin_banners"),
        types.InlineKeyboardButton("✍️ Фразы", callback_data="admin_phrases"),
        types.InlineKeyboardButton("⚙️ Настройки", callback_data="admin_settings"),
        types.InlineKeyboardButton("❌ Закрыть", callback_data="admin_close"),
    )
    return kb


@bot.message_handler(commands=["admin"])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "⛔ Нет доступа.")
        return
    bot.send_message(message.chat.id, "🔐 <b>Админ-панель</b>\n\nВыберите действие:", parse_mode="HTML", reply_markup=admin_menu())


@bot.callback_query_handler(func=lambda c: c.data.startswith("admin_"))
def admin_actions(c):
    if c.from_user.id != ADMIN_ID:
        bot.answer_callback_query(c.id, "Нет доступа", show_alert=True)
        return
    bot.answer_callback_query(c.id)

    if c.data == "admin_stats":
        bot.send_message(c.message.chat.id, f"📊 <b>Статистика</b>\n\n👥 Пользователей: <b>{len(users_data)}</b>\n🌅 Подписчиков «Добра дня»: <b>{len(subscribers)}</b>\n✍️ Предложенных фраз: <b>{len(phrases_data)}</b>\n📸 Баннеров: <b>{len(banners_data)}</b>", parse_mode="HTML", reply_markup=admin_menu())

    elif c.data == "admin_broadcast":
        admin_waiting_broadcast.add(c.message.chat.id)
        bot.send_message(c.message.chat.id, "📢 Отправьте следующим сообщением текст рассылки подписчикам «Добра дня».\n\nОтмена: /cancelbroadcast")

    elif c.data == "admin_vote":
        send_vote(c.message.chat.id)

    elif c.data == "admin_daily":
        phrase = random.choice(QUOTES)
        sent = 0
        for chat_id in list(subscribers):
            try:
                bot.send_message(chat_id, "🌅 <b>Добро дня</b>\n\n" + html.escape(phrase), parse_mode="HTML")
                sent += 1
            except Exception:
                pass
        bot.send_message(c.message.chat.id, f"✅ Добро дня отправлено. Получателей: <b>{sent}</b>", parse_mode="HTML", reply_markup=admin_menu())

    elif c.data == "admin_banners":
        kb=types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("➕ Добавить баннер", callback_data="add_banner"))
        kb.add(types.InlineKeyboardButton("👁 Посмотреть опубликованные", callback_data="view_banners"))
        bot.send_message(c.message.chat.id, f"📸 <b>Управление баннерами</b>\n\nОпубликовано: <b>{len(banners_data)}</b>", parse_mode="HTML", reply_markup=kb)

    elif c.data == "admin_phrases":
        show_phrase_admin(c.message.chat.id, 0)

    elif c.data == "admin_settings":
        bot.send_message(c.message.chat.id, f"⚙️ <b>Настройки</b>\n\n🌐 Сайт: {SITE_URL}\n❤️ Пожертвования: {DONATE_URL}\n🌅 Добро дня: около 09:00 по Москве", parse_mode="HTML", reply_markup=admin_menu())

    elif c.data == "admin_close":
        bot.edit_message_text("🔒 Админ-панель закрыта.", c.message.chat.id, c.message.message_id)


def show_phrase_admin(chat_id,index=0):
    if not phrases_data:
        bot.send_message(chat_id,"✍️ Пока предложенных фраз нет.",reply_markup=admin_menu())
        return
    index=max(0,min(index,len(phrases_data)-1))
    p=phrases_data[index]
    status={"new":"🆕 Новая","approved":"✅ Одобрена","rejected":"❌ Отклонена"}.get(p.get("status"),p.get("status",""))
    text=(f"✍️ <b>Предложенная фраза</b>\n\n"
          f"«{html.escape(p.get('text',''))}»\n\n"
          f"👤 {html.escape(p.get('name') or 'Пользователь')}\n"
          f"📌 Статус: {status}\n"
          f"📄 {index+1} из {len(phrases_data)}")
    kb=types.InlineKeyboardMarkup()
    kb.row(types.InlineKeyboardButton("✅ Одобрить",callback_data=f"phrase_ok_{index}"),
           types.InlineKeyboardButton("❌ Отклонить",callback_data=f"phrase_no_{index}"))
    nav=[]
    if index>0: nav.append(types.InlineKeyboardButton("◀️",callback_data=f"phrase_view_{index-1}"))
    if index<len(phrases_data)-1: nav.append(types.InlineKeyboardButton("▶️",callback_data=f"phrase_view_{index+1}"))
    if nav: kb.row(*nav)
    bot.send_message(chat_id,text,parse_mode="HTML",reply_markup=kb)

@bot.callback_query_handler(func=lambda c:c.data.startswith(("phrase_ok_","phrase_no_","phrase_view_")))
def phrase_admin_callback(c):
    if c.from_user.id!=ADMIN_ID:
        bot.answer_callback_query(c.id,"Нет доступа",show_alert=True); return
    bot.answer_callback_query(c.id)
    try:
        idx=int(c.data.rsplit("_",1)[1])
        if c.data.startswith("phrase_ok_"):
            phrases_data[idx]["status"]="approved"; save_json_list(PHRASES_FILE,phrases_data)
        elif c.data.startswith("phrase_no_"):
            phrases_data[idx]["status"]="rejected"; save_json_list(PHRASES_FILE,phrases_data)
        show_phrase_admin(c.message.chat.id,idx)
    except Exception:
        bot.send_message(c.message.chat.id,"Не удалось открыть фразу.")

@bot.callback_query_handler(func=lambda c:c.data in ("add_banner","view_banners","publish_banner","cancel_banner"))
def banner_admin_callbacks(c):
    if c.from_user.id != ADMIN_ID:
        bot.answer_callback_query(c.id,"Нет доступа",show_alert=True); return
    bot.answer_callback_query(c.id)
    if c.data=="view_banners":
        show_banner(c.message.chat.id,0)
    elif c.data=="add_banner":
        admin_banner_state[c.message.chat.id]={"step":"photo"}
        bot.send_message(c.message.chat.id,"📸 <b>Новый баннер</b>\n\n1/4 Отправьте фотографию баннера.\n\nОтмена: /cancelbanner",parse_mode="HTML")
    elif c.data=="cancel_banner":
        admin_banner_state.pop(c.message.chat.id,None)
        bot.send_message(c.message.chat.id,"❌ Публикация отменена.",reply_markup=admin_menu())
    elif c.data=="publish_banner":
        data=admin_banner_state.pop(c.message.chat.id,None)
        if data and all(k in data for k in ("file_id","city","date","phrase")):
            banners_data.append({k:data[k] for k in ("file_id","city","date","phrase")})
            save_banners()
            bot.send_message(c.message.chat.id,"✅ <b>Баннер опубликован!</b>\n\nТеперь он доступен в разделе «📸 Наши баннеры».",parse_mode="HTML",reply_markup=admin_menu())


@bot.message_handler(commands=["cancelbanner"])
def cancel_banner_command(m):
    if m.from_user.id==ADMIN_ID:
        admin_banner_state.pop(m.chat.id,None)
        bot.send_message(m.chat.id,"❌ Добавление баннера отменено.",reply_markup=admin_menu())


@bot.message_handler(func=lambda m:m.from_user.id==ADMIN_ID and m.chat.id in admin_banner_state,content_types=["photo","text"])
def banner_wizard(m):
    state=admin_banner_state[m.chat.id]
    step=state.get("step")
    if step=="photo":
        if not m.photo:
            bot.send_message(m.chat.id,"Сначала отправьте фотографию баннера 📸"); return
        state["file_id"]=m.photo[-1].file_id
        state["step"]="city"
        bot.send_message(m.chat.id,"2/4 📍 Укажите город:")
    elif step=="city":
        state["city"]=(m.text or "").strip()
        state["step"]="date"
        bot.send_message(m.chat.id,"3/4 📅 Укажите дату размещения, например: 6 октября 2026:")
    elif step=="date":
        state["date"]=(m.text or "").strip()
        state["step"]="phrase"
        bot.send_message(m.chat.id,"4/4 💬 Напишите фразу, размещённую на баннере:")
    elif step=="phrase":
        state["phrase"]=(m.text or "").strip()
        state["step"]="confirm"
        caption=(f"📸 <b>Предпросмотр</b>\n\n"
                 f"💬 {html.escape(state['phrase'])}\n"
                 f"📍 {html.escape(state['city'])}\n"
                 f"📅 {html.escape(state['date'])}")
        kb=types.InlineKeyboardMarkup()
        kb.row(types.InlineKeyboardButton("✅ Опубликовать",callback_data="publish_banner"),
               types.InlineKeyboardButton("❌ Отмена",callback_data="cancel_banner"))
        bot.send_photo(m.chat.id,state["file_id"],caption=caption,parse_mode="HTML",reply_markup=kb)


@bot.message_handler(commands=["cancelbroadcast"])
def cancel_broadcast(message):
    if message.from_user.id != ADMIN_ID:
        return
    admin_waiting_broadcast.discard(message.chat.id)
    bot.send_message(message.chat.id, "Рассылка отменена.", reply_markup=admin_menu())


@bot.message_handler(func=lambda m: m.chat.id in admin_waiting_broadcast and m.from_user.id == ADMIN_ID, content_types=["text"])
def admin_broadcast(message):
    admin_waiting_broadcast.discard(message.chat.id)
    if message.text.startswith("/"):
        bot.send_message(message.chat.id, "Рассылка отменена.", reply_markup=admin_menu())
        return
    sent = 0
    failed = 0
    for chat_id in list({u.get("chat_id") for u in users_data if u.get("chat_id")}):
        try:
            bot.send_message(chat_id, "📢 <b>Новости проекта «Одно доброе слово»</b>\n\n" + html.escape(message.text), parse_mode="HTML")
            sent += 1
        except Exception:
            failed += 1
    bot.send_message(message.chat.id, f"✅ <b>Рассылка завершена</b>\n\nДоставлено: <b>{sent}</b>\nНе доставлено: <b>{failed}</b>", parse_mode="HTML", reply_markup=admin_menu())


@bot.message_handler(commands=["help"])
def help_command(message):
    remember_user(message)
    bot.send_message(message.chat.id,
        "❤️ <b>Помощь</b>\n\n"
        "Используйте кнопки меню для добрых фраз, голосования, баннеров, отчётов и поддержки проекта.\n"
        "Если вы хотите предложить свою фразу — нажмите «✍️ Предложить фразу».",
        parse_mode="HTML",reply_markup=keyboard())

@bot.message_handler(func=lambda m: True)
def fallback(message):
    remember_user(message)
    start(message)

if __name__ == "__main__":
    threading.Thread(target=daily_worker, daemon=True).start()
    print("Bot started")
    bot.infinity_polling(skip_pending=True, timeout=30, long_polling_timeout=30)
