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


# =========================
# OPENAI + АНАЛІЗ ФОТО
# =========================

def download_telegram_photo(photo_id):
    file_info = bot.get_file(photo_id)
    photo_bytes = bot.download_file(file_info.file_path)

    return photo_bytes


def generate_post_from_photo(photo_id, user_description, variation=False):
    photo_bytes = download_telegram_photo(photo_id)

    base64_image = base64.b64encode(photo_bytes).decode("utf-8")

    if variation:
        variation_instruction = """
Це повторна генерація.
Зроби абсолютно іншу подачу попередньої теми:
інший заголовок, інший вступ та інший акцент.
Не повторюй попередні шаблонні фрази.
"""
    else:
        variation_instruction = ""

    prompt = f"""
Ти — контент-асистент професійного автосервісу Autoservice A24.

Твоє завдання — уважно проаналізувати фотографію з автосервісу
та написати цікаву публікацію українською мовою для Google Business Profile.

Короткий опис від механіка:
"{user_description}"

ВАЖЛИВО:

1. Спочатку реально подивись на фотографію.
2. Зрозумій, яка автомобільна деталь, вузол, інструмент або процес на ній зображений.
3. Зверни увагу на видимі сліди роботи, зносу, пошкодження, забруднення,
   демонтажу або ремонту.
4. Використовуй короткий опис механіка як додатковий контекст.
5. Не вигадуй марку автомобіля, модель двигуна або несправність,
   якщо цього неможливо достовірно визначити.
6. Не стверджуй, що деталь несправна лише через зовнішній вигляд,
   якщо по фото це неможливо підтвердити.
7. Якщо на фотографії є цікавий технічний момент —
   зроби саме його головною темою поста.
8. Не використовуй постійно однакові фрази типу:
   "провели необхідні роботи",
   "регулярна діагностика допомагає уникнути несправностей".
9. Кожна публікація повинна відчуватися написаною спеціально під конкретне фото.
10. Поясни клієнту простою мовою, чому те, що показано на фото, важливе.
11. Не перевантажуй текст складною технічною термінологією.
12. Не вигадуй результати вимірювань, зазори, тиск, пробіг або причину поломки,
    якщо механік їх не вказав.

СТРУКТУРА:

• короткий сильний заголовок з емодзі;
• 1–2 речення про те, що конкретно видно на фото;
• що перевіряли або робили;
• чому цей вузол/деталь важливі;
• короткий корисний висновок для власника автомобіля;
• в кінці:
  🔧 Autoservice A24
  📍 Діагностика та ремонт автомобілів

Пиши природно, професійно та цікаво.

Не пиши слова:
"На фотографії ми бачимо".
Одразу починай з суті.

Максимальна довжина — приблизно 800 символів.

{variation_instruction}
"""

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}",
                            "detail": "high"
                        }
                    }
                ]
            }
        ]
    )

    post_text = response.choices[0].message.content.strip()

    # Telegram caption має обмеження довжини.
    if len(post_text) > 1000:
        post_text = post_text[:997] + "..."

    return post_text


# =========================
# /START
# =========================

@bot.message_handler(commands=["start"])
def start(message):
    user_state.pop(message.chat.id, None)
    user_data.pop(message.chat.id, None)

    bot.send_message(
        message.chat.id,
        "🔧 Autoservice A24\n\n"
        "Вітаю! Я ваш помічник для створення "
        "та публікації новин.\n\n"
        "Оберіть потрібну дію 👇",
        reply_markup=main_menu()
    )


# =========================
# СТВОРЕННЯ ПОСТА З ФОТО
# =========================

@bot.message_handler(
    func=lambda message: message.text == "📸 Створити новину з фото"
)
def start_photo_post(message):
    chat_id = message.chat.id

    user_state[chat_id] = "waiting_photo"
    user_data[chat_id] = {}

    bot.send_message(
        chat_id,
        "📸 Надішліть фотографію виконаної роботи.\n\n"
        "Я проаналізую, що саме зображено на фото."
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
        "Тепер коротко напишіть, що ви робили.\n\n"
        "Можна буквально 2–5 слів.\n\n"
        "Наприклад:\n"
        "• перевірка вкладишів\n"
        "• заміна форсунок\n"
        "• діагностика турбіни\n"
        "• заміна ланцюга ГРМ\n\n"
        "🤖 Фото я проаналізую сам."
    )


@bot.message_handler(
    func=lambda message:
        user_state.get(message.chat.id) == "waiting_description"
)
def receive_description(message):
    chat_id = message.chat.id

    description = message.text
    user_data[chat_id]["description"] = description

    bot.send_message(
        chat_id,
        "🔍 Аналізую фотографію та готую публікацію..."
    )

    try:
        post_text = generate_post_from_photo(
            user_data[chat_id]["photo_id"],
            description
        )

        user_data[chat_id]["post_text"] = post_text
        user_state[chat_id] = "preview"

        bot.send_photo(
            chat_id,
            user_data[chat_id]["photo_id"],
            caption=post_text,
            reply_markup=post_buttons()
        )
except Exception as e:
    print("OPENAI ERROR:", repr(e), flush=True)
    

        bot.send_message(
            chat_id,
            "⚠️ Не вдалося проаналізувати фото через ШІ.\n\n"
            "Перевірте OPENAI_API_KEY або журнал Railway."
        )


# =========================
# INLINE-КНОПКИ
# =========================

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id

    if call.data == "publish":
        bot.answer_callback_query(call.id)

        bot.send_message(
            chat_id,
            "✅ Пост готовий до публікації.\n\n"
            "Наступним етапом підключимо Google Business Profile."
        )

    elif call.data == "regenerate":
        bot.answer_callback_query(call.id)

        bot.send_message(
            chat_id,
            "🔄 Аналізую фото ще раз і роблю іншу версію..."
        )

        try:
            photo_id = user_data[chat_id]["photo_id"]
            description = user_data[chat_id]["description"]

            post_text = generate_post_from_photo(
                photo_id,
                description,
                variation=True
            )

            user_data[chat_id]["post_text"] = post_text

            bot.edit_message_caption(
                chat_id=chat_id,
                message_id=call.message.message_id,
                caption=post_text,
                reply_markup=post_buttons()
            )

        except Exception as error:
            print("REGENERATE ERROR:", error)

            bot.send_message(
                chat_id,
                "⚠️ Не вдалося створити нову версію."
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


# =========================
# РЕДАГУВАННЯ
# =========================

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


# =========================
# GOOGLE ТОЧКИ
# =========================

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


# =========================
# ІНШІ КНОПКИ
# =========================

@bot.message_handler(
    func=lambda message: message.text == "🤖 Запропонувати тему"
)
def suggest_topic(message):
    bot.send_message(
        message.chat.id,
        "🤖 Цю функцію підключимо наступним етапом."
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


# =========================
# ЗАПУСК
# =========================

bot.delete_webhook(drop_pending_updates=True)

print("Autoservice A24 bot started")

bot.infinity_polling(
    timeout=60,
    long_polling_timeout=60
)
