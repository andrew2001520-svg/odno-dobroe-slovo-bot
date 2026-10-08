import os, random, html, json, threading, time, zipfile, hashlib, hmac, base64, uuid
from datetime import datetime
from urllib.parse import quote, urlparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
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
VOTE_FILE = "vote.json"
REPORTS_FILE = "reports.json"
EVENTS_FILE = "events.json"
STARS_FILE = "stars_payments.json"
ANON_FILE = "anonymous_messages.json"
KINDNESS_FILE = "kindness_chain.json"
STEPS_FILE = "small_steps.json"
LETTERS_FILE = "private_letters.json"
CITIES_FILE = "kindness_cities.json"
DAILY_MISSIONS_FILE = "daily_missions.json"
NETWORK_FILE = "kindness_network.json"
CITY_VOTE_FILE = "next_city_vote.json"
PROJECT_GOAL_FILE = "project_goal.json"
SUPPORT_EMAIL = "andrew2001520@icloud.com"
SUPPORT_TELEGRAM_URL = "https://t.me/raskol4444"
STAR_PACKS = [25, 50, 100, 250, 500]

CABINET_SESSION_TTL = 60 * 60 * 24 * 30

def _cabinet_b64encode(raw):
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")

def _cabinet_b64decode(value):
    value += "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value.encode("ascii"))

def cabinet_make_session(user_id):
    expires = int(time.time()) + CABINET_SESSION_TTL
    payload = f"{int(user_id)}:{expires}"
    sig = hmac.new(TOKEN.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return _cabinet_b64encode(f"{payload}:{sig}".encode("utf-8"))

def cabinet_check_session(token):
    try:
        raw = _cabinet_b64decode(token).decode("utf-8")
        user_id, expires, sig = raw.split(":", 2)
        payload = f"{user_id}:{expires}"
        expected = hmac.new(TOKEN.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected) or int(expires) < int(time.time()):
            return None
        return int(user_id)
    except Exception:
        return None

def verify_telegram_login(data):
    try:
        supplied_hash = str(data.get("hash", ""))
        auth_date = int(data.get("auth_date", 0))
        if not supplied_hash or abs(int(time.time()) - auth_date) > 86400:
            return None
        fields = []
        for key, value in data.items():
            if key == "hash" or value is None:
                continue
            fields.append(f"{key}={value}")
        check_string = "\n".join(sorted(fields))
        secret_key = hashlib.sha256(TOKEN.encode("utf-8")).digest()
        expected = hmac.new(secret_key, check_string.encode("utf-8"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, supplied_hash):
            return None
        return int(data["id"])
    except Exception:
        return None

def cabinet_profile_payload(uid):
    steps = _user_steps(uid)
    done = sum(1 for x in steps if x.get("status") == "done")
    streak = _step_streak(uid)
    kindness = kindness_records()
    sent = sum(1 for x in kindness if str(x.get("user_id")) == str(uid))
    received = sum(1 for x in kindness if str(uid) in {str(v) for v in (x.get("delivered_to", []) or [])})
    letters = load_json_list(LETTERS_FILE)
    waiting = sum(1 for x in letters if str(x.get("user_id")) == str(uid) and x.get("status") == "waiting")
    missions_done = sum(1 for x in daily_mission_records() if str(x.get("user_id")) == str(uid))
    current_level, next_level = kindness_level(sent)
    badges = achievement_lines(sent, received, done, streak)
    if missions_done >= 1: badges.append("🌅 Добро началось")
    if missions_done >= 7: badges.append("✨ Неделя добра")
    if missions_done >= 30: badges.append("💛 Добрая привычка")
    city = ""
    for row in reversed(city_records()):
        if str(row.get("user_id")) == str(uid):
            city = normalize_city_name(row.get("city")) or ""
            break
    user = next((x for x in users_data if str(x.get("id")) == str(uid)), {})
    next_target = next_level[0] if next_level else current_level[0]
    return {
        "ok": True,
        "profile": {
            "first_name": user.get("first_name", ""),
            "city": city,
            "level": current_level[1],
            "sent": sent,
            "received": received,
            "steps_done": done,
            "streak": streak,
            "letters_waiting": waiting,
            "missions_done": missions_done,
            "achievements": badges,
            "next_level_target": next_target,
            "progress_percent": 100 if not next_level else max(0, min(100, round(sent / max(1, next_target) * 100))),
        }
    }


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

BOT_VERSION = "2026.10.07-cabinet-v1"

def keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, is_persistent=True)
    kb.row("❤️ Мне нужно одно доброе слово")
    kb.row("💌 Передать добро", "🫂 Мне нужно выговориться")
    kb.row("🌱 Мой маленький шаг", "🌙 Письмо в тишину")
    kb.row("🏡 Моё пространство", "🌍 Добро прямо сейчас")
    kb.row("🌍 Живая сеть добра")
    kb.row("📍 Карта добра")
    kb.row("🌅 Добро дня", "💬 Доброе слово")
    kb.row("❤️ Одно доброе слово")
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
waiting_for_anonymous = set()
admin_anon_reply = {}
waiting_for_kindness = set()
waiting_for_step = set()
waiting_for_letter = set()
waiting_for_city = set()
pending_letters = {}

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

def load_vote():
    try:
        with open(VOTE_FILE,"r",encoding="utf-8") as f:
            d=json.load(f)
            if isinstance(d,dict): return d
    except Exception:
        pass
    return {
        "active": True,
        "question": "Какую фразу вы хотели бы увидеть на улице?",
        "options": ["❤️ Ты справишься","🌿 Не сдавайся","☀️ Всё ещё впереди","❤️ Цени тех, кто рядом","✨ Ты важен"],
        "votes": {}
    }

def save_vote():
    try:
        with open(VOTE_FILE,"w",encoding="utf-8") as f:
            json.dump(vote_data,f,ensure_ascii=False,indent=2)
    except Exception:
        pass

vote_data=load_vote()
admin_vote_setup={}
reports_data=load_json_list(REPORTS_FILE)
admin_report_state={}
events_data=load_json_list(EVENTS_FILE)
NOTIFY_MILESTONES={10,25,50,100,250,500,1000}

def log_event(kind, text, notify=False):
    event={"time":datetime.now().strftime("%d.%m.%Y %H:%M"),"kind":kind,"text":text}
    events_data.append(event)
    if len(events_data)>300:
        del events_data[:-300]
    save_json_list(EVENTS_FILE,events_data)
    if notify:
        try:
            bot.send_message(ADMIN_ID,f"🔔 <b>{html.escape(kind)}</b>\n\n{html.escape(text)}",parse_mode="HTML")
        except Exception:
            pass

def show_event_log(chat_id,page=0):
    page=max(0,page)
    per_page=10
    rev=list(reversed(events_data))
    start=page*per_page
    items=rev[start:start+per_page]
    if not items:
        bot.send_message(chat_id,"📋 Журнал событий пока пуст.",reply_markup=admin_menu())
        return
    lines=["📋 <b>Журнал событий</b>",""]
    for e in items:
        lines.append(f"• <b>{html.escape(e.get('time',''))}</b> — {html.escape(e.get('kind',''))}\n{html.escape(e.get('text',''))}")
    kb=types.InlineKeyboardMarkup()
    nav=[]
    if page>0: nav.append(types.InlineKeyboardButton("◀️ Новее",callback_data=f"events_{page-1}"))
    if start+per_page<len(rev): nav.append(types.InlineKeyboardButton("Старее ▶️",callback_data=f"events_{page+1}"))
    if nav: kb.row(*nav)
    kb.add(types.InlineKeyboardButton("🗑 Очистить журнал",callback_data="events_clear"))
    bot.send_message(chat_id,"\n\n".join(lines),parse_mode="HTML",reply_markup=kb)

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
    bot.send_message(message.chat.id, "❤️ <b>Одно доброе слово</b>\n\nЗдесь можно получить настоящее доброе слово от незнакомого человека, оставить своё следующему, выговориться или просто найти немного поддержки.\n\nВыберите, что вам сейчас нужно 👇", parse_mode="HTML", reply_markup=keyboard())

@bot.message_handler(commands=["menu"])
def menu_command(message):
    remember_user(message)
    bot.send_message(message.chat.id, "❤️ <b>Главное меню обновлено</b>\n\nНовые разделы уже здесь 👇", parse_mode="HTML", reply_markup=keyboard())

@bot.message_handler(commands=["version"])
def version_command(message):
    bot.send_message(message.chat.id, f"Версия бота: <code>{BOT_VERSION}</code>", parse_mode="HTML", reply_markup=keyboard())

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


DAILY_MISSIONS = [
    "Напиши человеку, которому давно хотел сказать спасибо.",
    "Скажи сегодня кому-нибудь искреннее доброе слово.",
    "Позвони близкому человеку просто так — без повода.",
    "Сделай маленькое доброе дело так, чтобы не ждать ничего взамен.",
    "Спроси у близкого человека, как он на самом деле себя чувствует, и выслушай его.",
    "Поддержи человека, которому сегодня может быть непросто.",
    "Поблагодари человека за то, что обычно воспринимаешь как должное.",
    "Напиши короткое тёплое сообщение тому, с кем давно не общался.",
    "Уступи, помоги или прояви терпение там, где обычно спешишь.",
    "Сделай сегодня одно небольшое доброе дело для себя.",
    "Скажи близкому человеку, почему он для тебя важен.",
    "Оставь после себя сегодня хотя бы одну улыбку.",
    "Поддержи чью-то идею или старание добрыми словами.",
    "Найди минуту и искренне похвали человека за то, что он делает хорошо."
]

def daily_mission_date():
    return datetime.utcnow().strftime("%Y-%m-%d")

def daily_mission_text(date_str=None):
    date_str = date_str or daily_mission_date()
    try:
        idx = datetime.strptime(date_str, "%Y-%m-%d").date().toordinal() % len(DAILY_MISSIONS)
    except Exception:
        idx = 0
    return DAILY_MISSIONS[idx]

def daily_mission_records():
    return load_json_list(DAILY_MISSIONS_FILE)

def daily_mission_done(uid, date_str=None):
    date_str = date_str or daily_mission_date()
    return any(str(x.get("user_id")) == str(uid) and x.get("date") == date_str for x in daily_mission_records())

def daily_mission_count(date_str=None):
    date_str = date_str or daily_mission_date()
    return len({str(x.get("user_id")) for x in daily_mission_records() if x.get("date") == date_str})

# 2. Добро дня — ежедневная фраза + общая добрая миссия
@bot.message_handler(func=lambda m: m.text == "🌅 Добро дня")
def daily_kindness(message):
    remember_user(message)
    done = daily_mission_done(message.from_user.id)
    count = daily_mission_count()
    kb = types.InlineKeyboardMarkup()
    if not done:
        kb.add(types.InlineKeyboardButton("❤️ Сделано", callback_data="daily_mission_done"))
    if message.chat.id in subscribers:
        kb.add(types.InlineKeyboardButton("🔕 Отключить ежедневное сообщение", callback_data="daily_off"))
        sub = "🔔 Ежедневное сообщение включено"
    else:
        kb.add(types.InlineKeyboardButton("🔔 Получать каждый день", callback_data="daily_on"))
        sub = "🔕 Ежедневное сообщение выключено"
    status = "✅ Ты уже сделал добро дня." if done else "Когда выполнишь — нажми «❤️ Сделано»."
    text = ("🌅 <b>Добро дня</b>\n\n" + html.escape(random.choice(QUOTES)) +
            "\n\n✨ <b>Общая миссия на сегодня</b>\n" + html.escape(daily_mission_text()) +
            f"\n\n❤️ Сегодня выполнили: <b>{count}</b>\n{status}\n\n{sub}")
    bot.send_message(message.chat.id, text, parse_mode="HTML", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data == "daily_mission_done")
def daily_mission_complete(c):
    if daily_mission_done(c.from_user.id):
        bot.answer_callback_query(c.id, "Уже отмечено ❤️")
        return
    data = daily_mission_records()
    data.append({"user_id": c.from_user.id, "date": daily_mission_date(), "completed": datetime.utcnow().isoformat(timespec="seconds")})
    save_json_list(DAILY_MISSIONS_FILE, data)
    count = daily_mission_count()
    log_event("Добро дня", "Кто-то выполнил общую добрую миссию.")
    bot.answer_callback_query(c.id, "Засчитано ❤️")
    bot.send_message(c.message.chat.id, f"❤️ <b>Спасибо.</b> Сегодня эту миссию выполнили уже <b>{count}</b> чел.\n\nОдно маленькое действие тоже меняет день.", parse_mode="HTML", reply_markup=keyboard())

@bot.callback_query_handler(func=lambda c: c.data in ("daily_on", "daily_off"))
def daily_toggle(c):
    if c.data == "daily_on":
        subscribers.add(c.message.chat.id); text = "❤️ «Добро дня» включено."
        log_event("Добро дня","Новый пользователь включил ежедневную добрую фразу.",notify=True)
    else:
        subscribers.discard(c.message.chat.id); text = "🔕 «Добро дня» отключено."
        log_event("Добро дня","Пользователь отключил ежедневную добрую фразу.")
    save_subscribers(); bot.answer_callback_query(c.id, text); bot.edit_message_text(text, c.message.chat.id, c.message.message_id)

# 3. Предложить фразу
@bot.message_handler(func=lambda m: m.text == "✍️ Предложить фразу")
def suggest_phrase(message):
    waiting_for_phrase.add(message.chat.id)
    bot.send_message(message.chat.id, "✍️ <b>Предложить свою фразу</b>\n\nНапишите одним сообщением фразу, которую вы хотели бы увидеть на улицах города ❤️\n\nОтмена: /cancel", parse_mode="HTML")

@bot.message_handler(commands=["cancel"])
def cancel(message):
    waiting_for_phrase.discard(message.chat.id)
    waiting_for_anonymous.discard(message.chat.id)
    waiting_for_kindness.discard(message.chat.id)
    waiting_for_step.discard(message.chat.id)
    waiting_for_letter.discard(message.chat.id)
    waiting_for_city.discard(message.chat.id)
    if message.from_user and message.from_user.id == ADMIN_ID:
        admin_anon_reply.pop(ADMIN_ID, None)
    bot.send_message(message.chat.id, "Отменено ❤️", reply_markup=keyboard())

@bot.message_handler(func=lambda m: m.chat.id in waiting_for_phrase, content_types=["text"])
def receive_phrase(message):
    waiting_for_phrase.discard(message.chat.id); phrase = (message.text or "").strip()
    if not phrase or len(phrase) > 500:
        bot.send_message(message.chat.id, "Фраза не принята. Максимум 500 символов.", reply_markup=keyboard()); return
    u = message.from_user; username = "@" + u.username if u.username else "не указан"
    phrases_data.append({"text":phrase,"user_id":u.id,"username":u.username or "","name":u.first_name or "","status":"new","created":datetime.utcnow().isoformat(timespec="seconds")})
    save_json_list(PHRASES_FILE,phrases_data)
    log_event("Новая фраза", f"Пользователь предложил: «{phrase}»")
    bot.send_message(ADMIN_ID, "💌 <b>Новая предложенная фраза</b>\n\n" + f"«{html.escape(phrase)}»\n\n👤 {html.escape(u.first_name or 'Пользователь')}\n🔗 {html.escape(username)}\n🆔 <code>{u.id}</code>", parse_mode="HTML")
    bot.send_message(message.chat.id, "❤️ <b>Спасибо!</b> Ваша фраза принята. Возможно, однажды именно она появится на улицах города.", parse_mode="HTML", reply_markup=keyboard())

# 4. Поделиться добром
@bot.callback_query_handler(func=lambda c: c.data == "share_quote")
def share_quote(c):
    bot.answer_callback_query(c.id)
    send_kind_share_menu(c.message.chat.id)

def send_kind_share_menu(chat_id):
    kb=types.InlineKeyboardMarkup(row_width=1)
    choices=[
        ("❤️ Ты справишься.","kindshare_0"),
        ("🌿 Не сдавайся.","kindshare_1"),
        ("✨ Ты важен.","kindshare_2"),
        ("☀️ Всё ещё впереди.","kindshare_3"),
        ("❤️ Цени тех, кто рядом.","kindshare_4"),
        ("🎲 Случайная фраза","kindshare_random")
    ]
    for title,data in choices:
        kb.add(types.InlineKeyboardButton(title,callback_data=data))
    bot.send_message(chat_id,"🎁 <b>Поделиться добром</b>\n\nВыберите фразу, которую хотите отправить близкому человеку ❤️",parse_mode="HTML",reply_markup=kb)

@bot.callback_query_handler(func=lambda c:c.data.startswith("kindshare_"))
def kind_share_callback(c):
    bot.answer_callback_query(c.id)
    fixed=[
        "❤️ Ты справишься.",
        "🌿 Не сдавайся. Иногда до перемен остаётся совсем немного.",
        "✨ Ты важен. Даже если сегодня тебе кажется иначе.",
        "☀️ Всё ещё впереди. Хорошие дни обязательно придут.",
        "❤️ Цени тех, кто рядом. Иногда простые слова значат очень много."
    ]
    if c.data=="kindshare_random":
        phrase=random.choice(QUOTES)
    else:
        try: phrase=fixed[int(c.data.rsplit("_",1)[1])]
        except Exception: phrase=random.choice(QUOTES)
    share_text=f"{phrase}\n\nПусть это доброе слово сегодня будет для тебя ❤️\n\n«Одно доброе слово»"
    url="https://t.me/share/url?url="+quote("https://t.me/odno_dobroe_slovo_bot")+"&text="+quote(share_text)
    kb=types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("📤 Отправить близкому",url=url))
    kb.add(types.InlineKeyboardButton("🔄 Выбрать другую фразу",callback_data="kindshare_again"))
    bot.send_message(c.message.chat.id,f"🎁 <b>Добрая карточка</b>\n\n<b>{html.escape(phrase)}</b>\n\nПусть это доброе слово сегодня будет для тебя ❤️",parse_mode="HTML",reply_markup=kb)
    log_event("Поделиться добром","Пользователь подготовил добрую фразу для отправки.")

