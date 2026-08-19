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
# КЛАВІАТУРИ
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


# =========================================================
# OPENAI
# =========================================================

def download_telegram_photo(photo_id):
    file_info = bot.get_file(photo_id)
    return bot.download_file(file_info.file_path)


def build_photo_prompt(user_description, variation=False):
    variation_text = ""

    if variation:
        variation_text = """
Це повторна генерація.

Зроби нову версію публікації:
- інший заголовок;
- інший вступ;
- інший акцент;
- інша структура речень;
- не повторюй попередні шаблонні формулювання.
"""

    return f"""
Ти — професійний контент-асистент автосервісу Autoservice A24.

Тобі передано фотографію реальної роботи з автосервісу
та короткий коментар механіка.

КОМЕНТАР МЕХАНІКА:
"{user_description}"

ТВОЄ ЗАВДАННЯ:

Уважно проаналізуй саме фотографію.

Визнач:
- яка деталь, вузол або процес зображений;
- які особливості реально видно;
- чи видно сліди зносу, тертя, забруднення, пошкодження,
  перегріву, демонтажу або ремонту;
- що на фото може бути цікавим для власника автомобіля.

Використовуй коментар механіка як головний технічний контекст,
але доповнюй його тим, що реально видно на фотографії.

ВАЖЛИВО:

1. Не пиши універсальний шаблон.
2. Кожна новина повинна бути написана саме під конкретне фото.
3. Не вигадуй марку автомобіля, двигун, пробіг або несправність,
   якщо цього немає в описі або це неможливо достовірно визначити.
4. Не вигадуй вимірювання, зазори, тиск, компресію чи інші цифри.
5. Якщо по фото неможливо точно підтвердити пошкодження —
   використовуй формулювання:
   "видно сліди роботи",
   "помітний стан робочої поверхні",
   "деталь потребує перевірки",
   а не категоричний діагноз.
6. Не повторюй постійно:
   "провели необхідні роботи",
   "регулярна діагностика допомагає уникнути несправностей".
7. Пояснюй технічну тему простою мовою для звичайного клієнта.
8. Не починай словами:
   "На фото ми бачимо".
9. Додай одну цікаву технічну деталь про те,
   чому цей вузол важливий.
10. Текст має звучати професійно, але живо.

СТРУКТУРА:

Перша строка:
короткий сильний заголовок з емодзі.

Потім:
- що конкретно зображено;
- що перевіряємо або ремонтуємо;
- на що звертаємо увагу;
- чому це важливо для двигуна або автомобіля;
- короткий висновок для клієнта.

В кінці обов'язково:

🔧 Autoservice A24
📍 Діагностика та ремонт автомобілів

Мова: українська.

Довжина:
приблизно 500–850 символів.

{variation_text}
"""


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

    post_text = response.output_text.strip()

    if not post_text:
        raise RuntimeError(
            "OpenAI returned empty response"
        )

    if len(post_text) > 1000:
        post_text = post_text[:997] + "..."

    return post_text


def generate_post_from_text(
    user_description,
    variation=False
):
    variation_text = ""

    if variation:
        variation_text = """
Це повторна генерація.
Зроби зовсім іншу подачу та інший заголовок.
"""

    prompt = f"""
Ти — контент-асистент автосервісу Autoservice A24.

Механік написав:

"{user_description}"

Створи цікаву новину українською мовою
для Google Business Profile.

Не вигадуй факти, яких немає в описі.

Поясни:
- що було зроблено;
- чому ця робота важлива;
- які проблеми може попередити така перевірка або ремонт.

Не використовуй постійно однакові шаблонні фрази.

Структура:

• короткий заголовок з емодзі;
• суть роботи;
• коротке технічне пояснення;
• користь для клієнта;

В кінці:

🔧 Autoservice A24
📍 Діагностика та ремонт автомобілів

Довжина приблизно 500–800 символів.

{variation_text}
"""

    response = client.responses.create(
        model=OPENAI_MODEL,
        input=prompt
    )

    post_text = response.output_text.strip()

    if not post_text:
        raise RuntimeError(
            "OpenAI returned empty response"
        )

    if len(post_text) > 1000:
        post_text = post_text[:997] + "..."

    return post_text


# =========================================================
# START
# =========================================================

@bot.message_handler(commands=["start"])
def start(message):
    chat_id = message.chat.id

    user_state.pop(chat_id, None)
    user_data.pop(chat_id, None)

    bot.send_message(
        chat_id,
        "🔧 Autoservice A24\n\n"
        "Вітаю! Я ваш помічник для створення "
        "та публікації новин.\n\n"
        "Оберіть потрібну дію 👇",
        reply_markup=main_menu()
    )


