import os
import json
import random
import difflib

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.points import add_points

# 🔍 Root papka (Optimum/)
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# 🗂 JSON fayllar papkasi: Optimum/data/fastwords
FASTWORDS_DIR = os.path.join(ROOT_DIR, "data", "fastwords")

"""
Har bir fan uchun JSON fayl nomlari quyidagicha bo‘ladi:

data/fastwords/english_easy.json
data/fastwords/english_hard.json
data/fastwords/arabic_easy.json
data/fastwords/arabic_hard.json
data/fastwords/russian_easy.json
data/fastwords/russian_hard.json
data/fastwords/biology_easy.json
data/fastwords/biology_hard.json
data/fastwords/math_easy.json
data/fastwords/math_hard.json

JSON strukturasi bir necha ko‘rinishni qo‘llab-quvvatlaydi:

1) Oddiy word/translation:

[
  { "word": "apple", "translation": "olma" },
  { "word": "sun", "translation": ["quyosh", "quyosh nuri"] }
]

2) question/answers:

[
  { "question": "apple", "answers": ["olma", "olma meva"] }
]

3) English–Uzbek kalitlari bilan:

[
  { "en": "apple", "uz": "olma" },
  { "en": "book", "uz": "kitob" }
]

Quyidagi kod UCHALA formatni ham bitta standartga o‘giradi:
{ "question": "...", "answers": ["...", ...] }
"""

# Fanlar ro‘yxati (quizdagi fanlarga mos)
SUBJECTS = {
    "english": {
        "title": "🇬🇧 Ingliz tili",
        "file_prefix": "english",
    },
    "arabic": {
        "title": "🇸🇦 Arab tili",
        "file_prefix": "arabic",
    },
    "russian": {
        "title": "🇷🇺 Rus tili",
        "file_prefix": "russian",
    },
    "biology": {
        "title": "🧬 Biologiya",
        "file_prefix": "biology",
    },
    "math": {
        "title": "📐 Matematika",
        "file_prefix": "math",
    },
}

# Darajalar: ballari bilan
LEVELS = {
    "easy": {
        "title": "🟢 Oson (1 ball)",
        "points": 1,
    },
    "hard": {
        "title": "🔴 Qiyin (3 ball)",
        "points": 3,
    },
}

# Foydalanuvchi holatini saqlaymiz
# user_id -> {
#   "subject": "english",
#   "level": "easy",
#   "data": [ { "question": ..., "answers": [...] }, ... ],
#   "current": { "question": ..., "answers": [...] },
# }
FASTWORDS_STATE = {}

# Menyu tugmalari (bosilsa Fastwords rejimidan chiqib ketamiz)
MENU_BUTTON_TEXTS = {
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
    "⬅️ Ortga",
    "🌐 Translate",
    "🔄 Tilni o'zgartirish",
    "📊 Statistikam",
    "🔙 Asosiy menyu",
    "💾 Backup",
    "♻️ Restore",
}


def _load_fastwords_data(subject_key: str, level_key: str):
    """
    JSONdan so'zlarni o‘qib keladi VA umumiy formatga o'tkazadi.
    """
    subject = SUBJECTS.get(subject_key)
    level = LEVELS.get(level_key)
    if not subject or not level:
        return []

    file_name = f"{subject['file_prefix']}_{level_key}.json"
    file_path = os.path.join(FASTWORDS_DIR, file_name)

    if not os.path.exists(file_path):
        print(f"[FASTWORDS] Fayl topilmadi: {file_path}")
        return []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except Exception as e:
        print(f"[FASTWORDS] JSON o‘qishda xato ({file_path}): {e}")
        return []

    data = []
    if not isinstance(raw, list):
        print(f"[FASTWORDS] JSON ro'yxat emas: {file_path}")
        return data

    for item in raw:
        if not isinstance(item, dict):
            continue

        # 🔑 Savol (so'z) uchun turli kalitlarni tekshiramiz
        question = (
            item.get("question")
            or item.get("word")
            or item.get("en")   # english_easy.json / english_hard.json
            or item.get("q")
        )

        # 🔑 Javob(lar) uchun turli kalitlar
        answers_raw = (
            item.get("answers")
            or item.get("answer")
            or item.get("translation")
            or item.get("translations")
            or item.get("uz")   # english_easy / english_hard: uz tarjima
        )

        if not question or not answers_raw:
            continue

        # Javobni listga aylantiramiz
        if isinstance(answers_raw, str):
            answers = [answers_raw]
        elif isinstance(answers_raw, list):
            answers = [str(a) for a in answers_raw if a]
        else:
            continue

        if not answers:
            continue

        data.append({
            "question": str(question),
            "answers": answers,
        })

    print(f"[FASTWORDS] Yuklandi: {file_path}, elementlar soni: {len(data)}")
    return data