@bot.callback_query_handler(func=lambda c:c.data=="kindshare_again")
def kind_share_again(c):
    bot.answer_callback_query(c.id)
    send_kind_share_menu(c.message.chat.id)


@bot.message_handler(func=lambda m:m.text=="🎁 Поделиться добром")
def share_kindness_menu(message):
    remember_user(message)
    send_kind_share_menu(message.chat.id)

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
def report_caption(r, index=None):
    parts=["📊 <b>Отчёт проекта</b>"]
    if r.get("title"): parts.append("\n<b>"+html.escape(r["title"])+"</b>")
    if r.get("amount"): parts.append("💳 Сумма: <b>"+html.escape(r["amount"])+"</b>")
    if r.get("purpose"): parts.append("🧾 Назначение: "+html.escape(r["purpose"]))
    if r.get("date"): parts.append("📅 "+html.escape(r["date"]))
    if r.get("description"): parts.append("\n"+html.escape(r["description"]))
    if index is not None: parts.append(f"\n📄 Отчёт {index+1} из {len(reports_data)}")
    return "\n".join(parts)

def show_report(chat_id,index=0):
    if not reports_data:
        bot.send_message(chat_id,"📊 <b>Отчёты проекта</b>\n\nПока опубликованных отчётов нет. Здесь будут подтверждения расходов, размещений и фотографии проекта ❤️",parse_mode="HTML")
        return
    index=max(0,min(index,len(reports_data)-1))
    r=reports_data[index]
    kb=types.InlineKeyboardMarkup()
    nav=[]
    if index>0: nav.append(types.InlineKeyboardButton("◀️ Назад",callback_data=f"report_{index-1}"))
    if index<len(reports_data)-1: nav.append(types.InlineKeyboardButton("Вперёд ▶️",callback_data=f"report_{index+1}"))
    if nav: kb.row(*nav)
    caption=report_caption(r,index)
    if r.get("photo_id"):
        bot.send_photo(chat_id,r["photo_id"],caption=caption,parse_mode="HTML",reply_markup=kb)
    else:
        bot.send_message(chat_id,caption,parse_mode="HTML",reply_markup=kb)

@bot.message_handler(func=lambda m: m.text == "📊 Отчёты")
def reports(message):
    remember_user(message)
    show_report(message.chat.id,0)

@bot.callback_query_handler(func=lambda c:c.data.startswith("report_"))
def report_nav(c):
    bot.answer_callback_query(c.id)
    try: show_report(c.message.chat.id,int(c.data.split("_",1)[1]))
    except Exception: pass

# 8. Голосование
def vote_keyboard():
    kb=types.InlineKeyboardMarkup(row_width=1)
    for i,opt in enumerate(vote_data.get("options",[])):
        kb.add(types.InlineKeyboardButton(opt,callback_data=f"vote_{i}"))
    kb.add(types.InlineKeyboardButton("📊 Результаты",callback_data="vote_results"))
    return kb

def vote_results_text():
    options=vote_data.get("options",[])
    votes=vote_data.get("votes",{})
    counts=[0]*len(options)
    for idx in votes.values():
        try:
            idx=int(idx)
            if 0<=idx<len(counts): counts[idx]+=1
        except Exception: pass
    total=sum(counts)
    lines=["📊 <b>Результаты голосования</b>",""]
    for i,opt in enumerate(options):
        pct=round(counts[i]*100/total) if total else 0
        lines.append(f"{html.escape(opt)} — <b>{counts[i]}</b> ({pct}%)")
    lines.append(f"\nВсего голосов: <b>{total}</b>")
    return "\n".join(lines)

def send_vote(chat_id):
    if not vote_data.get("active",False):
        bot.send_message(chat_id,"🗳 Сейчас активного голосования нет. Следующее появится совсем скоро ❤️")
        return
    bot.send_message(chat_id,"🗳 <b>"+html.escape(vote_data.get("question","Выберите фразу"))+"</b>\n\nОдин человек — один голос. Свой выбор можно изменить до завершения голосования.",parse_mode="HTML",reply_markup=vote_keyboard())

@bot.message_handler(func=lambda m: m.text == "🗳 Выбрать фразу")
def vote_phrase(message):
    remember_user(message)
    send_vote(message.chat.id)

@bot.callback_query_handler(func=lambda c:c.data.startswith("vote_"))
def vote_callbacks(c):
    if c.data=="vote_results":
        bot.answer_callback_query(c.id)
        bot.send_message(c.message.chat.id,vote_results_text(),parse_mode="HTML")
        return
    if not vote_data.get("active",False):
        bot.answer_callback_query(c.id,"Голосование уже завершено.",show_alert=True); return
    try:
        idx=int(c.data.split("_",1)[1])
        if idx<0 or idx>=len(vote_data.get("options",[])): raise ValueError
    except Exception:
        bot.answer_callback_query(c.id,"Ошибка варианта."); return
    vote_data.setdefault("votes",{})[str(c.from_user.id)]=idx
    save_vote()
    total=len(vote_data.get("votes",{}))
    log_event("Голосование",f"Получен голос за вариант: {vote_data.get('options',[])[idx]}")
    if total in NOTIFY_MILESTONES:
        try: bot.send_message(ADMIN_ID,f"🗳 <b>Голосование: {total} голосов!</b>\n\n"+vote_results_text(),parse_mode="HTML")
        except Exception: pass
    bot.answer_callback_query(c.id,"❤️ Ваш голос учтён!",show_alert=False)

@bot.callback_query_handler(func=lambda c: c.data == "open_vote")
def open_vote(c):
    bot.answer_callback_query(c.id)
    send_vote(c.message.chat.id)

