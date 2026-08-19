import os
import base64
import telebot
from telebot import types
from openai import OpenAI


# =========================================================
# НАЛАШТУВАННЯ
# =========================================================

TOKEN = (os.getenv("TELEGRAM_BOT_TOKEN") or "").strip()
OPENAI_API_KEY = (os.getenv("OPENAI_API_KEY") or "").strip()
OPENAI_MODEL = (os.getenv("OPENAI_MODEL") or "gpt-5-mini").strip()

if not TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is not set")


bot = telebot.TeleBot(TOKEN)
client = OpenAI(api_key=OPENAI_API_KEY)

user_state = {}
user_data = {}


# =========================================================
# ГОЛОВНЕ МЕНЮ
# =========================================================

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


# =========================================================
# КНОПКИ ПІД ГОТОВИМ ПОСТОМ
# =========================================================

def post_buttons():
    keyboard = types.InlineKeyboardMarkup()

    keyboard.row(
        types.InlineKeyboardButton(
            "✂️ Коротше",
            callback_data="shorter"
        ),
        types.InlineKeyboardButton(
            "🎯 Професійніше",
            callback_data="professional"
        )
    )

    keyboard.row(
        types.InlineKeyboardButton(
            "👤 Простіше",
            callback_data="simpler"
        ),
        types.InlineKeyboardButton(
            "🔄 Інший варіант",
            callback_data="regenerate"
        )
    )

    keyboard.row(
        types.InlineKeyboardButton(
            "✏️ Редагувати",
            callback_data="edit_post"
        ),
        types.InlineKeyboardButton(
            "✅ Опублікувати",
            callback_data="publish"
        )
    )

    keyboard.row(
        types.InlineKeyboardButton(
            "❌ Скасувати",
            callback_data="cancel"
        )
    )

    return keyboard


# =========================================================
# OPENAI: ДОПОМІЖНІ ФУНКЦІЇ
# =========================================================

def download_telegram_photo(photo_id):
    file_info = bot.get_file(photo_id)
    return bot.download_file(file_info.file_path)


def clean_post(text):
    text = (text or "").strip()

    if len(text) > 1000:
        text = text[:997] + "..."

    return text


# =========================================================
# ПРОМПТ ДЛЯ ФОТО
# =========================================================

def build_photo_prompt(user_description, variation=False):
    variation_text = ""

    if variation:
        variation_text = """
Це повторна генерація.

Зроби публікацію повністю по-іншому:
- інший заголовок;
- інший вступ;
- інший акцент;
- інша структура;
- не повторюй попередній текст.
"""

    return f"""
Ти — контент-асистент професійного автосервісу Autoservice A24.

Тобі передано реальну фотографію роботи з автосервісу
та короткий коментар механіка.

КОМЕНТАР МЕХАНІКА:
"{user_description}"

ТВОЄ ЗАВДАННЯ:

Уважно проаналізуй саме фотографію.

Визнач:
- яка деталь, вузол або процес зображений;
- які особливості реально видно;
- чи видно сліди тертя, зносу, пошкодження, забруднення,
  демонтажу або ремонту;
- який технічний момент на цьому фото найцікавіший.

ВАЖЛИВО:

1. Не пиши універсальний шаблон.
2. Публікація повинна бути прив'язана саме до конкретного фото.
3. Коментар механіка має пріоритет.
4. Не вигадуй марку автомобіля, двигун або пробіг.
5. Не вигадуй результати вимірювань.
6. Не вигадуй точну причину несправності, якщо її неможливо підтвердити.
7. Якщо видно сліди роботи або зносу — можеш це описати обережно.
8. Не роби категоричний діагноз тільки по фотографії.
9. Пояснюй клієнту просто, але технічно грамотно.
10. Уникай шаблонних фраз.
11. Не починай словами "На фото ми бачимо".
12. Не перевантажуй текст.

СТРУКТУРА:

• короткий цікавий заголовок;
• що саме перевіряємо/ремонтуємо;
• що цікавого можна побачити;
• чому ця деталь або вузол важливі;
• короткий висновок.

В кінці:

🔧 Autoservice A24
📍 Діагностика та ремонт автомобілів

Мова: українська.

Оптимальна довжина:
450–700 символів.

Текст має добре читатися як пост у Google Business Profile.

{variation_text}
"""


# =========================================================
# ГЕНЕРАЦІЯ ПОСТА З ФОТО
# =========================================================

