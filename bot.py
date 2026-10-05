import os
import random
import telebot
from telebot import types

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
bot = telebot.TeleBot(TOKEN)

def keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("❤️ Поддержать проект", "💬 Доброе слово")
    kb.row("🌿 О проекте", "📸 Наши баннеры")
    kb.row("📊 Отчёты", "🌐 Наш сайт")
    return kb

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "❤️ <b>Одно доброе слово</b>\n\n"
        "А что, если одна фраза сможет изменить чей-то день?\n\n"
        "Мы размещаем на улицах баннеры с добрыми словами о надежде, "
        "любви, семье и ценности жизни.\n\n"
        "Выберите раздел 👇",
        parse_mode="HTML",
        reply_markup=keyboard(),
    )

@bot.message_handler(func=lambda m: m.text == "💬 Доброе слово")
def good_word(message):
    quotes = [
        "❤️ Ты справишься.",
        "🌿 Всё ещё впереди.",
        "❤️ Ты важен.",
        "☀️ После трудных дней обязательно становится светлее.",
        "🌱 Не сдавайся. Иногда до перемен остаётся всего один шаг.",
        "❤️ Цени тех, кто рядом.",
        "✨ Жизнь продолжается.",
        "❤️ Ты сильнее, чем тебе кажется.",
    ]
    bot.send_message(
        message.chat.id,
        f"<b>{random.choice(quotes)}</b>\n\nПусть эти слова сегодня будут именно для тебя. ❤️",
        parse_mode="HTML",
    )

@bot.message_handler(func=lambda m: m.text == "❤️ Поддержать проект")
def donate(message):
    donate_kb = types.InlineKeyboardMarkup()
    donate_kb.add(
        types.InlineKeyboardButton(
            "❤️ Пожертвовать",
            url="https://pro.selfwork.ru/to/02197162",
        )
    )
    bot.send_message(
        message.chat.id,
        "❤️ <b>Поддержать проект</b>\n\n"
        "Ваш вклад помогает оплачивать печать, аренду рекламных конструкций, "
        "монтаж и размещение первых баннеров.\n\n"
        "Сейчас собрано: <b>1 350 ₽ из 50 000 ₽</b>\n\n"
        "Нажмите кнопку ниже, чтобы поддержать проект ❤️",
        parse_mode="HTML",
        reply_markup=donate_kb,
    )

@bot.message_handler(func=lambda m: m.text == "🌿 О проекте")
def about(message):
    bot.send_message(
        message.chat.id,
        "🌿 <b>Одно доброе слово</b>\n\n"
        "Мы размещаем на улицах слова, которые ничего не продают:\n\n"
        "«Ты справишься»\n«Не сдавайся»\n«Ты важен»\n"
        "«Жизнь продолжается»\n«Цени тех, кто рядом»\n\n"
        "Иногда одна фраза может встретить человека именно тогда, "
        "когда она ему особенно нужна. ❤️",
        parse_mode="HTML",
    )

@bot.message_handler(func=lambda m: m.text == "📸 Наши баннеры")
def banners(message):
    bot.send_message(
        message.chat.id,
        "📸 <b>Наши баннеры</b>\n\n"
        "Здесь будут фотографии баннеров, которые появились на улицах "
        "благодаря вашей поддержке. ❤️",
        parse_mode="HTML",
    )

@bot.message_handler(func=lambda m: m.text == "📊 Отчёты")
def reports(message):
    bot.send_message(
        message.chat.id,
        "📊 <b>Отчёты проекта</b>\n\n"
        "Здесь будут публиковаться собранные средства, расходы на печать, "
        "аренду и монтаж, а также фотографии размещённых баннеров.",
        parse_mode="HTML",
    )

@bot.message_handler(func=lambda m: m.text == "🌐 Наш сайт")
def website(message):
    bot.send_message(
        message.chat.id,
        "🌐 <b>Сайт проекта:</b>\nhttps://odnodobroeslovo.ru",
        parse_mode="HTML",
    )

@bot.message_handler(func=lambda m: True)
def fallback(message):
    start(message)

if __name__ == "__main__":
    bot.infinity_polling(skip_pending=True, timeout=30, long_polling_timeout=30)