def load_stars_payments():
    try:
        with open(STARS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception:
        return []

def save_stars_payments(data):
    try:
        with open(STARS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def stars_stats():
    payments = load_stars_payments()
    total = sum(int(x.get("amount", 0)) for x in payments)
    supporters = len({str(x.get("user_id")) for x in payments if x.get("user_id") is not None})
    return total, len(payments), supporters

def stars_keyboard():
    kb = types.InlineKeyboardMarkup(row_width=2)
    buttons = [types.InlineKeyboardButton(f"⭐ {amount}", callback_data=f"stars_{amount}") for amount in STAR_PACKS]
    kb.add(*buttons)
    kb.add(types.InlineKeyboardButton("💳 Поддержать рублями", url=DONATE_URL))
    kb.add(types.InlineKeyboardButton("💬 Поддержка", url=SUPPORT_TELEGRAM_URL))
    return kb

@bot.message_handler(func=lambda m: m.text == "❤️ Поддержать проект")
def donate(message):
    total_stars, payments_count, supporters_count = stars_stats()
    bot.send_message(
        message.chat.id,
        "❤️ <b>Поддержать проект</b>\n\n"
        "Ваш вклад помогает оплачивать печать, аренду рекламных конструкций, монтаж и размещение баннеров.\n\n"
        f"⭐ Уже собрано: <b>{total_stars} Stars</b>\n"
        f"❤️ Поддержали: <b>{supporters_count}</b> чел.\n"
        f"🧾 Платежей Stars: <b>{payments_count}</b>\n\n"
        "Можно поддержать проект Telegram Stars ⭐ или рублями 💳",
        parse_mode="HTML", reply_markup=stars_keyboard())

@bot.callback_query_handler(func=lambda c: c.data.startswith("stars_"))
def stars_invoice(c):
    try:
        amount = int(c.data.split("_", 1)[1])
    except Exception:
        return bot.answer_callback_query(c.id, "Ошибка суммы")
    if amount not in STAR_PACKS:
        return bot.answer_callback_query(c.id, "Недоступная сумма")
    bot.answer_callback_query(c.id)
    bot.send_invoice(
        c.message.chat.id,
        title="Поддержать «Одно доброе слово»",
        description=f"Добровольная поддержка социального проекта — {amount} Telegram Stars",
        invoice_payload=f"support_stars:{amount}:{c.from_user.id}:{int(time.time())}",
        provider_token="",
        currency="XTR",
        prices=[types.LabeledPrice(label="Поддержка проекта", amount=amount)],
        start_parameter="support-stars")

@bot.pre_checkout_query_handler(func=lambda q: True)
def stars_pre_checkout(q):
    if q.currency != "XTR" or not q.invoice_payload.startswith("support_stars:"):
        return bot.answer_pre_checkout_query(q.id, ok=False, error_message="Не удалось проверить платёж. Попробуйте ещё раз.")
    bot.answer_pre_checkout_query(q.id, ok=True)

@bot.message_handler(content_types=["successful_payment"])
def stars_success(message):
    p = message.successful_payment
    record = {
        "user_id": message.from_user.id,
        "username": message.from_user.username or "",
        "first_name": message.from_user.first_name or "",
        "amount": p.total_amount,
        "currency": p.currency,
        "payload": p.invoice_payload,
        "telegram_payment_charge_id": p.telegram_payment_charge_id,
        "provider_payment_charge_id": getattr(p, "provider_payment_charge_id", ""),
        "date": datetime.utcnow().isoformat() + "Z"
    }
    payments = load_stars_payments(); payments.append(record); save_stars_payments(payments)
    try:
        log_event("stars_payment", f"{message.from_user.id}: {p.total_amount} XTR")
    except Exception:
        pass
    total_stars, payments_count, supporters_count = stars_stats()
    bot.send_message(
        message.chat.id,
        f"⭐ <b>Спасибо за поддержку!</b>\n\n"
        f"Получено: <b>{p.total_amount} ⭐</b>\n"
        f"Всего проект получил: <b>{total_stars} ⭐</b>\n"
        f"Проект поддержали: <b>{supporters_count}</b> чел. ❤️",
        parse_mode="HTML")
    try:
        bot.send_message(ADMIN_ID, f"⭐ <b>Новая поддержка Stars</b>\n\nПользователь: {message.from_user.id}\nСумма: <b>{p.total_amount} ⭐</b>", parse_mode="HTML")
    except Exception:
        pass

@bot.message_handler(commands=["paysupport"])
def pay_support(message):
    bot.send_message(message.chat.id, f"💬 <b>Поддержка по платежам</b>\n\nЕсли возник вопрос по Telegram Stars или пожертвованию, напишите:\n📧 {SUPPORT_EMAIL}\n✈️ @raskol4444", parse_mode="HTML")

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
                try: bot.send_message(chat_id, "🌅 <b>Добро дня</b>\n\n" + html.escape(random.choice(QUOTES)) + "\n\n✨ <b>Миссия дня</b>\n" + html.escape(daily_mission_text()) + "\n\nОткрой «🌅 Добро дня» и отметь выполнение ❤️", parse_mode="HTML")
                except Exception: pass
            last_date = now.date()

        # Возвращаем личные письма, срок которых наступил.
        letters = load_json_list(LETTERS_FILE)
        changed = False
        for item in letters:
            if item.get("status") != "waiting":
                continue
            try:
                due = datetime.fromisoformat(item.get("due", ""))
            except Exception:
                continue
            if due <= now:
                try:
                    bot.send_message(
                        int(item["chat_id"]),
                        "🌙 <b>Письмо из прошлого</b>\n\nКогда-то ты решил вернуть себе эти слова:\n\n“" + html.escape(item.get("text", "")) + "”\n\nМожно просто прочитать их и идти дальше. ❤️",
                        parse_mode="HTML",
                    )
                    item["status"] = "delivered"
                    item["delivered"] = now.isoformat(timespec="seconds")
                    changed = True
                except Exception:
                    pass
        if changed:
            save_json_list(LETTERS_FILE, letters)
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
        types.InlineKeyboardButton("📊 Отчёты", callback_data="admin_reports"),
        types.InlineKeyboardButton("💾 Резервная копия", callback_data="admin_backup"),
        types.InlineKeyboardButton("📋 Журнал событий", callback_data="admin_events"),
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
        bot.send_message(c.message.chat.id, f"📊 <b>Статистика</b>\n\n👥 Пользователей: <b>{len(users_data)}</b>\n🌅 Подписчиков «Добра дня»: <b>{len(subscribers)}</b>\n✍️ Предложенных фраз: <b>{len(phrases_data)}</b>\n📸 Баннеров: <b>{len(banners_data)}</b>\n📊 Отчётов: <b>{len(reports_data)}</b>\n⭐ Stars получено: <b>{sum(int(x.get('amount',0)) for x in load_stars_payments())}</b>\n⭐ Платежей Stars: <b>{len(load_stars_payments())}</b>", parse_mode="HTML", reply_markup=admin_menu())

    elif c.data == "admin_broadcast":
        admin_waiting_broadcast.add(c.message.chat.id)
        bot.send_message(c.message.chat.id, "📢 Отправьте следующим сообщением текст рассылки подписчикам «Добра дня».\n\nОтмена: /cancelbroadcast")

    elif c.data == "admin_vote":
        kb=types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("➕ Новое голосование",callback_data="vote_admin_new"))
        kb.add(types.InlineKeyboardButton("📊 Результаты",callback_data="vote_admin_results"))
        if vote_data.get("active"):
            kb.add(types.InlineKeyboardButton("🏆 Завершить",callback_data="vote_admin_finish"))
        bot.send_message(c.message.chat.id,"🗳 <b>Управление голосованием</b>\n\n"+("🟢 Сейчас голосование активно." if vote_data.get("active") else "⚪ Активного голосования нет."),parse_mode="HTML",reply_markup=kb)

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

    elif c.data == "admin_reports":
        kb=types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("➕ Добавить отчёт",callback_data="report_admin_new"))
        kb.add(types.InlineKeyboardButton("👁 Посмотреть отчёты",callback_data="report_admin_view"))
        bot.send_message(c.message.chat.id,f"📊 <b>Управление отчётами</b>\n\nОпубликовано: <b>{len(reports_data)}</b>",parse_mode="HTML",reply_markup=kb)

    elif c.data == "admin_events":
        show_event_log(c.message.chat.id,0)

    elif c.data == "admin_backup":
        backup_name=f"odno_dobroe_slovo_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        backup_files=[SUBS_FILE,BANNERS_FILE,USERS_FILE,PHRASES_FILE,VOTE_FILE,REPORTS_FILE,EVENTS_FILE,STARS_FILE,ANON_FILE,KINDNESS_FILE,STEPS_FILE,LETTERS_FILE]
        # Save current in-memory data first.
        save_subscribers()
        save_banners()
        save_json_list(USERS_FILE,users_data)
        save_json_list(PHRASES_FILE,phrases_data)
        save_vote()
        save_json_list(REPORTS_FILE,reports_data)
        save_json_list(EVENTS_FILE,events_data)
        try:
            with zipfile.ZipFile(backup_name,"w",zipfile.ZIP_DEFLATED) as z:
                added=0
                for filename in backup_files:
                    if os.path.exists(filename):
                        z.write(filename,arcname=os.path.basename(filename))
                        added+=1
                info={
                    "project":"Одно доброе слово",
                    "created":datetime.now().isoformat(timespec="seconds"),
                    "files":added,
                    "users":len(users_data),
                    "subscribers":len(subscribers),
                    "banners":len(banners_data),
                    "phrases":len(phrases_data),
                    "reports":len(reports_data)
                }
                z.writestr("backup_info.json",json.dumps(info,ensure_ascii=False,indent=2))
            with open(backup_name,"rb") as f:
                bot.send_document(c.message.chat.id,f,caption="💾 <b>Резервная копия проекта готова.</b>\n\nСохраните этот ZIP-файл в надёжном месте. Он содержит данные бота на момент создания копии.",parse_mode="HTML")
            try: os.remove(backup_name)
            except Exception: pass
        except Exception as e:
            bot.send_message(c.message.chat.id,"❌ Не удалось создать резервную копию. Попробуйте ещё раз.",reply_markup=admin_menu())

    elif c.data == "admin_settings":
        bot.send_message(c.message.chat.id, f"⚙️ <b>Настройки</b>\n\n🌐 Сайт: {SITE_URL}\n❤️ Пожертвования: {DONATE_URL}\n🌅 Добро дня: около 09:00 по Москве", parse_mode="HTML", reply_markup=admin_menu())

    elif c.data == "admin_close":
        bot.edit_message_text("🔒 Админ-панель закрыта.", c.message.chat.id, c.message.message_id)


@bot.callback_query_handler(func=lambda c:c.data.startswith("events_"))
def events_callbacks(c):
    if c.from_user.id!=ADMIN_ID:
        bot.answer_callback_query(c.id,"Нет доступа",show_alert=True); return
    bot.answer_callback_query(c.id)
    if c.data=="events_clear":
        events_data.clear()
        save_json_list(EVENTS_FILE,events_data)
        bot.send_message(c.message.chat.id,"🗑 Журнал событий очищен.",reply_markup=admin_menu())
    else:
        try: show_event_log(c.message.chat.id,int(c.data.split("_",1)[1]))
        except Exception: pass

@bot.callback_query_handler(func=lambda c:c.data in ("report_admin_new","report_admin_view","report_publish","report_cancel"))
def report_admin_callbacks(c):
    if c.from_user.id!=ADMIN_ID:
        bot.answer_callback_query(c.id,"Нет доступа",show_alert=True); return
    bot.answer_callback_query(c.id)
    if c.data=="report_admin_view":
        show_report(c.message.chat.id,0)
    elif c.data=="report_admin_new":
        admin_report_state[c.message.chat.id]={"step":"title"}
        bot.send_message(c.message.chat.id,"📊 <b>Новый отчёт</b>\n\n1/6 Напишите название.\nНапример: «Печать первого баннера»\n\nОтмена: /cancelreport",parse_mode="HTML")
    elif c.data=="report_cancel":
        admin_report_state.pop(c.message.chat.id,None)
        bot.send_message(c.message.chat.id,"❌ Добавление отчёта отменено.",reply_markup=admin_menu())
    elif c.data=="report_publish":
        d=admin_report_state.pop(c.message.chat.id,None)
        if d:
            reports_data.append({k:d.get(k,"") for k in ("title","amount","purpose","date","description","photo_id")})
            save_json_list(REPORTS_FILE,reports_data)
            log_event("Новый отчёт",f"Опубликован отчёт: {d.get('title','')}",notify=True)
            bot.send_message(c.message.chat.id,"✅ <b>Отчёт опубликован.</b>\n\nТеперь пользователи увидят его в разделе «📊 Отчёты».",parse_mode="HTML",reply_markup=admin_menu())