def generate_post_from_photo(
    photo_id,
    user_description,
    variation=False
):
    photo_bytes = download_telegram_photo(photo_id)

    base64_image = base64.b64encode(
        photo_bytes
    ).decode("utf-8")

    prompt = build_photo_prompt(
        user_description,
        variation=variation
    )

    response = client.responses.create(
        model=OPENAI_MODEL,
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": prompt
                    },
                    {
                        "type": "input_image",
                        "image_url": (
                            "data:image/jpeg;base64,"
                            + base64_image
                        )
                    }
                ]
            }
        ]
    )

    post_text = clean_post(response.output_text)

    if not post_text:
        raise RuntimeError("OpenAI returned empty response")

    return post_text


# =========================================================
# ГЕНЕРАЦІЯ ПОСТА ТІЛЬКИ З ТЕКСТУ
# =========================================================

def generate_post_from_text(
    user_description,
    variation=False
):
    variation_text = ""

    if variation:
        variation_text = """
Зроби абсолютно іншу версію:
інший заголовок, інша подача та інший акцент.
"""

    prompt = f"""
Ти — контент-асистент автосервісу Autoservice A24.

Опис роботи від механіка:

"{user_description}"

Створи професійну, цікаву та зрозумілу
публікацію українською мовою для Google Business Profile.

Не вигадуй факти, яких немає в описі.

Поясни:
- що було зроблено;
- навіщо це робиться;
- чому це важливо для автомобіля;
- що корисно знати власнику.

Не пиши сухий шаблон.

В кінці:

🔧 Autoservice A24
📍 Діагностика та ремонт автомобілів

Довжина:
450–700 символів.

{variation_text}
"""

    response = client.responses.create(
        model=OPENAI_MODEL,
        input=prompt
    )

    post_text = clean_post(response.output_text)

    if not post_text:
        raise RuntimeError("OpenAI returned empty response")

    return post_text


# =========================================================
# ПЕРЕРОБКА ВЖЕ ГОТОВОГО ПОСТА
# =========================================================

def rewrite_post(current_text, mode):
    instructions = {
        "shorter": """
Зроби цей пост значно коротшим.

Збережи:
- основний технічний зміст;
- найцікавіший момент;
- Autoservice A24.

Оптимальна довжина:
250–400 символів.

Без води.
""",

        "professional": """
Перепиши цей пост професійніше.

Тон:
експертний автосервіс.

Зроби текст технічно точнішим,
але зрозумілим звичайному клієнту.

Не вигадуй нові факти.
""",

        "simpler": """
Перепиши цей пост простішою мовою.

Прибери зайву технічну складність.

Текст має легко зрозуміти клієнт,
який не розбирається в будові автомобіля.

Не вигадуй нові факти.
""",

        "regenerate": """
Напиши повністю нову версію цього поста.

Зміни:
- заголовок;
- вступ;
- структуру;
- акцент.

Збережи факти з оригінального тексту.
Не вигадуй нові факти.
"""
    }

    instruction = instructions.get(
        mode,
        instructions["regenerate"]
    )

    prompt = f"""
Ти редагуєш готовий пост автосервісу Autoservice A24.

ПОТОЧНИЙ ПОСТ:

{current_text}

ЗАВДАННЯ:

{instruction}

В кінці залиш:

🔧 Autoservice A24
📍 Діагностика та ремонт автомобілів

Мова: українська.
"""

    response = client.responses.create(
        model=OPENAI_MODEL,
        input=prompt
    )

    new_text = clean_post(response.output_text)

    if not new_text:
        raise RuntimeError("OpenAI returned empty response")

    return new_text


# =========================================================
# /START
# =========================================================

@bot.message_handler(commands=["start"])
def start(message):
    chat_id = message.chat.id

    user_state.pop(chat_id, None)
    user_data.pop(chat_id, None)

    bot.send_message(
        chat_id,
        "🔧 Autoservice A24\n\n"
        "Помічник для створення публікацій.\n\n"
        "Оберіть потрібну дію 👇",
        reply_markup=main_menu()
    )


# =========================================================
# СТВОРЕННЯ НОВИНИ З ФОТО
# =========================================================

@bot.message_handler(
    func=lambda message:
        message.text == "📸 Створити новину з фото"
)
def start_photo_post(message):
    chat_id = message.chat.id

    user_state[chat_id] = "waiting_photo"

    user_data[chat_id] = {
        "mode": "photo"
    }

    bot.send_message(
        chat_id,
        "📸 Надішліть фотографію виконаної роботи.\n\n"
        "Я проаналізую, що саме зображено."
    )


