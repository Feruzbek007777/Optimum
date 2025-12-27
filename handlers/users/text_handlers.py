from config import CONTACT_INFO
from keyboards.default import main_menu_keyboard, gift_menu_keyboard
from keyboards.inline import generate_courses_keyboard
from database.database import (
    get_announcements,
    get_gift_likes_count,
    get_referrals_count,
)
from handlers.users.top_users import format_top_users
from utils.points import get_points, get_top_users

# ✅ safe yuborish (403/429 botni yiqitmasin)
import time
from utils.safe_telegram import safe_send_message, safe_send_photo


# ✅ oddiy cooldown (user spam bosmasin)
_LAST_ACTION = {}


def _is_rate_limited(user_id: int, key: str, cooldown: float = 1.2) -> bool:
    now = time.time()
    k = (user_id, key)
    last = _LAST_ACTION.get(k, 0)
    if now - last < cooldown:
        return True
    _LAST_ACTION[k] = now
    return False


def setup_user_text_handlers(bot):
    """
    Foydalanuvchilar uchun text handlerlar.
    """

    def format_user_stats(user_id: int, username: str | None, full_name: str | None) -> str:
        points = get_points(user_id)
        referrals_count = get_referrals_count(user_id)

        rows = get_top_users(limit=1000)
        rank = None
        total_users = len(rows)

        for idx, (u_id, u_username, u_full_name, u_points, u_refs) in enumerate(rows, start=1):
            if u_id == user_id:
                rank = idx
                break

        name_part = (full_name or "").strip()
        if username:
            if name_part:
                name_part = f"{name_part} (@{username})"
            else:
                name_part = f"@{username}"
        if not name_part:
            name_part = f"ID: {user_id}"

        if rank is not None:
            if total_users > 0:
                rank_text = f"{rank}-o‘rinda (jami {total_users} ta foydalanuvchi ichida)"
            else:
                rank_text = "Reytingda ishtirokchilar soni hali kam."
        else:
            if total_users == 0:
                rank_text = "Hali reytingda foydalanuvchilar yo‘q."
            else:
                rank_text = "Hali umumiy reytingda ko‘rinadigan darajada ball yo‘q 🙂"

        text = (
            "📊 Sizning statistikangiz\n\n"
            f"👤 Foydalanuvchi: {name_part}\n"
            f"💰 Ballaringiz: {points}\n"
            f"🤝 Takliflaringiz soni: {referrals_count}\n"
            f"🏆 Reytingdagi holatingiz: {rank_text}\n\n"
            "🎯 Ko‘proq quiz yeching, Tezkor so'zlar bajaring va do‘stlaringizni taklif qiling —\n"
            "ballaringiz tez o‘sadi! 🚀"
        )
        return text

    # 📚 Kurslar haqida ma'lumot
    @bot.message_handler(func=lambda m: m.chat.type == "private" and m.text == "📚 Kurslar haqida ma'lumot")
    def handle_courses_info(message):
        if _is_rate_limited(message.from_user.id, "courses_info", 0.8):
            return

        kb = generate_courses_keyboard(action="info")
        safe_send_message(
            bot,
            message.chat.id,
            "📚 Qaysi kurs haqida ma'lumot olishni xohlaysiz?",
            reply_markup=kb
        )

    # 📝 Kursga yozilish
    @bot.message_handler(func=lambda m: m.chat.type == "private" and m.text == "📝 Kursga yozilish")
    def handle_course_register(message):
        if _is_rate_limited(message.from_user.id, "course_register", 0.8):
            return

        kb = generate_courses_keyboard(action="register")
        safe_send_message(
            bot,
            message.chat.id,
            "📝 Qaysi kursga yozilmoqchisiz?\nKursni tanlang 👇",
            reply_markup=kb
        )

    # 📞 Biz bilan bog'lanish
    @bot.message_handler(func=lambda m: m.chat.type == "private" and m.text == "📞 Biz bilan bog'lanish")
    def handle_contact(message):
        if _is_rate_limited(message.from_user.id, "contact", 0.8):
            return

        safe_send_message(
            bot,
            message.chat.id,
            CONTACT_INFO,
            reply_markup=main_menu_keyboard()
        )

    # 📢 E'lonlar
    @bot.message_handler(func=lambda m: m.chat.type == "private" and m.text == "📢 E'lonlar")
    def handle_announcements(message):
        if _is_rate_limited(message.from_user.id, "announcements", 2.0):
            return

        announcements = get_announcements()
        if not announcements:
            # ✅ FIX: bot parametri qo'shildi
            safe_send_message(
                bot,
                message.chat.id,
                "Hozircha e'lonlar yo'q.",
                reply_markup=main_menu_keyboard()
            )
            return

        for text, image_path in announcements:
            if image_path:
                try:
                    with open(image_path, "rb") as img:
                        safe_send_photo(bot, message.chat.id, img, caption=text)
                except FileNotFoundError:
                    safe_send_message(bot, message.chat.id, text)
            else:
                safe_send_message(bot, message.chat.id, text)

    # 🎁 Sovg'a yutish bo'limi + ❤️ like tugmasi
    @bot.message_handler(func=lambda m: m.chat.type == "private" and m.text == "🎁 Sovg'a yutish")
    def open_gift_menu(message):
        if _is_rate_limited(message.from_user.id, "gift_menu", 1.5):
            return

        likes_count = get_gift_likes_count()
        like_text = f"❤️ {likes_count}"

        intro_text = (
            "🎁 Sovg'a yutish bo'limi:\n\n"
            "Bu yerda siz:\n"
            "• 🧪 Quiz yechib ball to'playsiz\n"
            "• 🤝 Do'stlarni taklif qilib bonus olasiz\n"
            "• ⚡ Tezkor so'zlar bilan ingliz so'zlarini mustahkamlaysiz\n\n"
            "Like bosib bizni qo‘llab-quvvatlang 👇"
        )

        from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
        inline_kb = InlineKeyboardMarkup(row_width=1)
        inline_kb.add(
            InlineKeyboardButton(like_text, callback_data="gift_like")
        )

        safe_send_message(
            bot,
            message.chat.id,
            intro_text,
            reply_markup=inline_kb
        )

        safe_send_message(
            bot,
            message.chat.id,
            "Bo'limlardan birini tanlang 👇",
            reply_markup=gift_menu_keyboard()
        )

    # 📊 Mening ballarim
    @bot.message_handler(func=lambda m: m.chat.type == "private" and m.text == "📊 Mening ballarim")
    def handle_my_points(message):
        if _is_rate_limited(message.from_user.id, "my_points", 1.0):
            return

        user = message.from_user
        full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()

        text = format_user_stats(
            user_id=user.id,
            username=user.username,
            full_name=full_name
        )

        safe_send_message(
            bot,
            message.chat.id,
            text,
            reply_markup=gift_menu_keyboard()
        )

    # ⬅️ Ortga tugmasi (asosiy menyuga qaytish)
    @bot.message_handler(func=lambda m: m.chat.type == "private" and m.text == "⬅️ Ortga")
    def back_to_main_menu(message):
        if _is_rate_limited(message.from_user.id, "back_main", 1.0):
            return

        safe_send_message(
            bot,
            message.chat.id,
            "🏠 Asosiy menyuga qaytdingiz.",
            reply_markup=main_menu_keyboard()
        )

    # 🏆 Top foydalanuvchilar tugmasi
    @bot.message_handler(func=lambda m: m.chat.type == "private" and m.text == "🏆 Top foydalanuvchilar")
    def show_top_users_handler(message):
        if _is_rate_limited(message.from_user.id, "top_users", 1.2):
            return

        text = format_top_users()
        safe_send_message(
            bot,
            message.chat.id,
            text,
            reply_markup=main_menu_keyboard()
        )