def _build_subjects_keyboard() -> InlineKeyboardMarkup:
    """
    Fan tanlash uchun inline keyboard (quizdagi fanlarga o‘xshash).
    """
    kb = InlineKeyboardMarkup(row_width=2)

    order = ["english", "arabic", "russian", "biology", "math"]
    row = []
    for key in order:
        meta = SUBJECTS[key]
        btn = InlineKeyboardButton(
            meta["title"],
            callback_data=f"fast_sub_{key}"
        )
        row.append(btn)
        if len(row) == 2:
            kb.row(*row)
            row = []
    if row:
        kb.row(*row)

    kb.add(
        InlineKeyboardButton("⬅️ Ortga", callback_data="fast_back_main")
    )
    return kb


def _build_levels_keyboard(subject_key: str) -> InlineKeyboardMarkup:
    """
    Oson / Qiyin darajalarini tanlash uchun keyboard.
    """
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton(
            "🟢 Oson (1 ball)",
            callback_data=f"fast_lvl_{subject_key}_easy",
        ),
        InlineKeyboardButton(
            "🔴 Qiyin (3 ball)",
            callback_data=f"fast_lvl_{subject_key}_hard",
        ),
    )
    kb.add(
        InlineKeyboardButton("⬅️ Ortga", callback_data="fast_back_subjects")
    )
    return kb


def _choose_next_word(bot, user_id: int, chat_id: int):
    """
    Navbatdagi so‘zni tanlab, foydalanuvchiga yuboradi.
    """
    state = FASTWORDS_STATE.get(user_id)
    if not state or not state.get("data"):
        bot.send_message(
            chat_id,
            "❌ Bu fan va daraja uchun so‘zlar topilmadi. Admin bilan bog‘laning."
        )
        FASTWORDS_STATE.pop(user_id, None)
        return

    item = random.choice(state["data"])
    state["current"] = item

    subject_title = SUBJECTS[state["subject"]]["title"]
    level_title = LEVELS[state["level"]]["title"]

    text = (
        f"⚡️ *Tezkor mashq* — {subject_title}\n"
        f"{level_title}\n\n"
        f"✍️ So'z: *{item['question']}*\n\n"
        "Tarjima variantini yozing:"
    )

    bot.send_message(
        chat_id,
        text,
        parse_mode="Markdown"
    )


def _is_correct_answer(user_answer: str, answers: list[str]) -> bool:
    """
    User javobi to'g'ri yoki yo‘qligini tekshiramiz.
    80% o‘xshashlik bo‘lsa ham to‘g'ri deb hisoblaymiz.
    """
    user_answer = user_answer.strip().lower()
    if not user_answer:
        return False

    for ans in answers:
        ans_norm = ans.strip().lower()
        if not ans_norm:
            continue

        if user_answer == ans_norm:
            return True

        ratio = difflib.SequenceMatcher(None, user_answer, ans_norm).ratio()
        if ratio >= 0.8:
            return True

    return False