@bot.message_handler(commands=["cancelreport"])
def cancel_report(m):
    if m.from_user.id==ADMIN_ID:
        admin_report_state.pop(m.chat.id,None)
        bot.send_message(m.chat.id,"❌ Добавление отчёта отменено.",reply_markup=admin_menu())

@bot.message_handler(func=lambda m:m.from_user.id==ADMIN_ID and m.chat.id in admin_report_state,content_types=["text","photo"])
def report_wizard(m):
    d=admin_report_state[m.chat.id]
    step=d.get("step")
    if step=="title":
        if not m.text: bot.send_message(m.chat.id,"Отправьте название текстом."); return
        d["title"]=m.text.strip(); d["step"]="amount"
        bot.send_message(m.chat.id,"2/6 💳 Укажите сумму.\nНапример: 8 500 ₽\nЕсли суммы нет — отправьте «0».")
    elif step=="amount":
        if not m.text: return
        d["amount"]=m.text.strip(); d["step"]="purpose"
        bot.send_message(m.chat.id,"3/6 🧾 Напишите назначение расхода/операции.\nНапример: печать и монтаж.")
    elif step=="purpose":
        if not m.text: return
        d["purpose"]=m.text.strip(); d["step"]="date"
        bot.send_message(m.chat.id,"4/6 📅 Укажите дату.\nНапример: 10 октября 2026.")
    elif step=="date":
        if not m.text: return
        d["date"]=m.text.strip(); d["step"]="description"
        bot.send_message(m.chat.id,"5/6 📝 Добавьте короткое описание.")
    elif step=="description":
        if not m.text: return
        d["description"]=m.text.strip(); d["step"]="photo"
        bot.send_message(m.chat.id,"6/6 📸 Отправьте фото чека, подтверждения или размещённого баннера.\n\nЕсли фото не нужно — отправьте /skipphoto")
    elif step=="photo":
        if not m.photo:
            bot.send_message(m.chat.id,"Отправьте фотографию или /skipphoto."); return
        d["photo_id"]=m.photo[-1].file_id
        d["step"]="confirm"
        kb=types.InlineKeyboardMarkup()
        kb.row(types.InlineKeyboardButton("✅ Опубликовать",callback_data="report_publish"),types.InlineKeyboardButton("❌ Отмена",callback_data="report_cancel"))
        bot.send_photo(m.chat.id,d["photo_id"],caption="👁 <b>Предпросмотр</b>\n\n"+report_caption(d),parse_mode="HTML",reply_markup=kb)

@bot.message_handler(commands=["skipphoto"])
def report_skip_photo(m):
    d=admin_report_state.get(m.chat.id)
    if m.from_user.id!=ADMIN_ID or not d or d.get("step")!="photo": return
    d["photo_id"]=""
    d["step"]="confirm"
    kb=types.InlineKeyboardMarkup()
    kb.row(types.InlineKeyboardButton("✅ Опубликовать",callback_data="report_publish"),types.InlineKeyboardButton("❌ Отмена",callback_data="report_cancel"))
    bot.send_message(m.chat.id,"👁 <b>Предпросмотр</b>\n\n"+report_caption(d),parse_mode="HTML",reply_markup=kb)

@bot.callback_query_handler(func=lambda c:c.data.startswith("vote_admin_"))
def vote_admin_callback(c):
    if c.from_user.id!=ADMIN_ID:
        bot.answer_callback_query(c.id,"Нет доступа",show_alert=True); return
    bot.answer_callback_query(c.id)
    if c.data=="vote_admin_results":
        bot.send_message(c.message.chat.id,vote_results_text(),parse_mode="HTML")
    elif c.data=="vote_admin_finish":
        vote_data["active"]=False
        save_vote()
        options=vote_data.get("options",[])
        counts=[0]*len(options)
        for v in vote_data.get("votes",{}).values():
            try:
                v=int(v)
                if 0<=v<len(counts): counts[v]+=1
            except Exception: pass
        if options:
            winner=options[counts.index(max(counts))]
            bot.send_message(c.message.chat.id,f"🏆 <b>Голосование завершено</b>\n\nПобедила фраза:\n<b>{html.escape(winner)}</b>\n\n"+vote_results_text(),parse_mode="HTML",reply_markup=admin_menu())
        else:
            bot.send_message(c.message.chat.id,"Голосование завершено.",reply_markup=admin_menu())
    elif c.data=="vote_admin_new":
        admin_vote_setup[c.message.chat.id]={"step":"question"}
        bot.send_message(c.message.chat.id,"🗳 <b>Новое голосование</b>\n\n1/2 Напишите вопрос голосования.\n\nОтмена: /cancelvote",parse_mode="HTML")

@bot.message_handler(commands=["cancelvote"])
def cancel_vote_setup(m):
    if m.from_user.id==ADMIN_ID:
        admin_vote_setup.pop(m.chat.id,None)
        bot.send_message(m.chat.id,"❌ Создание голосования отменено.",reply_markup=admin_menu())

@bot.message_handler(func=lambda m:m.from_user.id==ADMIN_ID and m.chat.id in admin_vote_setup,content_types=["text"])
def vote_setup_message(m):
    st=admin_vote_setup[m.chat.id]
    if st.get("step")=="question":
        if m.text.startswith("/"): return
        st["question"]=m.text.strip()
        st["step"]="options"
        bot.send_message(m.chat.id,"2/2 Отправьте варианты <b>каждый с новой строки</b>.\n\nНапример:\nТы справишься\nНе сдавайся\nТы важен",parse_mode="HTML")
    elif st.get("step")=="options":
        opts=[x.strip() for x in (m.text or "").splitlines() if x.strip()]
        if not 2<=len(opts)<=10:
            bot.send_message(m.chat.id,"Нужно от 2 до 10 вариантов. Отправьте их ещё раз, каждый с новой строки."); return
        vote_data.clear()
        vote_data.update({"active":True,"question":st["question"],"options":opts,"votes":{}})
        save_vote()
        admin_vote_setup.pop(m.chat.id,None)
        bot.send_message(m.chat.id,"✅ <b>Новое голосование запущено!</b>\n\nПользователи увидят его через «🗳 Выбрать фразу».",parse_mode="HTML",reply_markup=admin_menu())

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
            log_event("Новый баннер",f"Опубликован баннер: {data.get('phrase','')}",notify=True)
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




# 🏆 Достижения и уровни добра.
KINDNESS_LEVELS = [
    (0, "🌱 Начало пути"),
    (1, "✨ Первый луч"),
    (5, "☀️ Несёшь тепло"),
    (25, "❤️ Человек добра"),
    (50, "🏮 Маяк добра"),
    (100, "💫 Сердце цепочки"),
]

def kindness_level(sent_count):
    current = KINDNESS_LEVELS[0]
    next_level = None
    for item in KINDNESS_LEVELS:
        if sent_count >= item[0]:
            current = item
        elif next_level is None:
            next_level = item
            break
    return current, next_level

def achievement_lines(sent, received, done, streak):
    badges = []
    if sent >= 1: badges.append("✨ Первый луч — передано первое доброе слово")
    if sent >= 5: badges.append("☀️ Несёшь тепло — передано 5 добрых слов")
    if sent >= 25: badges.append("❤️ Человек добра — передано 25 добрых слов")
    if sent >= 50: badges.append("🏮 Маяк добра — передано 50 добрых слов")
    if sent >= 100: badges.append("💫 Сердце цепочки — передано 100 добрых слов")
    if received >= 10: badges.append("🤍 Открытое сердце — получено 10 добрых слов")
    if done >= 1: badges.append("🌱 Первый шаг — выполнен первый маленький шаг")
    if done >= 10: badges.append("🌿 Иду вперёд — выполнено 10 маленьких шагов")
    if streak >= 7: badges.append("🔥 Неделя движения — серия 7 дней")
    return badges

# 💌 Цепочка добра — анонимные добрые слова между пользователями.
def kindness_records():
    return load_json_list(KINDNESS_FILE)

def save_kindness_records(data):
    save_json_list(KINDNESS_FILE, data)

def kindness_stats():
    data = kindness_records()
    return len(data), len({str(x.get("user_id")) for x in data if x.get("user_id") is not None})

def kindness_home_keyboard():
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("❤️ Получить слово от человека", callback_data="kindness_receive"))
    kb.add(types.InlineKeyboardButton("💌 Оставить слово следующему", callback_data="kindness_write"))
    return kb

@bot.message_handler(func=lambda m: m.text == "❤️ Мне нужно одно доброе слово")
def kindness_receive_menu(message):
    remember_user(message)
    total, people = kindness_stats()
    bot.send_message(message.chat.id,
        "❤️ <b>Одно настоящее доброе слово</b>\n\n"
        "Здесь фразы оставляют сами люди — для того, кто откроет бота после них. "
        "Никаких имён и профилей. Только несколько добрых слов от человека человеку.\n\n"
        f"💌 В цепочке уже <b>{total}</b> добрых слов от <b>{people}</b> участников.",
        parse_mode="HTML", reply_markup=kindness_home_keyboard())

@bot.message_handler(func=lambda m: m.text == "💌 Передать добро")
def kindness_write_menu(message):
    remember_user(message)
    waiting_for_kindness.add(message.chat.id)
    bot.send_message(message.chat.id,
        "💌 <b>Оставьте доброе слово незнакомому человеку</b>\n\n"
        "Напишите короткое искреннее сообщение — то, что вам самому было бы приятно прочитать в трудный день. "
        "Имя и username получателю не показываются.\n\nДо 700 символов. Отмена: /cancel",
        parse_mode="HTML")

@bot.callback_query_handler(func=lambda c: c.data == "kindness_write")
def kindness_write_callback(c):
    bot.answer_callback_query(c.id)
    waiting_for_kindness.add(c.message.chat.id)
    bot.send_message(c.message.chat.id,
        "💌 <b>Напишите доброе слово следующему человеку.</b>\n\n"
        "До 700 символов. Ваше имя и username не будут показаны. Отмена: /cancel",
        parse_mode="HTML")

@bot.message_handler(func=lambda m: m.chat.id in waiting_for_kindness, content_types=["text"])
def kindness_save(m):
    text = (m.text or "").strip()
    if text == "/cancel":
        waiting_for_kindness.discard(m.chat.id)
        bot.send_message(m.chat.id, "Отменено ❤️", reply_markup=keyboard())
        return
    if not text or len(text) > 700:
        bot.send_message(m.chat.id, "Сообщение должно быть от 1 до 700 символов. Попробуйте ещё раз или отправьте /cancel.")
        return
    waiting_for_kindness.discard(m.chat.id)
    data = kindness_records()
    data.append({
        "id": max([int(x.get("id", 0)) for x in data] or [0]) + 1,
        "chain_id": max([int(x.get("id", 0)) for x in data] or [0]) + 1,
        "user_id": m.from_user.id,
        "text": text,
        "created": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "delivered_to": []
    })
    if len(data) > 5000:
        data = data[-5000:]
    save_kindness_records(data)
    total, people = kindness_stats()
    user_sent = sum(1 for x in data if x.get("user_id") == m.from_user.id)
    milestone = {1: "✨ <b>Новое достижение: Первый луч</b>", 5: "☀️ <b>Новое достижение: Несёшь тепло</b>", 25: "❤️ <b>Новое достижение: Человек добра</b>", 50: "🏮 <b>Новое достижение: Маяк добра</b>", 100: "💫 <b>Новое достижение: Сердце цепочки</b>"}.get(user_sent)
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("❤️ Получить доброе слово", callback_data="kindness_receive"))
    bot.send_message(m.chat.id,
        "❤️ <b>Спасибо. Ваше доброе слово теперь в цепочке.</b>\n\n"
        "Однажды его получит человек, которому, возможно, именно сегодня нужно это прочитать.\n\n"
        f"💌 Всего передано: <b>{total}</b>", parse_mode="HTML", reply_markup=kb)
    if milestone:
        bot.send_message(m.chat.id, milestone + f"\n\nТы передал уже <b>{user_sent}</b> добрых слов. Награда появилась в 🏡 «Моём пространстве». ❤️", parse_mode="HTML")
    log_event("Цепочка добра", "Пользователь оставил анонимное доброе слово.")

