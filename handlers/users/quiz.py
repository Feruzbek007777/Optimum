import os
import json
import random
import time
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.points import add_points

# Har bir foydalanuvchi uchun quiz session ma'lumoti
# {
#   user_id: {
#       "subject": "eng"/"rus"/"arab"/"bio"/"math",
#       "level": "easy"/"hard",
#       "correct_index": int,
#       "points": int/float,
#       "options_count": int,
#       "questions_answered": int,
#       "last_message_id": int,
#       "answered": bool
#   }
# }
quiz_sessions = {}

# Root papkani aniqlaymiz (Optimum/)
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
QUIZ_DIR = os.path.join(ROOT_DIR, "data", "quiz")

# Fanlar ro'yxati va fayllar
QUIZ_SUBJECTS = {
    "eng": {
        "name": "Ingliz tili",
        "easy_file": "english_easy.json",
        "hard_file": "english_hard.json",
    },
    "rus": {
        "name": "Rus tili",
        "easy_file": "russian_easy.json",
        "hard_file": "russian_hard.json",
    },
    "arab": {
        "name": "Arab tili",
        "easy_file": "arabic_easy.json",
        "hard_file": "arabic_hard.json",
    },
    "bio": {
        "name": "Biologiya",
        "easy_file": "biology_easy.json",
        "hard_file": "biology_hard.json",
    },
    "math": {
        "name": "Matematika",
        "easy_file": "math_easy.json",
        "hard_file": "math_hard.json",
    },
}

# Transition uchun motivatsion matnlar (random beriladi)
MOTIVATION_MESSAGES = [
    "🔄 Yangi savol yuklanmoqda…",
    "💡 Ajoyib! Bilimlaringiz kuchaymoqda…",
    "👉 Keyingi savolga tayyormisiz? 😊",
    "🔥 Har bir savol — yangi skill!",
    "📚 Zo’r ketayapsiz, davom etamiz!",
    "🚀 Har bir javob sizni oldinga olib chiqadi!",
    "🎯 Diqqatni jamlang, navbatdagi savol kelmoqda…"
]

# 7-savoldan keyingi ogohlantirish matni (2-variant)
ANTI_SPAM_WARNING = (
    "⚠️ Ogohlantirish: “ko‘p bosdim = ko‘p bal” ishlamaydi 😄 "
    "Tasodifiy bosilgan javoblar sizni yetakchi qatoriga olib chiqmaydi. "
    "Yaxshisi, sekinroq, lekin to‘g‘ri yeching ✅"
)

# 🔥 Ball qoidalari
EASY_CORRECT = 1.0
EASY_WRONG = -0.2

HARD_CORRECT = 3.0
HARD_WRONG = -0.5


def _fmt_points(x: float) -> str:
    """
    0.2, 0.5, 0.8 ko'rinishda chiqarish uchun.
    """
    try:
        s = f"{float(x):.2f}".rstrip("0").rstrip(".")
        return s
    except Exception:
        return str(x)


def load_questions(subject_key: str, level: str):
    """
    JSON'dan savollarni o'qish.
    ✅ Fayl yo'q / JSON xato / format xato bo'lsa: jim, [] qaytaradi.
    """
    subject = QUIZ_SUBJECTS.get(subject_key)
    if not subject:
        return []

    filename = subject["easy_file"] if level == "easy" else subject["hard_file"]
    path = os.path.join(QUIZ_DIR, filename)

    if not os.path.exists(path):
        return []

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            return []
        return data
    except Exception:
        # ✅ silent
        return []


def build_subject_keyboard():
    kb = InlineKeyboardMarkup(row_width=2)
    buttons = [
        InlineKeyboardButton("🇬🇧 Ingliz tili", callback_data="quiz_subj|eng"),
        InlineKeyboardButton("🇷🇺 Rus tili", callback_data="quiz_subj|rus"),
        InlineKeyboardButton("🇸🇦 Arab tili", callback_data="quiz_subj|arab"),
        InlineKeyboardButton("🧬 Biologiya", callback_data="quiz_subj|bio"),
        InlineKeyboardButton("➗ Matematika", callback_data="quiz_subj|math"),
        InlineKeyboardButton("⬅️ Ortga", callback_data="quiz_back|menu"),
    ]
    kb.add(*buttons)
    return kb


def build_level_keyboard(subject_key: str):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("🟢 Oson", callback_data=f"quiz_lvl|{subject_key}|easy"),
        InlineKeyboardButton("🔴 Qiyin", callback_data=f"quiz_lvl|{subject_key}|hard"),
    )
    kb.add(
        InlineKeyboardButton("⬅️ Ortga", callback_data="quiz_back|subject")
    )
    return kb


