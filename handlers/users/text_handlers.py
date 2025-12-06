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


def setup_user_text_handlers(bot):
    """
    Foydalanuvchilar uchun text handlerlar.
    main.py ichida:
        from handlers.users.text_handlers import setup_user_text_handlers
        ...
        setup_user_text_handlers(bot)
    deb chaqiriladi.
    """

    # ✅ Foydalanuvchi statistikasi formatlovchi ichki funksiya
    def format_user_stats(user_id: int, username: str | None, full_name: str | None) -> str:
        """
        Foydalanuvchi uchun chiroyli statistik matn:
        - ismi
        - username
        - ballari
        - takliflar soni
        - top bo'yicha taxminiy o'rni
        """
        points = get_points(user_id)
        referrals_count = get_referrals_count(user_id)

        # Top ro'yxatidan taxminiy rankni aniqlash
        rows = get_top_users(limit=1000)  # (user_id, username, full_name, points, referrals_count)
        rank = None
        total_users = len(rows)

        for idx, (u_id, u_username, u_full_name, u_points, u_refs) in enumerate(rows, start=1):
            if u_id == user_id:
                rank = idx
                break

        # Foydalanuvchi nomi
        name_part = (full_name or "").strip()
        if username:
            if name_part:
                name_part = f"{name_part} (@{username})"
            else:
                name_part = f"@{username}"
        if not name_part:
            name_part = f"ID: {user_id}"

        # Rank matni
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
        kb = generate_courses_keyboard(action="info")
        bot.send_message(
            message.chat.id,
            "📚 Qaysi kurs haqida ma'lumot olishni xohlaysiz?",
            reply_markup=kb
        )

    # 📝 Kursga yozilish
    @bot.message_handler(func=lambda m: m.chat.type == "private" and m.text == "📝 Kursga yozilish")
    def handle_course_register(message):
        kb = generate_courses_keyboard(action="register")
        bot.send_message(
            message.chat.id,
            "📝 Qaysi kursga yozilmoqchisiz?\nKursni tanlang 👇",
            reply_markup=kb
        )

    # 📞 Biz bilan bog'lanish
    @bot.message_handler(func=lambda m: m.chat.type == "private" and m.text == "📞 Biz bilan bog'lanish")
    def handle_contact(message):
        bot.send_message(
            message.chat.id,
            CONTACT_INFO,
            reply_markup=main_menu_keyboard()
        )

    # 📢 E'lonlar
    @bot.message_handler(func=lambda m: m.chat.type == "private" and m.text == "📢 E'lonlar")
    def handle_announcements(message):
        announcements = get_announcements()
        if not announcements:
            bot.send_message(message.chat.id, "Hozircha e'lonlar yo'q.", reply_markup=main_menu_keyboard())
            return

        for text, image_path in announcements:
            if image_path:
                try:
                    with open(image_path, "rb") as img:
                        bot.send_photo(message.chat.id, img, caption=text)
                except FileNotFoundError:
                    bot.send_message(message.chat.id, text)
            else:
                bot.send_message(message.chat.id, text)

    # 🎁 Sovg'a yutish bo'limi + ❤️ like tugmasi
    @bot.message_handler(func=lambda m: m.chat.type == "private" and m.text == "🎁 Sovg'a yutish")
    def open_gift_menu(message):
        # Jami likelar sonini olamiz
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

        # 1-xabar: matn + ❤️ inline tugma (olovcha effekt bilan)
        bot.send_message(
            message.chat.id,
            intro_text,
            reply_markup=inline_kb
        )

        # 2-xabar: odatdagi menyu tugmalari
        bot.send_message(
            message.chat.id,
            "Bo'limlardan birini tanlang 👇",
            reply_markup=gift_menu_keyboard()
        )

    # 📊 Mening ballarim
    @bot.message_handler(func=lambda m: m.chat.type == "private" and m.text == "📊 Mening ballarim")
    def handle_my_points(message):
        user = message.from_user
        full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()

        text = format_user_stats(
            user_id=user.id,
            username=user.username,
            full_name=full_name
        )

        bot.send_message(
            message.chat.id,
            text,
            reply_markup=gift_menu_keyboard()
        )

    # ⬅️ Ortga tugmasi (asosiy menyuga qaytish)
    @bot.message_handler(func=lambda m: m.chat.type == "private" and m.text == "⬅️ Ortga")
    def back_to_main_menu(message):
        bot.send_message(
            message.chat.id,
            "🏠 Asosiy menyuga qaytdingiz.",
            reply_markup=main_menu_keyboard()
        )

    # 🏆 Top foydalanuvchilar tugmasi
    @bot.message_handler(func=lambda m: m.chat.type == "private" and m.text == "🏆 Top foydalanuvchilar")
    def show_top_users_handler(message):
        text = format_top_users()
        bot.send_message(message.chat.id, text, reply_markup=main_menu_keyboard())