@bot.callback_query_handler(func=lambda c: c.data == "kindness_receive")
def kindness_receive(c):
    bot.answer_callback_query(c.id)
    data = kindness_records()
    uid = c.from_user.id
    # Не показываем человеку его собственное сообщение и по возможности не повторяем уже полученное.
    candidates = [x for x in data if x.get("user_id") != uid and uid not in x.get("delivered_to", [])]
    if not candidates:
        candidates = [x for x in data if x.get("user_id") != uid]
    if not candidates:
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("💌 Оставить первое слово", callback_data="kindness_write"))
        bot.send_message(c.message.chat.id,
            "🌱 Пока в цепочке нет чужого доброго слова для вас. Можно оставить своё — с него для кого-то всё начнётся. ❤️",
            reply_markup=kb)
        return
    rec = random.choice(candidates)
    rec.setdefault("delivered_to", [])
    if uid not in rec["delivered_to"]:
        rec["delivered_to"].append(uid)
        # Не раздуваем запись бесконечно.
        rec["delivered_to"] = rec["delivered_to"][-500:]
        save_kindness_records(data)
        record_network_hop(rec, uid)
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("💌 Передать добро дальше", callback_data="kindness_write"))
    kb.add(types.InlineKeyboardButton("❤️ Получить ещё одно", callback_data="kindness_receive"))
    bot.send_message(c.message.chat.id,
        "💌 <b>Кто-то оставил эти слова для человека, которому они понадобятся:</b>\n\n"
        f"«{html.escape(rec.get('text',''))}»\n\n"
        "❤️ От одного человека — другому. Анонимно.",
        parse_mode="HTML", reply_markup=kb)
    log_event("Цепочка добра", "Пользователь получил доброе слово из цепочки.")

# Проектные разделы убраны с главного экрана в один центр.
def project_hub_keyboard():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.row(types.InlineKeyboardButton("❤️ Поддержать", callback_data="hub_donate"),
           types.InlineKeyboardButton("📸 Баннеры", callback_data="hub_banners"))
    kb.row(types.InlineKeyboardButton("🗳 Голосование", callback_data="hub_vote"),
           types.InlineKeyboardButton("📊 Отчёты", callback_data="hub_reports"))
    kb.row(types.InlineKeyboardButton("✍️ Предложить фразу", callback_data="hub_phrase"),
           types.InlineKeyboardButton("🎯 Следующий баннер", callback_data="hub_next"))
    kb.row(types.InlineKeyboardButton("🌐 Сайт проекта", url=SITE_URL),
           types.InlineKeyboardButton("💬 Поддержка", url=SUPPORT_TELEGRAM_URL))
    return kb

@bot.message_handler(func=lambda m: m.text == "❤️ Одно доброе слово")
def project_hub(message):
    remember_user(message)
    bot.send_message(message.chat.id,
        "❤️ <b>Проект «Одно доброе слово»</b>\n\n"
        "Здесь — всё о самом проекте: уличные баннеры, отчёты, голосование, поддержка и сайт.\n\n"
        "Основные функции бота остаются на главном экране.",
        parse_mode="HTML", reply_markup=project_hub_keyboard())

@bot.callback_query_handler(func=lambda c: c.data.startswith("hub_"))
def project_hub_callback(c):
    bot.answer_callback_query(c.id)
    action = c.data[4:]
    if action == "donate": donate(c.message)
    elif action == "banners": show_banner(c.message.chat.id, 0)
    elif action == "vote": send_vote(c.message.chat.id)
    elif action == "reports": show_report(c.message.chat.id, 0)
    elif action == "phrase":
        waiting_for_phrase.add(c.message.chat.id)
        bot.send_message(c.message.chat.id, "✍️ <b>Предложить свою фразу</b>\n\nНапишите одним сообщением фразу, которую вы хотели бы увидеть на улицах города ❤️\n\nОтмена: /cancel", parse_mode="HTML")
    elif action == "next":
        kb = types.InlineKeyboardMarkup(); kb.add(types.InlineKeyboardButton("❤️ Помочь разместить", url=DONATE_URL)); kb.add(types.InlineKeyboardButton("🗳 Выбрать фразу", callback_data="open_vote"))
        bot.send_message(c.message.chat.id, "🎯 <b>Следующий баннер</b>\n\nМы готовим следующий уличный баннер проекта. Вы можете помочь с размещением или принять участие в выборе фразы ❤️", parse_mode="HTML", reply_markup=kb)

# Анонимная поддержка: пользователь может выговориться без показа профиля администратору.
def anon_records():
    return load_json_list(ANON_FILE)

def save_anon_records(data):
    save_json_list(ANON_FILE, data)

def anon_menu():
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("✍️ Написать анонимно", callback_data="anon_write"))
    kb.add(types.InlineKeyboardButton("🚨 Мне нужна срочная помощь", callback_data="anon_emergency"))
    return kb

@bot.message_handler(func=lambda m: m.text == "🫂 Мне нужно выговориться")
def anonymous_support(message):
    remember_user(message)
    bot.send_message(
        message.chat.id,
        "🫂 <b>Здесь можно выговориться</b>\n\n"
        "Иногда важно просто сказать то, что тяжело держать в себе. Напишите одним сообщением — без осуждения. ❤️\n\n"
        "Администратору не показываются ваше имя, username или ссылка на профиль. "
        "Чтобы бот мог доставить вам возможный ответ, Telegram ID технически сохраняется внутри бота и не выводится администратору.\n\n"
        "Это не экстренная и не медицинская служба.",
        parse_mode="HTML", reply_markup=anon_menu())

@bot.callback_query_handler(func=lambda c: c.data == "anon_write")
def anon_write_start(c):
    bot.answer_callback_query(c.id)
    waiting_for_anonymous.add(c.message.chat.id)
    bot.send_message(c.message.chat.id,
        "✍️ <b>Напишите всё, что хочется сказать.</b>\n\n"
        "Сообщение может быть до 3500 символов. Для отмены отправьте /cancel.",
        parse_mode="HTML")

@bot.callback_query_handler(func=lambda c: c.data == "anon_emergency")
def anon_emergency(c):
    bot.answer_callback_query(c.id)
    bot.send_message(c.message.chat.id,
        "🚨 <b>Если вам или кому-то рядом прямо сейчас угрожает опасность</b>, "
        "обратитесь в местную экстренную службу или к человеку, который может физически быть рядом. "
        "Во многих странах единый номер экстренной помощи — <b>112</b>.\n\n"
        "Если непосредственной опасности нет, вы всё равно можете написать сюда и выговориться. ❤️",
        parse_mode="HTML", reply_markup=anon_menu())

@bot.message_handler(func=lambda m: m.chat.id in waiting_for_anonymous, content_types=["text"])
def receive_anonymous(m):
    if (m.text or "").strip() == "/cancel":
        waiting_for_anonymous.discard(m.chat.id)
        bot.send_message(m.chat.id, "Отменено ❤️", reply_markup=keyboard())
        return
    text = (m.text or "").strip()
    if not text or len(text) > 3500:
        bot.send_message(m.chat.id, "Сообщение должно содержать от 1 до 3500 символов. Попробуйте ещё раз или отправьте /cancel.")
        return
    waiting_for_anonymous.discard(m.chat.id)
    data = anon_records()
    next_id = max([int(x.get("anon_id", 0)) for x in data] or [0]) + 1
    rec = {"anon_id": next_id, "user_id": m.from_user.id, "chat_id": m.chat.id,
           "text": text, "created": datetime.utcnow().isoformat(timespec="seconds") + "Z", "replied": False}
    data.append(rec)
    if len(data) > 1000:
        data = data[-1000:]
    save_anon_records(data)
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("💬 Ответить анонимно", callback_data=f"anonreply_{next_id}"))
    bot.send_message(ADMIN_ID,
        f"🫂 <b>Новое анонимное сообщение #{next_id}</b>\n\n{html.escape(text)}\n\n"
        "Личные данные отправителя не отображаются.",
        parse_mode="HTML", reply_markup=kb)
    bot.send_message(m.chat.id,
        "❤️ <b>Сообщение отправлено анонимно.</b>\n\nСпасибо, что поделились. Если администратор ответит, ответ придёт сюда через бота.",
        parse_mode="HTML", reply_markup=keyboard())

@bot.callback_query_handler(func=lambda c: c.data.startswith("anonreply_"))
def anon_reply_start(c):
    if c.from_user.id != ADMIN_ID:
        return bot.answer_callback_query(c.id, "Недоступно", show_alert=True)
    try:
        anon_id = int(c.data.split("_", 1)[1])
    except Exception:
        return bot.answer_callback_query(c.id, "Ошибка")
    rec = next((x for x in anon_records() if int(x.get("anon_id", 0)) == anon_id), None)
    if not rec:
        return bot.answer_callback_query(c.id, "Сообщение не найдено", show_alert=True)
    admin_anon_reply[ADMIN_ID] = anon_id
    bot.answer_callback_query(c.id)
    bot.send_message(ADMIN_ID,
        f"💬 Напишите ответ для анонимного сообщения #{anon_id}.\n\n"
        "Пользователь получит только текст ответа от проекта. Для отмены: /cancel")

@bot.message_handler(func=lambda m: m.from_user and m.from_user.id == ADMIN_ID and ADMIN_ID in admin_anon_reply, content_types=["text"])
def anon_reply_send(m):
    if (m.text or "").strip() == "/cancel":
        admin_anon_reply.pop(ADMIN_ID, None)
        bot.send_message(ADMIN_ID, "Ответ отменён.", reply_markup=admin_menu())
        return
    anon_id = admin_anon_reply.pop(ADMIN_ID)
    data = anon_records()
    rec = next((x for x in data if int(x.get("anon_id", 0)) == anon_id), None)
    if not rec:
        bot.send_message(ADMIN_ID, "Сообщение не найдено.")
        return
    answer = (m.text or "").strip()
    if not answer:
        bot.send_message(ADMIN_ID, "Пустой ответ не отправлен.")
        return
    try:
        bot.send_message(int(rec["chat_id"]),
            "💌 <b>Вам пришёл ответ</b>\n\n" + html.escape(answer) +
            "\n\n❤️ «Одно доброе слово»",
            parse_mode="HTML", reply_markup=keyboard())
        rec["replied"] = True
        rec["reply_time"] = datetime.utcnow().isoformat(timespec="seconds") + "Z"
        save_anon_records(data)
        bot.send_message(ADMIN_ID, f"✅ Ответ на сообщение #{anon_id} отправлен анонимно.", reply_markup=admin_menu())
    except Exception:
        bot.send_message(ADMIN_ID, "❌ Не удалось доставить ответ пользователю.", reply_markup=admin_menu())

@bot.message_handler(commands=["help"])
def help_command(message):
    remember_user(message)
    bot.send_message(message.chat.id,
        "❤️ <b>Помощь</b>\n\n"
        "Главное здесь — живые добрые слова между людьми, возможность выговориться и ежедневная поддержка.\n"
        "Проектные разделы собраны внутри кнопки «❤️ Одно доброе слово».",
        parse_mode="HTML",reply_markup=keyboard())

# 🌱 Личные маленькие шаги, письма и личное пространство

def _step_records():
    return load_json_list(STEPS_FILE)

def _save_steps(data):
    save_json_list(STEPS_FILE, data)

def _user_steps(uid):
    return [x for x in _step_records() if x.get("user_id") == uid]

def _step_streak(uid):
    dates = sorted({x.get("completed_date") for x in _user_steps(uid) if x.get("status") == "done" and x.get("completed_date")}, reverse=True)
    if not dates:
        return 0
    try:
        parsed = [datetime.strptime(x, "%Y-%m-%d").date() for x in dates]
    except Exception:
        return 0
    streak = 1
    for a, b in zip(parsed, parsed[1:]):
        if (a - b).days == 1:
            streak += 1
        else:
            break
    return streak

