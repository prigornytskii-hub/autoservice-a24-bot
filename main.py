import os
import telebot
from telebot import types

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

user_state = {}
user_data = {}


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


@bot.message_handler(commands=["start"])
def start(message):
    user_state.pop(message.chat.id, None)

    bot.send_message(
        message.chat.id,
        "🔧 Autoservice A24\n\n"
        "Вітаю! Я ваш помічник для створення та "
        "публікації новин.\n\n"
        "Оберіть потрібну дію 👇",
        reply_markup=main_menu()
    )


@bot.message_handler(
    func=lambda message: message.text == "📸 Створити новину з фото"
)
def start_photo_post(message):
    chat_id = message.chat.id

    user_state[chat_id] = "waiting_photo"
    user_data[chat_id] = {}

    bot.send_message(
        chat_id,
        "📸 Надішліть фотографію виконаної роботи."
    )


@bot.message_handler(
    content_types=["photo"],
    func=lambda message: user_state.get(message.chat.id) == "waiting_photo"
)
def receive_photo(message):
    chat_id = message.chat.id

    photo_id = message.photo[-1].file_id
    user_data[chat_id]["photo_id"] = photo_id

    user_state[chat_id] = "waiting_description"

    bot.send_message(
        chat_id,
        "✅ Фото отримано.\n\n"
        "Тепер коротко напишіть, що було зроблено.\n\n"
        "Наприклад:\n"
        "BMW M5 S63 — замінили форсунки, "
        "виконали кодування та перевірили паливну систему."
    )


@bot.message_handler(
    func=lambda message:
        user_state.get(message.chat.id) == "waiting_description"
)
def receive_description(message):
    chat_id = message.chat.id

    description = message.text
    user_data[chat_id]["description"] = description

    # Поки робимо тестовий текст без ШІ.
    # Наступним етапом підключимо OpenAI API.

    post_text = (
        "🔧 Autoservice A24\n\n"
        f"{description}\n\n"
        "Провели необхідні роботи та перевірку системи після ремонту.\n\n"
        "Регулярна діагностика та своєчасний ремонт допомагають "
        "уникнути серйозніших несправностей автомобіля.\n\n"
        "📍 Autoservice A24\n"
        "Запис на діагностику та ремонт."
    )

    user_data[chat_id]["post_text"] = post_text
    user_state[chat_id] = "preview"

    bot.send_photo(
        chat_id,
        user_data[chat_id]["photo_id"],
        caption=post_text,
        reply_markup=post_buttons()
    )


@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id

    if call.data == "publish":
        bot.answer_callback_query(call.id)

        bot.send_message(
            chat_id,
            "✅ Пост готовий до публікації.\n\n"
            "Наступним етапом підключимо ваші Google-точки."
        )

    elif call.data == "regenerate":
        bot.answer_callback_query(call.id)

        description = user_data.get(chat_id, {}).get(
            "description",
            "Виконано ремонт автомобіля."
        )

        post_text = (
            "🚘 Робота в Autoservice A24\n\n"
            f"{description}\n\n"
            "Після виконаних робіт автомобіль пройшов перевірку.\n"
            "Рекомендуємо не відкладати діагностику при появі "
            "перших симптомів несправності.\n\n"
            "🔧 Autoservice A24"
        )

        user_data[chat_id]["post_text"] = post_text

        bot.edit_message_caption(
            chat_id=chat_id,
            message_id=call.message.message_id,
            caption=post_text,
            reply_markup=post_buttons()
        )

    elif call.data == "edit_post":
        bot.answer_callback_query(call.id)

        user_state[chat_id] = "editing_post"

        bot.send_message(
            chat_id,
            "✏️ Надішліть свій варіант тексту поста."
        )

    elif call.data == "cancel":
        bot.answer_callback_query(call.id)

        user_state.pop(chat_id, None)
        user_data.pop(chat_id, None)

        bot.send_message(
            chat_id,
            "❌ Створення публікації скасовано.",
            reply_markup=main_menu()
        )


@bot.message_handler(
    func=lambda message:
        user_state.get(message.chat.id) == "editing_post"
)
def edit_post(message):
    chat_id = message.chat.id

    user_data[chat_id]["post_text"] = message.text
    user_state[chat_id] = "preview"

    bot.send_photo(
        chat_id,
        user_data[chat_id]["photo_id"],
        caption=message.text,
        reply_markup=post_buttons()
    )


@bot.message_handler(
    func=lambda message: message.text == "📍 Google-точки"
)
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


@bot.message_handler(
    func=lambda message: message.text == "⬅️ Головне меню"
)
def back_to_menu(message):
    bot.send_message(
        message.chat.id,
        "Головне меню 👇",
        reply_markup=main_menu()
    )


@bot.message_handler(
    func=lambda message: message.text == "🤖 Запропонувати тему"
)
def suggest_topic(message):
    bot.send_message(
        message.chat.id,
        "🤖 Наступним етапом підключимо ШІ, "
        "і я сам пропонуватиму теми для новин."
    )


@bot.message_handler(
    func=lambda message: message.text == "📅 Автопублікація"
)
def autopost(message):
    bot.send_message(
        message.chat.id,
        "📅 Автопублікацію підключимо після Google Business Profile."
    )


@bot.message_handler(
    func=lambda message: message.text == "📋 Історія"
)
def history(message):
    bot.send_message(
        message.chat.id,
        "📋 Тут буде історія створених та опублікованих новин."
    )


bot.delete_webhook(drop_pending_updates=True)
bot.infinity_polling()
