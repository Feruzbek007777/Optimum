import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from deep_translator import GoogleTranslator
from gtts import gTTS
import random
import os

# Foydalanuvchi tanlagan tillarni saqlash
user_languages = {}
user_stats = {}

# Random reaksiyalar
REACTIONS = ["👍", "🔥", "🤩", "👌", "❤️", "🥳"]


def get_translate_keyboard():
    """Translate uchun inline keyboard"""
    keyboard = InlineKeyboardMarkup(row_width=2)

    buttons = [
        InlineKeyboardButton("🇺🇿 UZ → 🇬🇧 EN", callback_data="translate_uz-en"),
        InlineKeyboardButton("🇬🇧 EN → 🇺🇿 UZ", callback_data="translate_en-uz"),
        InlineKeyboardButton("🇺🇿 UZ → 🇷🇺 RU", callback_data="translate_uz-ru"),
        InlineKeyboardButton("🇷🇺 RU → 🇺🇿 UZ", callback_data="translate_ru-uz"),
        InlineKeyboardButton("🇺🇿 UZ → 🇸🇦 AR", callback_data="translate_uz-ar"),
        InlineKeyboardButton("🇸🇦 AR → 🇺🇿 UZ", callback_data="translate_ar-uz"),
    ]

    for i in range(0, len(buttons), 2):
        if i + 1 < len(buttons):
            keyboard.add(buttons[i], buttons[i + 1])
        else:
            keyboard.add(buttons[i])

    return keyboard


def get_translate_menu():
    """Translate menyusi"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("🔄 Tilni o'zgartirish"), ("📊 Statistikam"))
    keyboard.add(KeyboardButton("🔙 Asosiy menyu"))
    return keyboard


def setup_translate_handlers(bot):
    """Translate handlerlarini sozlash"""

    @bot.message_handler(func=lambda message: message.text == "🌐 Translate")
    def translate_menu(message):
        keyboard = get_translate_keyboard()
        bot.send_message(message.chat.id, "🌐 Tarjima qilish uchun tilni tanlang:", reply_markup=keyboard)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("translate_"))
    def handle_translate_callback(call):
        lang_pair = call.data.replace("translate_", "")
        user_languages[call.from_user.id] = lang_pair

        lang_names = {
            "uz-en": "🇺🇿 O'zbekcha → 🇬🇧 Inglizcha",
            "en-uz": "🇬🇧 Inglizcha → 🇺🇿 O'zbekcha",
            "uz-ru": "🇺🇿 O'zbekcha → 🇷🇺 Ruscha",
            "ru-uz": "🇷🇺 Ruscha → 🇺🇿 O'zbekcha",
            "uz-ar": "🇺🇿 O'zbekcha → 🇸🇦 Arabcha",
            "ar-uz": "🇸🇦 Arabcha → 🇺🇿 O'zbekcha",
        }

        bot.answer_callback_query(call.id, f"✅ {lang_names[lang_pair]} tanlandi!")
        bot.send_message(
            call.message.chat.id,
            f"✅ {lang_names[lang_pair]}\n\n✍️ Endi tarjima qilmoqchi bo'lgan matnni yuboring:",
            reply_markup=get_translate_menu()
        )

    @bot.message_handler(func=lambda message: message.text == "🔄 Tilni o'zgartirish")
    def change_language(message):
        keyboard = get_translate_keyboard()
        bot.send_message(message.chat.id, "🌐 Yangi tilni tanlang:", reply_markup=keyboard)

    @bot.message_handler(func=lambda message: message.text == "📊 Statistikam")
    def show_stats(message):
        count = user_stats.get(message.from_user.id, 0)
        bot.send_message(message.chat.id, f"📊 Siz hozirgacha {count} marta tarjima qildingiz!")

    @bot.message_handler(func=lambda message: message.text == "🔙 Asosiy menyu")
    def back_to_main(message):
        from keyboards.default import main_menu_keyboard
        bot.send_message(message.chat.id, "🏠 Asosiy menyu:", reply_markup=main_menu_keyboard())

    # Matn tarjima qilish
    @bot.message_handler(func=lambda message:
        bool(getattr(message, "text", None))
        and not message.text.startswith("/")  # komandalarni chetlab o‘tish (/database, /start va h.k.)
        and message.from_user.id in user_languages
        and message.text not in [
            "🌐 Translate",
            "🔄 Tilni o'zgartirish",
            "📊 Statistikam",
            "🔙 Asosiy menyu",
            "💾 Backup",
            "♻️ Restore",
            "⬅️ Ortga",
        ])
    def translate_text(message):
        user_id = message.from_user.id
        lang_pair = user_languages[user_id]
        src, dest = lang_pair.split("-")

        try:
            # Tarjima qilish
            translated = GoogleTranslator(source=src, target=dest).translate(message.text)

            # Statistika
            user_stats[user_id] = user_stats.get(user_id, 0) + 1

            # Javob
            response = f"""
🔤 **Tarjima:**

📝 Asl matn: `{message.text}`
🌐 Tarjima: `{translated}`
"""
            bot.send_message(message.chat.id, response, parse_mode='Markdown')

            # Ovozli xabar
            try:
                tts = gTTS(translated, lang=dest)
                file_path = f"voice_{user_id}.mp3"
                tts.save(file_path)

                with open(file_path, "rb") as audio:
                    bot.send_voice(message.chat.id, audio)

                os.remove(file_path)
            except Exception as e:
                print(f"Ovozli xabar xatosi: {e}")

            # Reaksiya
            try:
                reaction = random.choice(REACTIONS)
                bot.set_message_reaction(message.chat.id, message.id, reaction=[reaction])
            except:
                pass

        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Xatolik: {str(e)}")