@bot.message_handler(func=lambda m: m.text == "🌱 Мой маленький шаг")
def small_step_menu(message):
    remember_user(message)
    active = next((x for x in reversed(_user_steps(message.from_user.id)) if x.get("status") == "active"), None)
    kb = types.InlineKeyboardMarkup()
    if active:
        kb.row(types.InlineKeyboardButton("✅ Получилось", callback_data=f"step_done_{active.get('id')}"),
               types.InlineKeyboardButton("🌿 Попробую ещё", callback_data=f"step_retry_{active.get('id')}"))
        kb.add(types.InlineKeyboardButton("➕ Новый маленький шаг", callback_data="step_new"))
        bot.send_message(message.chat.id, "🌱 <b>Твой маленький шаг</b>\n\n" + html.escape(active.get("text", "")) + "\n\nНе обязательно делать много. Иногда достаточно одного небольшого действия.", parse_mode="HTML", reply_markup=kb)
    else:
        kb.add(types.InlineKeyboardButton("✍️ Записать шаг", callback_data="step_new"))
        bot.send_message(message.chat.id, "🌱 <b>Мой маленький шаг</b>\n\nЗапиши одно небольшое действие, которое хочешь сделать для себя сегодня.\n\nНапример: выйти на прогулку, позвонить близкому, разобрать одну полку или просто вовремя лечь спать.", parse_mode="HTML", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data == "step_new")
def step_new(c):
    bot.answer_callback_query(c.id)
    waiting_for_step.add(c.message.chat.id)
    bot.send_message(c.message.chat.id, "🌱 Напиши свой маленький шаг одним сообщением.\n\nОтмена: /cancelstep")

@bot.message_handler(commands=["cancelstep"])
def cancel_step(m):
    waiting_for_step.discard(m.chat.id)
    bot.send_message(m.chat.id, "Отменено ❤️", reply_markup=keyboard())

@bot.message_handler(func=lambda m: m.chat.id in waiting_for_step, content_types=["text"])
def receive_step(m):
    if (m.text or "").startswith("/"):
        return
    waiting_for_step.discard(m.chat.id)
    text = (m.text or "").strip()
    if not text or len(text) > 300:
        bot.send_message(m.chat.id, "Шаг должен быть текстом до 300 символов.", reply_markup=keyboard())
        return
    data = _step_records()
    for x in data:
        if x.get("user_id") == m.from_user.id and x.get("status") == "active":
            x["status"] = "replaced"
    sid = int(time.time() * 1000)
    data.append({"id": sid, "user_id": m.from_user.id, "chat_id": m.chat.id, "text": text, "status": "active", "created": datetime.utcnow().isoformat(timespec="seconds")})
    _save_steps(data)
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("✅ Отметить выполненным", callback_data=f"step_done_{sid}"))
    bot.send_message(m.chat.id, "🌱 <b>Шаг записан.</b>\n\n" + html.escape(text) + "\n\nКогда сделаешь — просто отметь это. ❤️", parse_mode="HTML", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith(("step_done_", "step_retry_")))
def step_action(c):
    bot.answer_callback_query(c.id)
    try: sid = int(c.data.rsplit("_", 1)[1])
    except Exception: return
    data = _step_records()
    rec = next((x for x in data if x.get("id") == sid and x.get("user_id") == c.from_user.id), None)
    if not rec:
        bot.send_message(c.message.chat.id, "Этот шаг уже недоступен.")
        return
    if c.data.startswith("step_done_"):
        rec["status"] = "done"
        rec["completed_date"] = datetime.utcnow().strftime("%Y-%m-%d")
        rec["completed"] = datetime.utcnow().isoformat(timespec="seconds")
        _save_steps(data)
        streak = _step_streak(c.from_user.id)
        bot.send_message(c.message.chat.id, f"❤️ <b>Получилось.</b>\n\nДаже небольшой шаг имеет значение.\n\n🔥 Текущая серия: <b>{streak}</b> дн.", parse_mode="HTML", reply_markup=keyboard())
    else:
        rec["status"] = "retry"
        _save_steps(data)
        waiting_for_step.add(c.message.chat.id)
        bot.send_message(c.message.chat.id, "🌿 Ничего страшного. Можно выбрать шаг поменьше или попробовать ещё раз.\n\nНапиши новый маленький шаг:")

@bot.message_handler(func=lambda m: m.text == "🌙 Письмо в тишину")
def private_letter_menu(message):
    remember_user(message)
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("✍️ Написать письмо", callback_data="letter_new"))
    bot.send_message(message.chat.id, "🌙 <b>Письмо в тишину</b>\n\nЗдесь можно написать слова, которые не хочется или невозможно отправить человеку.\n\nПосле написания ты сам решишь: <b>отпустить их</b> или попросить бота <b>вернуть письмо позже</b>.\n\nЕсли выберешь «Отпустить», текст не будет сохраняться.", parse_mode="HTML", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data == "letter_new")
def letter_new(c):
    bot.answer_callback_query(c.id)
    waiting_for_letter.add(c.message.chat.id)
    bot.send_message(c.message.chat.id, "🌙 Напиши всё, что хочется сказать. До 4000 символов.\n\nОтмена: /cancelletter")

@bot.message_handler(commands=["cancelletter"])
def cancel_letter(m):
    waiting_for_letter.discard(m.chat.id)
    pending_letters.pop(m.chat.id, None)
    bot.send_message(m.chat.id, "Письмо отменено ❤️", reply_markup=keyboard())

@bot.message_handler(func=lambda m: m.chat.id in waiting_for_letter, content_types=["text"])
def receive_letter(m):
    if (m.text or "").startswith("/"):
        return
    waiting_for_letter.discard(m.chat.id)
    text = (m.text or "").strip()
    if not text or len(text) > 4000:
        bot.send_message(m.chat.id, "Письмо должно быть до 4000 символов.", reply_markup=keyboard())
        return
    pending_letters[m.chat.id] = text
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🗑 Отпустить и не сохранять", callback_data="letter_release"))
    kb.row(types.InlineKeyboardButton("⏳ Через 1 день", callback_data="letter_1"), types.InlineKeyboardButton("7 дней", callback_data="letter_7"))
    kb.add(types.InlineKeyboardButton("30 дней", callback_data="letter_30"))
    bot.send_message(m.chat.id, "🌙 <b>Письмо написано.</b>\n\nЧто сделать с этими словами?", parse_mode="HTML", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data == "letter_release" or c.data.startswith("letter_"))
def letter_action(c):
    bot.answer_callback_query(c.id)
    text = pending_letters.pop(c.message.chat.id, None)
    if not text:
        bot.send_message(c.message.chat.id, "Это письмо уже обработано.", reply_markup=keyboard())
        return
    if c.data == "letter_release":
        bot.send_message(c.message.chat.id, "🕊 <b>Отпущено.</b>\n\nТекст не сохранён. Иногда уже само написание помогает поставить точку или хотя бы запятую. ❤️", parse_mode="HTML", reply_markup=keyboard())
        return
    try: days = int(c.data.split("_", 1)[1])
    except Exception: days = 7
    from datetime import timedelta
    due = datetime.utcnow() + timedelta(days=days)
    letters = load_json_list(LETTERS_FILE)
    letters.append({"user_id": c.from_user.id, "chat_id": c.message.chat.id, "text": text, "created": datetime.utcnow().isoformat(timespec="seconds"), "due": due.isoformat(timespec="seconds"), "status": "waiting"})
    save_json_list(LETTERS_FILE, letters)
    bot.send_message(c.message.chat.id, f"⏳ Хорошо. Я верну тебе это письмо через <b>{days}</b> дн.\n\nДо этого момента оно хранится только для доставки обратно в этот чат.", parse_mode="HTML", reply_markup=keyboard())

# 📍 Карта добра — пользователь добровольно указывает только название города.
def city_records():
    return load_json_list(CITIES_FILE)

def save_city_records(data):
    save_json_list(CITIES_FILE, data)

def normalize_city_name(value):
    value = " ".join((value or "").strip().split())
    if not value or len(value) > 80:
        return None
    if any(ch.isdigit() for ch in value):
        return None
    allowed_extra = " -–—.'’()"
    if any(not (ch.isalpha() or ch in allowed_extra) for ch in value):
        return None
    return value.title()

def city_aggregates():
    latest = {}
    for row in city_records():
        uid = row.get("user_id")
        city = normalize_city_name(row.get("city"))
        if uid is not None and city:
            latest[str(uid)] = city
    counts = {}
    for city in latest.values():
        counts[city] = counts.get(city, 0) + 1
    return sorted(({"city": city, "people": count} for city, count in counts.items()), key=lambda x: (-x["people"], x["city"]))

def city_map_text():
    cities = city_aggregates()
    total_people = sum(x["people"] for x in cities)
    top = "\n".join(f"• {html.escape(x['city'])} — <b>{x['people']}</b>" for x in cities[:10]) if cities else "• Пока ни одного города. Можно стать первым ❤️"
    return ("📍 <b>Карта добра</b>\n\n"
            "Здесь отмечаются только города, которые пользователи указали добровольно. "
            "Точные координаты, адреса, имена и username не собираются для карты.\n\n"
            f"🌍 Городов в карте: <b>{len(cities)}</b>\n"
            f"❤️ Участников на карте: <b>{total_people}</b>\n\n"
            "<b>Города добра</b>\n" + top)

def city_map_keyboard():
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("❤️ Добавить или изменить мой город", callback_data="city_add"))
    kb.add(types.InlineKeyboardButton("🔄 Обновить карту", callback_data="city_refresh"))
    return kb

@bot.message_handler(func=lambda m: m.text == "📍 Карта добра")
def city_map_menu(message):
    remember_user(message)
    bot.send_message(message.chat.id, city_map_text(), parse_mode="HTML", reply_markup=city_map_keyboard())

@bot.callback_query_handler(func=lambda c: c.data == "city_add")
def city_add_start(c):
    bot.answer_callback_query(c.id)
    waiting_for_city.add(c.message.chat.id)
    bot.send_message(c.message.chat.id,
        "📍 <b>Напишите только название вашего города.</b>\n\nНапример: Москва, Казань, Aachen.\n"
        "Не отправляйте адрес, улицу или геолокацию. Отмена: /cancel", parse_mode="HTML")

@bot.message_handler(func=lambda m: m.chat.id in waiting_for_city, content_types=["text"])
def city_add_save(m):
    if (m.text or "").strip() == "/cancel":
        waiting_for_city.discard(m.chat.id)
        bot.send_message(m.chat.id, "Отменено ❤️", reply_markup=keyboard())
        return
    city = normalize_city_name(m.text)
    if not city:
        bot.send_message(m.chat.id, "Укажите только название города без адреса и цифр. Например: Москва. Или /cancel")
        return
    waiting_for_city.discard(m.chat.id)
    data = city_records()
    data = [x for x in data if str(x.get("user_id")) != str(m.from_user.id)]
    data.append({"user_id": m.from_user.id, "city": city, "updated": datetime.utcnow().isoformat(timespec="seconds") + "Z"})
    save_city_records(data)
    bot.send_message(m.chat.id, f"❤️ <b>{html.escape(city)}</b> появился на Карте добра.\n\nПублично показывается только город и общее число участников.", parse_mode="HTML", reply_markup=city_map_keyboard())

@bot.callback_query_handler(func=lambda c: c.data == "city_refresh")
def city_refresh(c):
    bot.answer_callback_query(c.id, "Карта обновлена ❤️")
    try:
        bot.edit_message_text(city_map_text(), c.message.chat.id, c.message.message_id, parse_mode="HTML", reply_markup=city_map_keyboard())
    except Exception:
        pass



# 🌍 Живая сеть добра 1.0
# Публично используются только агрегированные города и счётчики. Telegram ID нужны
# внутри бота для защиты от повторных голосов/доставок и наружу через API не отдаются.
def network_records():
    return load_json_list(NETWORK_FILE)

def save_network_records(data):
    save_json_list(NETWORK_FILE, data[-10000:])

def _city_for_user(uid):
    for x in city_records():
        if str(x.get("user_id")) == str(uid):
            return x.get("city") or None
    return None

def record_network_hop(kindness_record, receiver_uid):
    sender_city = _city_for_user(kindness_record.get("user_id"))
    receiver_city = _city_for_user(receiver_uid)
    data = network_records()
    data.append({
        "chain_id": int(kindness_record.get("chain_id") or kindness_record.get("id") or 0),
        "from_city": sender_city,
        "to_city": receiver_city,
        "created": datetime.utcnow().isoformat(timespec="seconds") + "Z"
    })
    save_network_records(data)

