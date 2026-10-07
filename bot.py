import os, random, html, json, threading, time, zipfile
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
VOTE_FILE = "vote.json"
REPORTS_FILE = "reports.json"
EVENTS_FILE = "events.json"
STARS_FILE = "stars_payments.json"
SUPPORT_EMAIL = "andrew2001520@icloud.com"
STAR_PACKS = [25, 50, 100, 250, 500]

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
    waiting_for_phrase.discard(message.chat.id); bot.send_message(message.chat.id, "Отменено ❤️", reply_markup=keyboard())

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

def stars_keyboard():
    kb = types.InlineKeyboardMarkup(row_width=2)
    buttons = [types.InlineKeyboardButton(f"⭐ {amount}", callback_data=f"stars_{amount}") for amount in STAR_PACKS]
    kb.add(*buttons)
    kb.add(types.InlineKeyboardButton("💳 Поддержать рублями", url=DONATE_URL))
    return kb

@bot.message_handler(func=lambda m: m.text == "❤️ Поддержать проект")
def donate(message):
    bot.send_message(
        message.chat.id,
        "❤️ <b>Поддержать проект</b>\n\n"
        "Ваш вклад помогает оплачивать печать, аренду рекламных конструкций, монтаж и размещение баннеров.\n\n"
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
    bot.send_message(message.chat.id, f"⭐ <b>Спасибо за поддержку!</b>\n\nПолучено: <b>{p.total_amount} ⭐</b>\nВаш вклад помогает проекту «Одно доброе слово» ❤️", parse_mode="HTML")
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
        backup_files=[SUBS_FILE,BANNERS_FILE,USERS_FILE,PHRASES_FILE,VOTE_FILE,REPORTS_FILE,EVENTS_FILE]
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
