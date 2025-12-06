import os
import random

from telebot.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from deep_translator import GoogleTranslator
from gtts import gTTS

# Menyu tugmalarini translate'dan himoya qilish uchun ro'yxat
BUTTON_TEXTS_EXCLUDE = [
    "🌐 Translate",
    "🔄 Tilni o'zgartirish",
    "📊 Statistikam",
    "🔙 Asosiy menyu",
    "💾 Backup",
    "♻️ Restore",
    "⬅️ Ortga",

    # Asosiy menyu / sovg'a menyusi tugmalari
    "📚 Kurslar haqida ma'lumot",
    "📝 Kursga yozilish",
    "📞 Biz bilan bog'lanish",
    "📢 E'lonlar",
    "🎁 Sovg'a yutish",
    "🧪 Quiz",
    "⚡️ Tezkor mashq",
    "🤝 Takliflarim",
    "📊 Mening ballarim",
    "🏆 Top foydalanuvchilar",
]

# Foydalanuvchi tanlagan tillarni saqlash
user_languages = {}
user_stats = {}

# Tarjima natijalari uchun kontekst:
# key: (chat_id, message_id) -> {"text": translated_text, "lang": dest_lang}
translation_context = {}

# Random reaksiyalar (odatiy emoji yuboramiz)
REACTIONS = ["👍", "🔥", "🤩", "👌", "❤️", "🥳"]

# gTTS til kodlari:
TTS_LANG_MAP = {
    "en": "en",
    "ru": "ru",
    "ar": "ar",
    # "uz" yo‘q → "en"ga fallback
}


def send_positive_reaction(bot, message):
    """
    ReactionTypeEmoji serverda ishlamagani uchun —
    shunchaki bitta random emoji yuboramiz.
    """
    try:
        emoji = random.choice(REACTIONS)
        bot.send_message(message.chat.id, emoji)
    except Exception as e:
        print(f"Reaction qo'yishda xatolik: {e}")


def get_translate_keyboard():
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
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(
        KeyboardButton("🔄 Tilni o'zgartirish"),
        KeyboardButton("📊 Statistikam")
    )
    keyboard.add(KeyboardButton("🔙 Asosiy menyu"))
    return keyboard


def get_voice_button_keyboard():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("🔊 Ovoz", callback_data="tr_voice"))
    return kb


def get_back_button_keyboard():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("⬅️ Ortga", callback_data="tr_back"))
    return kb


def setup_translate_handlers(bot):

    @bot.message_handler(func=lambda message: message.text == "🌐 Translate")
    def translate_menu(message):
        keyboard = get_translate_keyboard()
        bot.send_message(
            message.chat.id,
            "🌐 Tarjima qilish uchun tilni tanlang:",
            reply_markup=keyboard
        )

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
            f"✅ {lang_names[lang_pair]}\n\n"
            "✍️ Endi yuboradigan matnlaringiz tarjima qilinadi.\n"
            "Boshqa bo‘lim tugmasini bossangiz — translate rejimi o‘chadi.",
            reply_markup=get_translate_menu()
        )

    @bot.message_handler(func=lambda message: message.text == "🔄 Tilni o'zgartirish")
    def change_language(message):
        bot.send_message(message.chat.id, "🌐 Yangi tilni tanlang:", reply_markup=get_translate_keyboard())

    @bot.message_handler(func=lambda message: message.text == "📊 Statistikam")
    def show_stats(message):
        count = user_stats.get(message.from_user.id, 0)
        bot.send_message(message.chat.id, f"📊 Siz hozirgacha {count} marta tarjima qildingiz!")

    @bot.message_handler(func=lambda message: message.text == "🔙 Asosiy menyu")
    def back_to_main(message):
        from keyboards.default import main_menu_keyboard
        user_languages.pop(message.from_user.id, None)
        bot.send_message(message.chat.id, "🏠 Asosiy menyu:", reply_markup=main_menu_keyboard())

    # 🔊 Voice va ortga tugma
    @bot.callback_query_handler(func=lambda call: call.data in ("tr_voice", "tr_back"))
    def handle_result_callbacks(call):

        if call.data == "tr_voice":
            key = (call.message.chat.id, call.message.message_id)
            ctx = translation_context.get(key)
            if not ctx:
                bot.answer_callback_query(call.id, "❌ Tarjima matni topilmadi.")
                return

            translated = ctx["text"]
            dest = ctx["lang"]

            tts_lang = TTS_LANG_MAP.get(dest, "en")

            try:
                tts = gTTS(translated, lang=tts_lang)
                file_path = f"voice_tr_{call.from_user.id}.mp3"
                tts.save(file_path)

                with open(file_path, "rb") as audio:
                    sent_voice = bot.send_voice(
                        call.message.chat.id,
                        audio,
                        caption=translated,
                        reply_markup=get_back_button_keyboard()
                    )

                os.remove(file_path)
                ctx["last_voice_id"] = sent_voice.message_id if sent_voice else None
                translation_context[key] = ctx

                bot.answer_callback_query(call.id, "🔊 Ovoz yuborildi.")
            except Exception as e:
                print(f"Ovozli xabar xatosi: {e}")
                bot.answer_callback_query(call.id, "❌ Ovoz yaratishda xatolik.")

        else:
            try:
                bot.delete_message(call.message.chat.id, call.message.message_id)
            except Exception as e:
                print(f"Ovoz xabarini o'chirishda xatolik: {e}")
            bot.answer_callback_query(call.id, "⬅️ Ovoz o'chirildi.")

    # 🔤 Matn tarjima handler
    @bot.message_handler(
        func=lambda message:
        message.chat.type == "private"
        and bool(getattr(message, "text", None))
        and message.from_user.id in user_languages
        and message.text not in BUTTON_TEXTS_EXCLUDE
        and not message.text.startswith("/")
    )
    def translate_text(message):
        user_id = message.from_user.id
        text = (message.text or "").strip()

        lang_pair = user_languages.get(user_id)
        if not lang_pair:
            return

        src, dest = lang_pair.split("-")

        send_positive_reaction(bot, message)

        try:
            translated = GoogleTranslator(source=src, target=dest).translate(text)
            user_stats[user_id] = user_stats.get(user_id, 0) + 1

            response = (
                "🔤 Tarjima:\n\n"
                f"📝 Asl matn: {text}\n"
                f"🌐 Tarjima: {translated}\n\n"
                "🔊 Ovozini eshitish uchun pastdagi tugmani bosing 👇"
            )

            sent = bot.send_message(
                message.chat.id,
                response,
                reply_markup=get_voice_button_keyboard()
            )

            translation_context[(sent.chat.id, sent.message_id)] = {
                "text": translated,
                "lang": dest,
            }

        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Xatolik: {str(e)}")
