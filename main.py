import os
import base64
import telebot
from telebot import types
from openai import OpenAI


# =========================
# НАЛАШТУВАННЯ
# =========================

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5-mini")

if not TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is not set")

bot = telebot.TeleBot(TOKEN)
client = OpenAI(api_key=OPENAI_API_KEY)

user_state = {}
user_data = {}


# =========================
# ГОЛОВНЕ МЕНЮ
# =========================

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
        types.KeyboardButton("📋 Історія")
    )

    return keyboard


def post_buttons():
    keyboard = types.InlineKeyboardMarkup()

    keyboard.row(
        types.InlineKeyboardButton(
            "✅ Опублікувати",
            callback_data="publish"
        ),
        types.InlineKeyboardButton(
            "🔄 Переробити",
            callback_data="regenerate"
        )
    )

    keyboard.row(
        types.InlineKeyboardButton(
            "✏️ Редагувати",
            callback_data="edit_post"
        ),
        types.InlineKeyboardButton(
            "❌ Скасувати",
            callback_data="cancel"
        )
    )

    return keyboard