def build_options_keyboard(options, subject_key: str, level: str):
    kb = InlineKeyboardMarkup(row_width=2)
    buttons = []
    for idx, opt in enumerate(options):
        buttons.append(
            InlineKeyboardButton(opt, callback_data=f"quiz_ans|{idx}")
        )
    kb.add(*buttons)
    kb.add(
        InlineKeyboardButton("⬅️ Ortga", callback_data=f"quiz_back|level|{subject_key}")
    )
    return kb


def send_quiz_subject_menu(bot, chat_id):
    kb = build_subject_keyboard()
    bot.send_message(
        chat_id,
        "📝 Quiz bo'limi:\n\nFanni tanlang 👇",
        reply_markup=kb
    )


def send_quiz_level_menu(bot, chat_id, subject_key: str):
    subject = QUIZ_SUBJECTS.get(subject_key, {}).get("name", "Fan")
    kb = build_level_keyboard(subject_key)
    bot.send_message(
        chat_id,
        f"🔢 {subject} bo'yicha qaysi daraja?\n\n"
        "🟢 Oson — to‘g‘ri: +1 ball | xato: -0.2 ball\n"
        "🔴 Qiyin — to‘g‘ri: +3 ball | xato: -0.5 ball",
        reply_markup=kb
    )


def send_transition(bot, chat_id):
    """
    Har bir savoldan OLDIN 2 sekundlik “transition”:
    typing... + random motiv gap -> 2 sekund -> o'chirish.
    ✅ Xato bo'lsa ham silent.
    """
    try:
        bot.send_chat_action(chat_id, "typing")
        text = random.choice(MOTIVATION_MESSAGES)
        msg = bot.send_message(chat_id, text)
        time.sleep(2)
        try:
            bot.delete_message(chat_id, msg.message_id)
        except Exception:
            pass
    except Exception:
        # ✅ silent
        pass


def send_quiz_question(bot, chat_id, user_id, subject_key: str, level: str):
    """
    Tasodifiy savol yuboradi, quiz_sessions[] ni yangilaydi.
    Har savoldan oldin 2 sekundlik transition ishlaydi.
    """
    questions = load_questions(subject_key, level)
    if not questions:
        bot.send_message(
            chat_id,
            "Bu bo'lim uchun savollar hali qo'shilmagan. Keyinroq qayta urinib ko'ring 😊"
        )
        return

    # Transition (typing + motiv xabar)
    send_transition(bot, chat_id)

    q = random.choice(questions)
    question_text = (q.get("question", "") or "").strip()
    options = q.get("options", [])
    correct_index = q.get("correct_index", 0)

    if not question_text or not options:
        bot.send_message(chat_id, "Savol formatida xato bor.")
        return

    # ball (to'g'ri javob uchun) - penalti pastda
    points = EASY_CORRECT if level == "easy" else HARD_CORRECT

    kb = build_options_keyboard(options, subject_key, level)
    msg = bot.send_message(
        chat_id,
        f"❓ {question_text}",
        reply_markup=kb
    )

    session = quiz_sessions.get(user_id, {})
    questions_answered = session.get("questions_answered", 0)

    quiz_sessions[user_id] = {
        "subject": subject_key,
        "level": level,
        "correct_index": int(correct_index),
        "points": float(points),
        "options_count": len(options),
        "questions_answered": questions_answered,
        "last_message_id": msg.message_id,
        "answered": False,   # 🔥 Bitta savolga bitta javob uchun flag
    }


