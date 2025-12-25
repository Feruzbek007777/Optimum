import os
from database.database import add_course_video_view, get_course_video_views_count


# Root papkani aniqlaymiz (Optimum/)
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# course_video/course_vid...
COURSE_VIDEO_DIR = os.path.join(ROOT_DIR, "course_video")

CANDIDATE_FILES = [
    "course_vid.mp4",
    "course_vid.mov",
    "course_vid.mkv",
    "course_vid.avi",
    "course_vid",
]

# Telegram Bot API limitlari o'zgarishi mumkin, lekin amalda ko'p serverlarda 50MB/20MB muammo bo'ladi.
# Shuning uchun juda katta bo'lsa userga ogohlantiramiz.
MAX_HINT_MB = 1900  # 1.9GB (ko'p hollarda limitdan katta bo'ladi)


def _find_video_path():
    for name in CANDIDATE_FILES:
        path = os.path.join(COURSE_VIDEO_DIR, name)
        if os.path.exists(path) and os.path.isfile(path):
            return path
    return None


def _build_caption(view_count: int) -> str:
    text = (
        "🎬 *Kurs Prezentatsiyasi (Video)*\n\n"
        "Bu videoda kurs nima beradi, kimlar uchun, va qanday natija olishingiz mumkin — hammasi tushuntirilgan.\n\n"
        "📌 *Batafsil ma’lumot uchun:*\n"
        "☎️ Telefon: `+998 90 630 6674`\n"
        "💬 Telegram: @fellixboi\n\n"
        f"👀 *Ko‘rganlar soni:* {view_count} ta"
    )
    return text


def setup_course_video_handlers(bot):

    @bot.message_handler(commands=['video'])
    def cmd_video(message):
        if message.chat.type != "private":
            bot.reply_to(message, "Bu buyruqni faqat shaxsiy chatda ishlating.")
            return

        user_id = message.from_user.id
        chat_id = message.chat.id

        # unique view
        add_course_video_view(user_id)
        view_count = get_course_video_views_count()

        caption = _build_caption(view_count)
        video_path = _find_video_path()

        if not video_path:
            bot.send_message(
                chat_id,
                caption + "\n\n⏳ Video hozircha yuklanmagan. Tez orada shu yerga tashlanadi.",
                parse_mode="Markdown"
            )
            return

        # fayl hajmi (diagnostika + limit haqida ogohlantirish)
        try:
            size_bytes = os.path.getsize(video_path)
            size_mb = size_bytes / (1024 * 1024)
        except Exception:
            size_mb = None

        if size_mb and size_mb > MAX_HINT_MB:
            bot.send_message(
                chat_id,
                "❌ Video juda katta ko‘rinadi. Telegram orqali yuborish qiyin bo‘lishi mumkin.\n\n"
                "Yechim: videoni siqib (compress) MP4 qiling yoki 1 marta yuborib `file_id` saqlab qo‘yamiz.",
            )
            # baribir urinib ko'ramiz (xohlasangiz shu yerda return qiling)
            # return

        # upload action
        try:
            bot.send_chat_action(chat_id, "upload_video")
        except Exception:
            pass

        # 1) Avval send_video
        try:
            with open(video_path, "rb", buffering=0) as f:
                bot.send_video(
                    chat_id,
                    f,
                    caption=caption,
                    parse_mode="Markdown",
                    timeout=600  # ✅ timeoutni katta qildik
                )
            return
        except Exception as e:
            print(f"/video send_video xato: {e}")

        # 2) Fallback: send_document (ko'p serverlarda stabilroq)
        try:
            with open(video_path, "rb", buffering=0) as f:
                bot.send_document(
                    chat_id,
                    f,
                    caption=caption,
                    parse_mode="Markdown",
                    timeout=600
                )
            return
        except Exception as e2:
            print(f"/video send_document xato: {e2}")

        # 3) Oxirgi xabar
        bot.send_message(
            chat_id,
            "❌ Videoni yuborishda timeout bo‘lyapti.\n\n"
            "Eng ishonchli yechim: videoni 1 marta bot orqali yuboramiz va `file_id`ni saqlab qo'yamiz — "
            "keyin hamma userlarga uploadsiz tez yuboriladi.\n"
            "Agar xohlasangiz, shu `file_id` variantini ham qilib beraman.",
        )