# =========================================================
# НОВИНА З ФОТО
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
        "🤖 Я проаналізую, що саме зображено на фото."
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
        "Тепер коротко напишіть, що ви робили.\n\n"
        "Можна буквально 2–5 слів.\n\n"
        "Наприклад:\n"
        "• перевірка шатунних вкладишів\n"
        "• заміна форсунок\n"
        "• діагностика турбіни\n"
        "• заміна ланцюга ГРМ\n\n"
        "🤖 Фото я проаналізую сам."
    )


@bot.message_handler(
    func=lambda message:
        user_state.get(message.chat.id)
        == "waiting_description"
)
def receive_description(message):
    chat_id = message.chat.id

    if not message.text:
        bot.send_message(
            chat_id,
            "Напишіть короткий опис текстом."
        )
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
            "⚠️ Не вдалося проаналізувати фото через ШІ.\n\n"
            "У Railway записана точна причина помилки."
        )


# =========================================================
# НОВИНА ТІЛЬКИ З ОПИСУ
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
        "✍️ Напишіть коротко, що було зроблено.\n\n"
        "Наприклад:\n"
        "BMW 3.0 дизель — замінили ланцюг ГРМ "
        "та перевірили фази газорозподілу."
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
            "⚠️ Не вдалося створити новину через ШІ.\n\n"
            "Перевірте журнал Railway."
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

    if call.data == "publish":
        bot.send_message(
            chat_id,
            "✅ Пост готовий до публікації.\n\n"
            "Наступним етапом підключимо "
            "Google Business Profile."
        )

    elif call.data == "regenerate":
        data = user_data.get(chat_id, {})

        description = data.get(
            "description",
            ""
        )

        mode = data.get(
            "mode",
            "text"
        )

        bot.send_message(
            chat_id,
            "🔄 Роблю нову версію..."
        )

        try:
            if mode == "photo":
                photo_id = data["photo_id"]

                post_text = generate_post_from_photo(
                    photo_id,
                    description,
                    variation=True
                )

                user_data[chat_id]["post_text"] = post_text

                try:
                    bot.edit_message_caption(
                        chat_id=chat_id,
                        message_id=call.message.message_id,
                        caption=post_text,
                        reply_markup=post_buttons()
                    )

                except Exception:
                    bot.send_photo(
                        chat_id,
                        photo_id,
                        caption=post_text,
                        reply_markup=post_buttons()
                    )

            else:
                post_text = generate_post_from_text(
                    description,
                    variation=True
                )

                user_data[chat_id]["post_text"] = post_text

                bot.send_message(
                    chat_id,
                    post_text,
                    reply_markup=post_buttons()
                )

        except Exception as error:
            print(
                "REGENERATE ERROR:",
                repr(error),
                flush=True
            )

            bot.send_message(
                chat_id,
                "⚠️ Не вдалося створити нову версію."
            )

    elif call.data == "edit_post":
        user_state[chat_id] = "editing_post"

        bot.send_message(
            chat_id,
            "✏️ Надішліть свій варіант тексту поста."
        )

    elif call.data == "cancel":
        user_state.pop(chat_id, None)
        user_data.pop(chat_id, None)

        bot.send_message(
            chat_id,
            "❌ Створення публікації скасовано.",
            reply_markup=main_menu()
        )


# =========================================================
# РЕДАГУВАННЯ
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

    new_text = message.text.strip()

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

        if photo_id:
            bot.send_photo(
                chat_id,
                photo_id,
                caption=new_text[:1000],
                reply_markup=post_buttons()
            )
            return

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
        "🤖 Думаю над темою для новини..."
    )

    try:
        response = client.responses.create(
            model=OPENAI_MODEL,
            input="""
Запропонуй одну цікаву тему для короткої
публікації автосервісу Autoservice A24.

Тема має бути корисною для власника автомобіля.

Наприклад:
ГРМ, форсунки, турбіна, олива, гальма,
підвіска, охолодження, діагностика,
кондиціонер або паливна система.

Українською мовою.

Дай:
1. Назву теми.
2. Коротко, про що написати.
3. Яке фото краще зробити для такої публікації.
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
        "📅 Автопублікацію підключимо після "
        "підключення Google Business Profile."
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
# ЗАПУСК БОТА
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