def setup_quiz_handlers(bot):
    """
    main.py ichida:
        from handlers.users.quiz import setup_quiz_handlers
        ...
        setup_quiz_handlers(bot)
    deb chaqiriladi.
    """

    @bot.message_handler(func=lambda m: m.chat.type == "private" and m.text == "📝 Quiz")
    def handle_quiz_entry(message):
        send_quiz_subject_menu(bot, message.chat.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("quiz_"))
    def handle_quiz_callbacks(call):
        data = call.data

        # Fan tanlash
        if data.startswith("quiz_subj|"):
            _, subj_key = data.split("|", 1)
            if subj_key in QUIZ_SUBJECTS:
                send_quiz_level_menu(bot, call.message.chat.id, subj_key)
            bot.answer_callback_query(call.id)
            return

        # Daraja tanlash
        if data.startswith("quiz_lvl|"):
            _, subj_key, level = data.split("|", 2)
            if subj_key in QUIZ_SUBJECTS and level in ("easy", "hard"):
                user_id = call.from_user.id
                quiz_sessions[user_id] = {
                    "subject": subj_key,
                    "level": level,
                    "correct_index": 0,
                    "points": float(EASY_CORRECT if level == "easy" else HARD_CORRECT),
                    "options_count": 0,
                    "questions_answered": 0,
                    "last_message_id": None,
                    "answered": False,
                }
                send_quiz_question(bot, call.message.chat.id, user_id, subj_key, level)
            bot.answer_callback_query(call.id)
            return

        # Ortga
        if data.startswith("quiz_back|"):
            parts = data.split("|")
            if (len(parts) == 2 and parts[1] in ("menu", "subject")):
                send_quiz_subject_menu(bot, call.message.chat.id)
            elif len(parts) == 3 and parts[1] == "level":
                subj_key = parts[2]
                send_quiz_level_menu(bot, call.message.chat.id, subj_key)
            bot.answer_callback_query(call.id)
            return

        # Javobni tekshirish
        if data.startswith("quiz_ans|"):
            try:
                _, idx_str = data.split("|", 1)
                chosen_idx = int(idx_str)
            except ValueError:
                bot.answer_callback_query(call.id, "Xatolik 😅", show_alert=False)
                return

            user_id = call.from_user.id
            session = quiz_sessions.get(user_id)
            if not session:
                bot.answer_callback_query(
                    call.id,
                    "Iltimos, quizni menyudan boshlasangiz 😊",
                    show_alert=False
                )
                return

            correct_index = session.get("correct_index", 0)
            level = session.get("level", "easy")
            subject_key = session.get("subject", "eng")
            last_msg_id = session.get("last_message_id")
            questions_answered = session.get("questions_answered", 0)

            # 🔥 1) ESKI SAVOLNI BOSSA ham ishlamasin
            if last_msg_id and call.message.message_id != last_msg_id:
                bot.answer_callback_query(call.id, "Bu savol eskirib qolgan 🙂", show_alert=False)
                return

            # 🔥 2) BIR SAVOLGA BIR MARTA JAVOB
            if session.get("answered", False):
                bot.answer_callback_query(call.id, "Bitta savolga bitta javob, jigar 😄", show_alert=False)
                return

            # Lock
            session["answered"] = True
            quiz_sessions[user_id] = session

            # Keyboardni o‘chirib qo'yamiz
            if last_msg_id:
                try:
                    bot.edit_message_reply_markup(
                        chat_id=call.message.chat.id,
                        message_id=last_msg_id,
                        reply_markup=None
                    )
                except Exception:
                    pass

            is_correct = (chosen_idx == correct_index)

            # penalti / reward
            if level == "easy":
                delta = EASY_CORRECT if is_correct else EASY_WRONG
            else:
                delta = HARD_CORRECT if is_correct else HARD_WRONG

            # Ball qo'shish/ayirish (xato bo'lsa ham silent)
            try:
                add_points(user_id, float(delta))
            except Exception:
                pass

            if is_correct:
                feedback_text = f"✅ To'g'ri javob! Sizga +{_fmt_points(delta)} ball berildi."
            else:
                feedback_text = (
                    f"❌ Xato javob! Sizdan {_fmt_points(abs(delta))} ball olindi.\n\n"
                    "Iltimos, sekinroq va to‘g‘ri bajarishga harakat qiling ✅"
                )

            feedback_msg = bot.send_message(call.message.chat.id, feedback_text)

            bot.answer_callback_query(call.id)

            time.sleep(1)

            if last_msg_id:
                try:
                    bot.delete_message(call.message.chat.id, last_msg_id)
                except Exception:
                    try:
                        bot.edit_message_reply_markup(
                            chat_id=call.message.chat.id,
                            message_id=last_msg_id,
                            reply_markup=None
                        )
                    except Exception:
                        pass

            try:
                bot.delete_message(call.message.chat.id, feedback_msg.message_id)
            except Exception:
                pass

            # Savol sonini oshiramiz
            questions_answered += 1
            session["questions_answered"] = questions_answered
            quiz_sessions[user_id] = session

            # 7-savoldan keyin anti-spam warning
            if questions_answered == 7:
                bot.send_message(call.message.chat.id, ANTI_SPAM_WARNING)

            # Yangi savol
            send_quiz_question(
                bot,
                call.message.chat.id,
                user_id,
                subject_key,
                level
            )