@bot.message_handler(
    content_types=["photo"],
    func=lambda message:
        user_state.get(message.chat.id)
        == "waiting_photo"
)
def receive_photo(message):
    chat_id = message.chat.id

    photo_id = message.photo[-1].file_id

    user_data.setdefault(chat_id, {})

    user_data[chat_id]["photo_id"] = photo_id
    user_data[chat_id]["mode"] = "photo"

    user_state[chat_id] = "waiting_description"

    bot.send_message(
        chat_id,
        "✅ Фото отримано.\n\n"
        "Тепер коротко напишіть, що робили.\n\n"
        "Наприклад:\n"
        "• перевірка шатунних вкладишів\n"
        "• заміна форсунок\n"
        "• діагностика турбіни\n"
        "• заміна ланцюга ГРМ\n\n"
        "🤖 Деталі з фото я проаналізую сам."
    )


@bot.message_handler(
    func=lambda message:
        user_state.get(message.chat.id)
        == "waiting_description"
)
def receive_description(message):
    chat_id = message.chat.id

    if not message.text:
        return

    description = message.text.strip()

    user_data.setdefault(chat_id, {})
    user_data[chat_id]["description"] = description

    bot.send_message(
        chat_id,
        "🔍 Аналізую фотографію та готую публікацію..."
    )

    try:
        photo_id = user_data[chat_id]["photo_id"]

        post_text = generate_post_from_photo(
            photo_id,
            description
        )

        user_data[chat_id]["post_text"] = post_text
        user_state[chat_id] = "preview"

        bot.send_photo(
            chat_id,
            photo_id,
            caption=post_text,
            reply_markup=post_buttons()
        )

    except Exception as error:
        print(
            "OPENAI PHOTO ERROR:",
            repr(error),
            flush=True
        )

        bot.send_message(
            chat_id,
            "⚠️ Не вдалося створити пост.\n\n"
            "Точна причина записана в Railway."
        )


# =========================================================
# НОВИНА З ОПИСУ
# =========================================================

@bot.message_handler(
    func=lambda message:
        message.text == "✍️ Створити новину з опису"
)
def start_text_post(message):
    chat_id = message.chat.id

    user_state[chat_id] = "waiting_text_post"

    user_data[chat_id] = {
        "mode": "text"
    }

    bot.send_message(
        chat_id,
        "✍️ Напишіть коротко, що було зроблено."
    )


@bot.message_handler(
    func=lambda message:
        user_state.get(message.chat.id)
        == "waiting_text_post"
)
def receive_text_post(message):
    chat_id = message.chat.id

    if not message.text:
        return

    description = message.text.strip()

    user_data.setdefault(chat_id, {})

    user_data[chat_id]["description"] = description
    user_data[chat_id]["mode"] = "text"

    bot.send_message(
        chat_id,
        "🤖 Готую публікацію..."
    )

    try:
        post_text = generate_post_from_text(
            description
        )

        user_data[chat_id]["post_text"] = post_text
        user_state[chat_id] = "preview"

        bot.send_message(
            chat_id,
            post_text,
            reply_markup=post_buttons()
        )

    except Exception as error:
        print(
            "OPENAI TEXT ERROR:",
            repr(error),
            flush=True
        )

        bot.send_message(
            chat_id,
            "⚠️ Не вдалося створити пост."
        )


# =========================================================
# INLINE КНОПКИ
# =========================================================

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id

    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass

    data = user_data.get(chat_id, {})

    current_text = data.get(
        "post_text",
        ""
    )

    # -----------------------------------------------------
    # КОРОТШЕ / ПРОФЕСІЙНІШЕ / ПРОСТІШЕ / ІНШИЙ ВАРІАНТ
    # -----------------------------------------------------

    if call.data in [
        "shorter",
        "professional",
        "simpler",
        "regenerate"
    ]:
        if not current_text:
            bot.send_message(
                chat_id,
                "⚠️ Не знайшов попередній текст."
            )
            return

        messages = {
            "shorter": "✂️ Роблю коротшу версію...",
            "professional": "🎯 Роблю професійнішу версію...",
            "simpler": "👤 Спрощую текст для клієнта...",
            "regenerate": "🔄 Роблю повністю новий варіант..."
        }

        bot.send_message(
            chat_id,
            messages[call.data]
        )

        try:
            new_text = rewrite_post(
                current_text,
                call.data
            )

            user_data[chat_id]["post_text"] = new_text

            mode = data.get("mode", "text")

            if mode == "photo":
                photo_id = data.get("photo_id")

                bot.send_photo(
                    chat_id,
                    photo_id,
                    caption=new_text,
                    reply_markup=post_buttons()
                )

            else:
                bot.send_message(
                    chat_id,
                    new_text,
                    reply_markup=post_buttons()
                )

        except Exception as error:
            print(
                "REWRITE ERROR:",
                repr(error),
                flush=True
            )

            bot.send_message(
                chat_id,
                "⚠️ Не вдалося переробити текст."
            )

    # -----------------------------------------------------
    # РЕДАГУВАТИ ВРУЧНУ
    # -----------------------------------------------------

    elif call.data == "edit_post":
        user_state[chat_id] = "editing_post"

        bot.send_message(
            chat_id,
            "✏️ Надішліть свій готовий варіант тексту.\n\n"
            "Я підставлю його замість поточного."
        )

    # -----------------------------------------------------
    # ПУБЛІКАЦІЯ
    # -----------------------------------------------------

    elif call.data == "publish":
        bot.send_message(
            chat_id,
            "✅ Пост готовий.\n\n"
            "Наступним етапом підключимо "
            "пряму публікацію в Google Business Profile."
        )

    # -----------------------------------------------------
    # СКАСУВАТИ
    # -----------------------------------------------------

    elif call.data == "cancel":
        user_state.pop(chat_id, None)
        user_data.pop(chat_id, None)

        bot.send_message(
            chat_id,
            "❌ Створення публікації скасовано.",
            reply_markup=main_menu()
        )


