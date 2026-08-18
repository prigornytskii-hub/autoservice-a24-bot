import os
import telebot
from telebot import types

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

bot = telebot.TeleBot(TOKEN)


def main_menu():
    keyboard = types.ReplyKeyboardMarkup(
        resize_keyboard=True,
        row_width=2
    )

    keyboard.add(
        types.KeyboardButton("📸 Створити новину з фото"),
        types.KeyboardButton("✍️ Створити новину з опису")
    )

    keyboard.add(
        types.KeyboardButton("🤖 Запропонувати тему"),
        types.KeyboardButton("📍 Google-точки")
    )

    keyboard.add(
        types.KeyboardButton("📅 Автопублікація"),
        types.KeyboardButton("🗂 Історія")
    )

    return keyboard


@bot.message_handler(commands=["start"])
def start(message):
    text = (
        "🔧 Autoservice A24\n\n"
        "Вітаю! Я ваш помічник для створення та "
        "публікації новин.\n\n"
        "Оберіть потрібну дію 👇"
    )

    bot.send_message(
        message.chat.id,
        text,
        reply_markup=main_menu()
    )


@bot.message_handler(func=lambda message: message.text == "📸 Створити новину з фото")
def photo_news(message):
    bot.send_message(
        message.chat.id,
        "📸 Надішліть мені фотографію виконаної роботи.\n\n"
        "Після цього я попрошу коротко описати, що було зроблено."
    )


@bot.message_handler(func=lambda message: message.text == "✍️ Створити новину з опису")
def text_news(message):
    bot.send_message(
        message.chat.id,
        "✍️ Напишіть коротко, про що потрібно створити новину.\n\n"
        "Наприклад:\n"
        "BMW X5 — заміна ланцюга ГРМ."
    )


@bot.message_handler(func=lambda message: message.text == "🤖 Запропонувати тему")
def suggest_topic(message):
    bot.send_message(
        message.chat.id,
        "🤖 Незабаром тут ШІ сам пропонуватиме тему для нової публікації."
    )


@bot.message_handler(func=lambda message: message.text == "📍 Google-точки")
def google_points(message):
    keyboard = types.ReplyKeyboardMarkup(
        resize_keyboard=True,
        row_width=2
    )

    keyboard.add(
        types.KeyboardButton("📍 Точка №1"),
        types.KeyboardButton("📍 Точка №2")
    )

    keyboard.add(
        types.KeyboardButton("📍 Точка №3"),
        types.KeyboardButton("🌐 Усі 3 точки")
    )

    keyboard.add(
        types.KeyboardButton("⬅️ Головне меню")
    )

    bot.send_message(
        message.chat.id,
        "📍 Оберіть Google-точку:",
        reply_markup=keyboard
    )


@bot.message_handler(func=lambda message: message.text == "📅 Автопублікація")
def autopost(message):
    bot.send_message(
        message.chat.id,
        "📅 Автопублікацію налаштуємо після підключення Google Business Profile."
    )


@bot.message_handler(func=lambda message: message.text == "🗂 Історія")
def history(message):
    bot.send_message(
        message.chat.id,
        "🗂 Тут буде історія створених та опублікованих новин."
    )


@bot.message_handler(func=lambda message: message.text == "⬅️ Головне меню")
def back_to_menu(message):
    bot.send_message(
        message.chat.id,
        "Головне меню 👇",
        reply_markup=main_menu()
    )


bot.delete_webhook(drop_pending_updates=True)
bot.infinity_polling()