def network_chains_public(limit=8):
    grouped = {}
    for x in network_records():
        cid = str(x.get("chain_id") or "")
        if not cid: continue
        g = grouped.setdefault(cid, {"chain_id": cid, "hops": 0, "cities": [], "last": ""})
        g["hops"] += 1
        for c in (x.get("from_city"), x.get("to_city")):
            if c and c not in g["cities"]: g["cities"].append(c)
        g["last"] = max(g["last"], str(x.get("created") or ""))
    rows = sorted(grouped.values(), key=lambda x: (x["hops"], x["last"]), reverse=True)
    return [{"chain_id": x["chain_id"], "people": x["hops"] + 1,
             "cities": x["cities"][:8], "city_count": len(x["cities"])} for x in rows[:limit]]

def network_summary():
    hops = network_records()
    chains = network_chains_public(limit=10000)
    today = datetime.utcnow().strftime("%Y-%m-%d")
    return {
        "chains": len({str(x.get("chain_id")) for x in hops if x.get("chain_id") is not None}),
        "hops": len(hops),
        "hops_today": sum(1 for x in hops if str(x.get("created", "")).startswith(today)),
        "longest_chain": max([x.get("people", 0) for x in chains] or [0]),
    }

def load_city_vote():
    try:
        with open(CITY_VOTE_FILE, "r", encoding="utf-8") as f: return json.load(f)
    except Exception: return {"votes": {}}