def setup_fastwords_handlers(bot):
    """
    Fast Words (⚡️ Tezkor mashq) uchun barcha handlerlar.
    main.py ichida:
        from handlers.users.fastwords import setup_fastwords_handlers
        ...
        setup_fastwords_handlers(bot)
    """

    # 🎛 Menyudan Fast words tugmasi bosilganda
    @bot.message_handler(
        func=lambda m: m.chat.type == "private" and m.text == "⚡️ Tezkor mashq"
    )
    def open_fastwords_menu(message):
        kb = _build_subjects_keyboard()
        bot.send_message(
            message.chat.id,
            "⚡️ Tezkor mashq bo'limi.\n\n"
            "Avval fanni tanlang:",
            reply_markup=kb
        )

    # 📚 Fan tanlash callback'i
    @bot.callback_query_handler(func=lambda call: call.data.startswith("fast_sub_"))
    def handle_fast_subject(call):
        subject_key = call.data.replace("fast_sub_", "", 1)
        if subject_key not in SUBJECTS:
            bot.answer_callback_query(call.id, "❌ Noto‘g‘ri fan tanlandi.")
            return

        kb = _build_levels_keyboard(subject_key)
        subject_title = SUBJECTS[subject_key]["title"]

        try:
            bot.edit_message_text(
                f"⚡️ Tezkor mashq — {subject_title}\n\n"
                "Darajani tanlang:",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=kb
            )
        except Exception as e:
            # Agar edit ishlamasa, yangi xabar jo'natamiz
            print(f"[FASTWORDS] edit_message_text xatosi: {e}")
            bot.send_message(
                call.message.chat.id,
                f"⚡️ Tezkor mashq — {subject_title}\n\n"
                "Darajani tanlang:",
                reply_markup=kb
            )

        bot.answer_callback_query(call.id)

    # ↩️ Fanlar menyusiga ortga
    @bot.callback_query_handler(func=lambda call: call.data == "fast_back_subjects")
    def handle_back_subjects(call):
        kb = _build_subjects_keyboard()
        try:
            bot.edit_message_text(
                "⚡️ Tezkor mashq bo'limi.\n\n"
                "Avval fanni tanlang:",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=kb
            )
        except Exception as e:
            print(f"[FASTWORDS] back_subjects edit xatosi: {e}")
            bot.send_message(
                call.message.chat.id,
                "⚡️ Tezkor mashq bo'limi.\n\n"
                "Avval fanni tanlang:",
                reply_markup=kb
            )
        bot.answer_callback_query(call.id)

    # ↩️ Asosiy sovg'a menyusiga ortga (inline)
    @bot.callback_query_handler(func=lambda call: call.data == "fast_back_main")
    def handle_back_main_from_inline(call):
        from keyboards.default import gift_menu_keyboard
        user_id = call.from_user.id
        # Fastwords rejimini to'xtatamiz
        FASTWORDS_STATE.pop(user_id, None)

        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(
            call.message.chat.id,
            "🎁 Sovg'a bo'limiga qaytdingiz.",
            reply_markup=gift_menu_keyboard()
        )
        bot.answer_callback_query(call.id)

    # ⭐ Daraja tanlash (easy / hard)
    @bot.callback_query_handler(func=lambda call: call.data.startswith("fast_lvl_"))
    def handle_fast_level(call):
        parts = call.data.split("_")
        # ["fast", "lvl", "{subject}", "{level}"]
        if len(parts) != 4:
            bot.answer_callback_query(call.id, "❌ Noto‘g‘ri format.")
            return

        subject_key = parts[2]
        level_key = parts[3]

        if subject_key not in SUBJECTS or level_key not in LEVELS:
            bot.answer_callback_query(call.id, "❌ Noto‘g‘ri fan yoki daraja.")
            return

        user_id = call.from_user.id
        chat_id = call.message.chat.id

        data = _load_fastwords_data(subject_key, level_key)
        if not data:
            bot.answer_callback_query(call.id, "❌ Bu bo‘lim uchun so‘zlar topilmadi.")
            bot.send_message(
                chat_id,
                "❌ Bu fan va daraja uchun so‘zlar topilmadi.\n"
                "Admin bilan bog‘laning yoki keyinroq qayta urinib ko‘ring."
            )
            return

        FASTWORDS_STATE[user_id] = {
            "subject": subject_key,
            "level": level_key,
            "data": data,
            "current": None,
        }

        subject_title = SUBJECTS[subject_key]["title"]
        level_title = LEVELS[level_key]["title"]

        bot.answer_callback_query(
            call.id,
            f"{subject_title} — {level_title} boshlandi! ✍️",
            show_alert=False
        )

        # So'z berishni boshlaymiz
        _choose_next_word(bot, user_id, chat_id)

    # ✍️ Foydalanuvchi javob yozganda (Tezkor mashq rejimida bo‘lsa)
    @bot.message_handler(
        func=lambda m: m.chat.type == "private" and m.from_user.id in FASTWORDS_STATE
    )
    def handle_fastwords_answer(message):
        user_id = message.from_user.id
        state = FASTWORDS_STATE.get(user_id)

        # Agar holat bo'lmasa yoki current yo'q bo‘lsa – hech narsa qilmaymiz
        if not state or not state.get("current"):
            return

        text = (message.text or "").strip()
        if not text:
            return

        # ✅ Agar menyu tugmasi yoki /komanda bo‘lsa:
        #  → Fastwords rejimini O'CHIRAMIZ va javob QAYTARMAYMIZ
        if text.startswith("/") or text in MENU_BUTTON_TEXTS:
            FASTWORDS_STATE.pop(user_id, None)
            return

        current = state["current"]
        answers = current["answers"]

        is_correct = _is_correct_answer(text, answers)
        level_key = state["level"]
        level_cfg = LEVELS[level_key]
        added_points = level_cfg["points"]

        if is_correct:
            # ✅ To'g'ri javob — ball qo‘shamiz
            try:
                add_points(user_id, added_points)
            except Exception as e:
                print(f"[FASTWORDS] add_points xatosi: {e}")

            correct_text = "✅ To'g'ri! "
            if level_key == "easy":
                correct_text += f"+{added_points} ball (oson daraja)."
            else:
                correct_text += f"+{added_points} ball (qiyin daraja)."

            bot.send_message(
                message.chat.id,
                correct_text
            )
        else:
            # ❌ Noto'g'ri javob — faqat to'g'ri variant(lar)ni ko'rsatamiz
            answers_str = ", ".join(answers)
            bot.send_message(
                message.chat.id,
                f"❌ To'g'ri emas.\n✅ To'g'ri javob(lar):  {answers_str}"
            )

        # Keyingi so'z
        _choose_next_word(bot, user_id, message.chat.id)