# =========================================================
# РУЧНЕ РЕДАГУВАННЯ
# =========================================================

@bot.message_handler(
    func=lambda message:
        user_state.get(message.chat.id)
        == "editing_post"
)
def edit_post(message):
    chat_id = message.chat.id

    if not message.text:
        return

    new_text = clean_post(
        message.text
    )

    user_data.setdefault(chat_id, {})

    user_data[chat_id]["post_text"] = new_text

    mode = user_data[chat_id].get(
        "mode",
        "text"
    )

    user_state[chat_id] = "preview"

    if mode == "photo":
        photo_id = user_data[chat_id].get(
            "photo_id"
        )

        bot.send_photo(
            chat_id,
            photo_id,
            caption=new_text,
            reply_markup=post_buttons()
        )

    else:
        bot.send_message(
            chat_id,
            new_text,
            reply_markup=post_buttons()
        )


# =========================================================
# ЗАПРОПОНУВАТИ ТЕМУ
# =========================================================

@bot.message_handler(
    func=lambda message:
        message.text == "🤖 Запропонувати тему"
)
def suggest_topic(message):
    chat_id = message.chat.id

    bot.send_message(
        chat_id,
        "🤖 Підбираю тему..."
    )

    try:
        response = client.responses.create(
            model=OPENAI_MODEL,
            input="""
Запропонуй одну цікаву тему для Google Business Profile
автосервісу Autoservice A24.

Тема повинна бути реально корисною власнику автомобіля.

Дай:

1. Назву теми.
2. Про що коротко розповісти.
3. Яке фото зробити в автосервісі.

Мова: українська.
"""
        )

        bot.send_message(
            chat_id,
            response.output_text.strip()
        )

    except Exception as error:
        print(
            "TOPIC ERROR:",
            repr(error),
            flush=True
        )

        bot.send_message(
            chat_id,
            "⚠️ Не вдалося запропонувати тему."
        )


# =========================================================
# GOOGLE ТОЧКИ
# =========================================================

@bot.message_handler(
    func=lambda message:
        message.text == "📍 Google-точки"
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
    func=lambda message:
        message.text == "⬅️ Головне меню"
)
def back_to_menu(message):
    chat_id = message.chat.id

    user_state.pop(chat_id, None)

    bot.send_message(
        chat_id,
        "Головне меню 👇",
        reply_markup=main_menu()
    )


# =========================================================
# АВТОПУБЛІКАЦІЯ
# =========================================================

@bot.message_handler(
    func=lambda message:
        message.text == "📅 Автопублікація"
)
def autopost(message):
    bot.send_message(
        message.chat.id,
        "📅 Автопублікацію підключимо "
        "після Google Business Profile."
    )


# =========================================================
# ІСТОРІЯ
# =========================================================

@bot.message_handler(
    func=lambda message:
        message.text == "📋 Історія"
)
def history(message):
    bot.send_message(
        message.chat.id,
        "📋 Тут буде історія створених "
        "та опублікованих новин."
    )


# =========================================================
# ЗАПУСК
# =========================================================

print(
    "====================================",
    flush=True
)

print(
    "Autoservice A24 bot starting...",
    flush=True
)

print(
    "OpenAI model:",
    OPENAI_MODEL,
    flush=True
)

print(
    "====================================",
    flush=True
)


try:
    bot.remove_webhook()
except Exception as error:
    print(
        "WEBHOOK REMOVE ERROR:",
        repr(error),
        flush=True
    )


print(
    "Autoservice A24 bot started successfully",
    flush=True
)


bot.infinity_polling(
    skip_pending=True,
    timeout=30,
    long_polling_timeout=30
)