def save_city_vote(data):
    try:
        with open(CITY_VOTE_FILE, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception: pass

def city_vote_results():
    data = load_city_vote(); counts = {}
    for city in data.get("votes", {}).values(): counts[city] = counts.get(city, 0) + 1
    return [{"city": city, "votes": n} for city, n in sorted(counts.items(), key=lambda x: (-x[1], x[0]))]

def city_vote_keyboard():
    kb = types.InlineKeyboardMarkup(row_width=2)
    cities = [x["city"] for x in city_aggregates()[:10]]
    for i in range(0, len(cities), 2):
        kb.row(*[types.InlineKeyboardButton("📍 " + c, callback_data="netvote_" + str(cities.index(c))) for c in cities[i:i+2]])
    kb.add(types.InlineKeyboardButton("📊 Результаты", callback_data="netvote_results"))
    return kb, cities

def city_vote_text():
    rows = city_vote_results()
    if not rows: return "🗳 <b>Следующий город для баннера</b>\n\nПока голосов нет. Выберите город ниже ❤️"
    return "🗳 <b>Следующий город для баннера</b>\n\n" + "\n".join(f"{i+1}. {html.escape(x['city'])} — <b>{x['votes']}</b>" for i,x in enumerate(rows[:10]))

@bot.callback_query_handler(func=lambda c: c.data.startswith("netvote_"))
def network_city_vote(c):
    if c.data == "netvote_results":
        bot.answer_callback_query(c.id); kb,_=city_vote_keyboard(); bot.send_message(c.message.chat.id, city_vote_text(), parse_mode="HTML", reply_markup=kb); return
    kb,cities = city_vote_keyboard()
    try: idx=int(c.data.split("_")[-1]); city=cities[idx]
    except Exception: bot.answer_callback_query(c.id, "Город уже изменился — откройте голосование снова.", show_alert=True); return
    data=load_city_vote(); data.setdefault("votes", {})[str(c.from_user.id)] = city; save_city_vote(data)
    bot.answer_callback_query(c.id, "❤️ Голос за «"+city+"» учтён!")

def project_goal():
    try:
        with open(PROJECT_GOAL_FILE, "r", encoding="utf-8") as f: return json.load(f)
    except Exception: return {"title":"Первый реальный баннер", "raised":0, "target":50000}

def save_project_goal(data):
    try:
        with open(PROJECT_GOAL_FILE, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception: pass

@bot.message_handler(commands=["setgoal"])
def set_project_goal(m):
    if m.from_user.id != ADMIN_ID: return
    try:
        parts=(m.text or "").split(); raised=max(0,int(parts[1])); target=max(1,int(parts[2])); title=" ".join(parts[3:]).strip() or "Следующий баннер"
        save_project_goal({"title":title,"raised":raised,"target":target})
        bot.send_message(m.chat.id, f"✅ Цель обновлена: {raised:,} / {target:,} ₽\n{html.escape(title)}", parse_mode="HTML")
    except Exception:
        bot.send_message(m.chat.id, "Формат: /setgoal 12500 50000 Первый баннер")

def collective_achievements():
    cities=len(city_aggregates()); words=len(kindness_records()); deliveries=sum(len(set(x.get("delivered_to",[]) or [])) for x in kindness_records()); banners=len(banners_data)
    milestones=[(cities>=1,"📍 Первый город в сети"),(cities>=10,"🌍 10 городов добра"),(words>=100,"💌 100 добрых слов"),(words>=1000,"❤️ 1 000 добрых слов"),(deliveries>=100,"🤲 100 полученных слов"),(banners>=1,"🏙️ Первый реальный баннер"),(banners>=5,"✨ 5 реальных баннеров")]
    return [name for ok,name in milestones if ok]

def network_text():
    ns=network_summary(); cities=city_aggregates(); chains=network_chains_public(5); votes=city_vote_results(); goal=project_goal()
    chain_lines=[]
    for x in chains:
        path=" → ".join(x["cities"]) if x["cities"] else "города пока не указаны"
        chain_lines.append(f"• Цепочка №{x['chain_id']}: <b>{x['people']}</b> чел. · {html.escape(path)}")
    ach=collective_achievements()
    return ("🌍 <b>Живая сеть добра</b>\n\n"
            f"📍 Городов: <b>{len(cities)}</b>\n💌 Активных цепочек: <b>{ns['chains']}</b>\n🔗 Передач между людьми: <b>{ns['hops']}</b>\n🔥 Самая длинная цепочка: <b>{ns['longest_chain']}</b> чел.\n\n"
            "<b>Живые цепочки</b>\n" + ("\n".join(chain_lines) if chain_lines else "• Первая цепочка появится после передачи слова ❤️") +
            "\n\n🏆 <b>Общие достижения</b>\n" + ("\n".join("• "+x for x in ach) if ach else "• Первое достижение ещё впереди") +
            f"\n\n🎯 <b>{html.escape(str(goal.get('title','Следующий баннер')))}</b>\n{int(goal.get('raised',0)):,} / {int(goal.get('target',50000)):,} ₽")

def network_keyboard():
    kb=types.InlineKeyboardMarkup(row_width=2)
    kb.row(types.InlineKeyboardButton("💌 Передать добро", callback_data="kindness_write"), types.InlineKeyboardButton("❤️ Получить", callback_data="kindness_receive"))
    kb.row(types.InlineKeyboardButton("🗳 Город баннера", callback_data="network_vote_open"), types.InlineKeyboardButton("📍 Мой город", callback_data="city_add"))
    kb.row(types.InlineKeyboardButton("❤️ Поддержать баннер", url=DONATE_URL), types.InlineKeyboardButton("🌐 Открыть сайт", url=SITE_URL))
    return kb

@bot.message_handler(func=lambda m: m.text == "🌍 Живая сеть добра")
def network_menu(m):
    remember_user(m); bot.send_message(m.chat.id, network_text(), parse_mode="HTML", reply_markup=network_keyboard())

@bot.callback_query_handler(func=lambda c: c.data == "network_vote_open")
def network_vote_open(c):
    bot.answer_callback_query(c.id); kb,_=city_vote_keyboard(); bot.send_message(c.message.chat.id, city_vote_text(), parse_mode="HTML", reply_markup=kb)


# 🌍 Живое сообщество добра — только агрегированная анонимная статистика.
def _parse_iso_dt(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).replace(tzinfo=None)
    except Exception:
        return None

def live_kindness_stats():
    kindness = kindness_records()
    steps = _step_records()
    today = datetime.utcnow().strftime("%Y-%m-%d")

    sent_today = sum(1 for x in kindness if str(x.get("created", "")).startswith(today))
    steps_today = sum(1 for x in steps if x.get("status") == "done" and x.get("completed_date") == today)

    participants = set()
    for x in kindness:
        uid = x.get("user_id")
        if uid is not None:
            participants.add(str(uid))
        for receiver in x.get("delivered_to", []) or []:
            participants.add(str(receiver))

    deliveries = sum(len(set(x.get("delivered_to", []) or [])) for x in kindness)
    return {
        "sent_today": sent_today,
        "steps_today": steps_today,
        "participants": len(participants),
        "total_words": len(kindness),
        "deliveries": deliveries,
        "mission_today_completed": daily_mission_count(),
        "mission_today_text": daily_mission_text(),
    }

def live_activity_lines(limit=5):
    items = []
    for x in kindness_records():
        created = _parse_iso_dt(x.get("created"))
        if created:
            items.append((created, "💌 Кто-то передал доброе слово"))
    for x in _step_records():
        if x.get("status") != "done":
            continue
        completed = _parse_iso_dt(x.get("completed"))
        if completed:
            items.append((completed, "🌱 Кто-то выполнил маленький шаг"))
    for x in daily_mission_records():
        completed = _parse_iso_dt(x.get("completed"))
        if completed:
            items.append((completed, "✨ Кто-то выполнил добро дня"))
    items.sort(key=lambda item: item[0], reverse=True)
    return [text for _, text in items[:limit]]

def live_community_keyboard():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.row(types.InlineKeyboardButton("🔄 Обновить", callback_data="live_refresh"),
           types.InlineKeyboardButton("💌 Передать добро", callback_data="kindness_write"))
    kb.add(types.InlineKeyboardButton("❤️ Получить доброе слово", callback_data="kindness_receive"))
    return kb

def live_community_text():
    stats = live_kindness_stats()
    activity = live_activity_lines()
    recent = "\n".join("• " + x for x in activity) if activity else "• Здесь скоро появятся первые добрые события ❤️"
    return (
        "🌍 <b>Добро прямо сейчас</b>\n\n"
        "Здесь нет имён, профилей и рейтинга людей — только реальные анонимные действия сообщества.\n\n"
        f"💌 Добрых слов передано сегодня: <b>{stats['sent_today']}</b>\n"
        f"🌱 Маленьких шагов выполнено сегодня: <b>{stats['steps_today']}</b>\n"
        f"❤️ Людей в цепочке добра: <b>{stats['participants']}</b>\n"
        f"✉️ Всего слов в цепочке: <b>{stats['total_words']}</b>\n"
        f"🤲 Получений добрых слов: <b>{stats['deliveries']}</b>\n\n"
        "✨ <b>Последние события</b>\n" + recent +
        "\n\nКаждое число здесь складывается из настоящих действий пользователей бота."
    )

# Публичный API для сайта. Возвращает только агрегированную статистику и
# обезличенные типы событий — без Telegram ID, имён, username и текстов сообщений.
def public_stats_payload():
    stats = live_kindness_stats()
    cities = city_aggregates()
    return {
        "project": "Одно доброе слово",
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "stats": stats,
        "activity": live_activity_lines(limit=5),
        "cities": cities,
        "city_stats": {"cities": len(cities), "participants": sum(x["people"] for x in cities)},
        "network": network_summary(),
        "chains": network_chains_public(limit=8),
        "city_vote": city_vote_results()[:10],
        "collective_achievements": collective_achievements(),
        "goal": project_goal(),
        "placements": [{"city": x.get("city", ""), "date": x.get("date", ""), "phrase": x.get("phrase", "")} for x in banners_data[-12:]],
    }

# Магазин: журнал заявок хранится на диске Railway. Для постоянного хранения
# подключите volume или внешнюю БД. Без этого записи могут пропасть при redeploy.
SHOP_FILE = os.environ.get("SHOP_ORDERS_FILE", "shop_orders.json")
SHOP_LOCK = threading.RLock()
SHOP_STATUSES = {"new": "Новый", "work": "В работе", "sent": "Отправлен", "done": "Завершён", "cancel": "Отменён"}

def shop_load():
    try:
        with open(SHOP_FILE, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (OSError, ValueError):
        return []

def shop_save(items):
    temp = SHOP_FILE + ".tmp"
    with open(temp, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    os.replace(temp, SHOP_FILE)

def shop_buttons(order_id):
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    for key, label in SHOP_STATUSES.items():
        keyboard.add(types.InlineKeyboardButton(label, callback_data="shopstatus:" + key + ":" + order_id))
    return keyboard

@bot.callback_query_handler(func=lambda c: c.data.startswith("shopstatus:"))
def shop_change_status(c):
    if not c.from_user or c.from_user.id != ADMIN_ID:
        bot.answer_callback_query(c.id, "Недоступно")
        return
    try:
        _, status, order_id = c.data.split(":", 2)
        if status not in SHOP_STATUSES:
            raise ValueError()
        with SHOP_LOCK:
            items = shop_load()
            order = next((x for x in items if x.get("id") == order_id), None)
            if not order:
                bot.answer_callback_query(c.id, "Заказ не найден в журнале")
                return
            order["status"] = status
            shop_save(items)
        bot.answer_callback_query(c.id, "Статус: " + SHOP_STATUSES[status])
        bot.send_message(ADMIN_ID, "📦 Заказ " + order_id + " → " + SHOP_STATUSES[status])
    except Exception:
        bot.answer_callback_query(c.id, "Не удалось обновить")

@bot.message_handler(commands=["shopstats", "shoporders"])
def shop_admin_commands(m):
    if not m.from_user or m.from_user.id != ADMIN_ID:
        return
    with SHOP_LOCK:
        items = shop_load()
    if m.text.startswith("/shopstats"):
        total = sum(int(x.get("total", 0)) for x in items if x.get("status") != "cancel")
        statuses = "\n".join(f"{label}: {sum(x.get('status') == key for x in items)}" for key, label in SHOP_STATUSES.items())
        bot.send_message(m.chat.id, f"📊 Заявок: {len(items)}\nПотенциальная сумма (не выручка): {total:,} ₽\n\n{statuses}")
    else:
        recent = items[-10:][::-1]
        lines = [f"{x['id']} — {SHOP_STATUSES.get(x.get('status'), '—')} — {x.get('total', 0)} ₽" for x in recent]
        bot.send_message(m.chat.id, "📦 Последние заявки:\n" + ("\n".join(lines) if lines else "Пока нет"))

class PublicStatsHandler(BaseHTTPRequestHandler):
    def _send_json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", SITE_URL)
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json_body(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 65536:
                return {}
            return json.loads(self.rfile.read(length).decode("utf-8"))
        except Exception:
            return {}

    def _session_uid(self):
        value = self.headers.get("Authorization", "")
        if not value.startswith("Bearer "):
            return None
        return cabinet_check_session(value[7:].strip())

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", SITE_URL)
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def _shop_admin_ok(self):
        return self._session_uid() == ADMIN_ID and self.headers.get("Origin") == SITE_URL

    def do_POST(self):
        path = urlparse(self.path).path.rstrip("/") or "/"
        if path == "/api/admin/shop/status":
            if not self._shop_admin_ok():
                self._send_json(403, {"ok": False, "error": "forbidden"})
                return
            data = self._json_body()
            if not isinstance(data, dict):
                self._send_json(400, {"ok": False})
                return
            order_id = str(data.get("order_id", ""))
            status = str(data.get("status", ""))
            if status not in SHOP_STATUSES:
                self._send_json(400, {"ok": False, "error": "bad_status"})
                return
            with SHOP_LOCK:
                items = shop_load()
                order = next((x for x in items if x.get("id") == order_id), None)
                if order is None:
                    self._send_json(404, {"ok": False, "error": "not_found"})
                    return
                order["status"] = status
                try:
                    shop_save(items)
                except OSError:
                    self._send_json(503, {"ok": False, "error": "storage_error"})
                    return
            self._send_json(200, {"ok": True})
            return
        if path == "/api/shop/order":
            # Only accept requests from the project's website (browser origin check).
            if self.headers.get("Origin") != SITE_URL:
                self._send_json(403, {"ok": False, "error": "origin_not_allowed"})
                return
            # Require JSON and bound request size in _json_body.
            if "application/json" not in self.headers.get("Content-Type", ""):
                self._send_json(415, {"ok": False, "error": "json_required"})
                return
            data = self._json_body()
            if not isinstance(data, dict):
                self._send_json(400, {"ok": False, "error": "invalid_data"})
                return
            # A hidden honeypot helps filter unsophisticated spam.
            if data.get("website"):
                self._send_json(200, {"ok": True})
                return
            name = str(data.get("name", "")).strip()
            phone = str(data.get("phone", "")).strip()
            delivery = str(data.get("delivery", "")).strip()
            city = str(data.get("city", "")).strip()
            comment = str(data.get("comment", "")).strip()
            try:
                quantity = int(data.get("quantity", 0))
            except (ValueError, TypeError):
                quantity = 0
            allowed = ("СДЭК", "Почта России", "Самовывоз (бесплатно)")
            digits = ''.join(c for c in phone if c.isdigit())
            if (not 2 <= len(name) <= 80 or not 10 <= len(digits) <= 15
                or delivery not in allowed or not 1 <= quantity <= 20
                or len(comment) > 350 or (delivery != allowed[2] and not 2 <= len(city) <= 100)):
                self._send_json(400, {"ok": False, "error": "invalid_fields"})
                return
            if delivery == allowed[2]:
                city = "Ростов-на-Дону"
            order_id = "ODS-" + uuid.uuid4().hex[:10].upper()
            message = ("🛍 <b>НОВЫЙ ЗАКАЗ</b> " + html.escape(order_id) + "\n\n"
                       "🎁 Коробочка тепла\n"
                       "📦 Количество: " + str(quantity) + "\n"
                       "💰 Товары: " + str(quantity * 1990) + " ₽ (без доставки)\n"
                       "🚚 Получение: " + html.escape(delivery) + "\n"
                       "📍 Город: " + html.escape(city) + "\n"
                       "👤 Имя: " + html.escape(name) + "\n"
                       "📞 Телефон: " + html.escape(phone) + "\n"
                       "💬 Комментарий: " + html.escape(comment or "—") + "\n\n"
                       "⏳ Ожидает подтверждения. Оплата не проведена.")
            try:
                bot.send_message(ADMIN_ID, message, parse_mode="HTML", reply_markup=shop_buttons(order_id))
                with SHOP_LOCK:
                    items = shop_load()
                    items.append({"id": order_id, "created": datetime.utcnow().isoformat() + "Z", "status": "new", "name": name, "phone": phone, "delivery": delivery, "city": city, "comment": comment, "quantity": quantity, "total": quantity * 1990})
                    shop_save(items)
            except Exception as exc:
                print("Shop order delivery error:", type(exc).__name__)
                self._send_json(503, {"ok": False, "error": "delivery_failed"})
                return
            self._send_json(200, {"ok": True, "order_id": order_id})
            return
        if path == "/api/auth/telegram":
            data = self._json_body()
            uid = verify_telegram_login(data)
            if not uid:
                self._send_json(401, {"ok": False, "error": "telegram_auth_failed"})
                return
            user = next((x for x in users_data if str(x.get("id")) == str(uid)), None)
            if not user:
                self._send_json(403, {"ok": False, "error": "open_bot_first"})
                return
            self._send_json(200, {"ok": True, "token": cabinet_make_session(uid)})
        else:
            self._send_json(404, {"error": "not_found"})

    def do_GET(self):
        path = urlparse(self.path).path.rstrip("/") or "/"
        if path == "/api/admin/shop/orders":
            if not self._shop_admin_ok():
                self._send_json(403, {"ok": False, "error": "forbidden"})
                return
            with SHOP_LOCK:
                items = shop_load()
            total = sum(int(x.get("total", 0)) for x in items if x.get("status") != "cancel")
            self._send_json(200, {"ok": True, "orders": items[-300:][::-1],
                                  "stats": {"count": len(items), "amount": total,
                                            "new": sum(x.get("status") == "new" for x in items)}})
            return
        if path == "/api/shop/public":
            with SHOP_LOCK:
                items = shop_load()
            self._send_json(200, {"ok": True, "orders": len(items)})
        elif path == "/api/stats":
            self._send_json(200, public_stats_payload())
        elif path == "/api/me":
            uid = self._session_uid()
            if not uid:
                self._send_json(401, {"ok": False, "error": "unauthorized"})
            else:
                self._send_json(200, cabinet_profile_payload(uid))
        elif path in ("/", "/health"):
            self._send_json(200, {"ok": True, "service": "odno-dobroe-slovo", "version": BOT_VERSION})
        else:
            self._send_json(404, {"error": "not_found"})

    def log_message(self, format, *args):
        return

def run_public_api():
    port = int(os.environ.get("PORT", "8080"))
    server = ThreadingHTTPServer(("0.0.0.0", port), PublicStatsHandler)
    print(f"Public stats API started on port {port}")
    server.serve_forever()

@bot.message_handler(func=lambda m: m.text == "🌍 Добро прямо сейчас")
def live_community(message):
    remember_user(message)
    bot.send_message(message.chat.id, live_community_text(), parse_mode="HTML", reply_markup=live_community_keyboard())

@bot.callback_query_handler(func=lambda c: c.data == "live_refresh")
def live_community_refresh(c):
    bot.answer_callback_query(c.id, "Обновлено ❤️")
    try:
        bot.edit_message_text(live_community_text(), c.message.chat.id, c.message.message_id,
                              parse_mode="HTML", reply_markup=live_community_keyboard())
    except Exception:
        bot.send_message(c.message.chat.id, live_community_text(), parse_mode="HTML", reply_markup=live_community_keyboard())

@bot.message_handler(func=lambda m: m.text == "🏡 Моё пространство")
def my_space(message):
    remember_user(message)
    uid = message.from_user.id
    steps = _user_steps(uid)
    done = sum(1 for x in steps if x.get("status") == "done")
    streak = _step_streak(uid)
    kindness = load_json_list(KINDNESS_FILE)
    sent = sum(1 for x in kindness if x.get("user_id") == uid)
    received = sum(1 for x in kindness if uid in x.get("delivered_to", []))
    letters = load_json_list(LETTERS_FILE)
    waiting = sum(1 for x in letters if x.get("user_id") == uid and x.get("status") == "waiting")
    missions_done = sum(1 for x in daily_mission_records() if str(x.get("user_id")) == str(uid))
    current_level, next_level = kindness_level(sent)
    badges = achievement_lines(sent, received, done, streak)
    if missions_done >= 1: badges.append("🌅 Добро началось — выполнено первое добро дня")
    if missions_done >= 7: badges.append("✨ Неделя добра — выполнено 7 добрых миссий")
    if missions_done >= 30: badges.append("💛 Добрая привычка — выполнено 30 добрых миссий")
    if next_level:
        remaining = next_level[0] - sent
        progress = f"До уровня «{next_level[1]}» осталось передать <b>{remaining}</b>."
    else:
        progress = "Ты достиг самого высокого уровня добра. 💫"
    awards = "\n".join("• " + x for x in badges) if badges else "Пока наград нет — первая появится после первого переданного слова или выполненного шага."
    text = ("🏡 <b>Моё пространство</b>\n\n"
            f"🏆 Уровень: <b>{current_level[1]}</b>\n"
            f"{progress}\n\n"
            f"💌 Добрых слов передано: <b>{sent}</b>\n"
            f"❤️ Добрых слов получено: <b>{received}</b>\n"
            f"🌱 Маленьких шагов выполнено: <b>{done}</b>\n"
            f"🔥 Серия маленьких шагов: <b>{streak}</b> дн.\n"
            f"🌙 Писем ждут возвращения: <b>{waiting}</b>\n"
            f"🌅 Добрых миссий выполнено: <b>{missions_done}</b>\n\n"
            "🎖 <b>Мои достижения</b>\n" + awards +
            "\n\nЗдесь важны не рекорды, а добро, которое ты передаёшь дальше. ❤️")
    bot.send_message(message.chat.id, text, parse_mode="HTML", reply_markup=keyboard())

@bot.message_handler(func=lambda m: True)
def fallback(message):
    remember_user(message)
    start(message)

if __name__ == "__main__":
    threading.Thread(target=daily_worker, daemon=True).start()
    threading.Thread(target=run_public_api, daemon=True).start()
    print("Bot started")
    bot.infinity_polling(skip_pending=True, timeout=30, long_polling_timeout=30)
