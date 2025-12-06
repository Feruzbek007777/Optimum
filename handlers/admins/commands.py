import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

from config import ADMINS
from keyboards.default import main_menu_keyboard, admin_menu_keyboard
from database.database import add_admin_group
from utils.givepoint import find_user_by_username, give_points_to_user
from utils.stats import get_bot_stats


def setup_admin_commands(bot):
    # /start — admin yoki oddiy userga qarab menyu
    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        if message.from_user.id in ADMINS:
            bot.send_message(
                message.chat.id,
                "👨‍💻 Admin menyusiga xush kelibsiz!",
                reply_markup=admin_menu_keyboard()
            )
        else:
            bot.send_message(
                message.chat.id,
                "🤖 Xush kelibsiz! Quyidagi menyudan kerakli bo'limni tanlang:",
                reply_markup=main_menu_keyboard()
            )

    # /admin — faqat adminlar uchun
    @bot.message_handler(commands=['admin'])
    def admin_panel(message):
        if message.from_user.id in ADMINS:
            bot.send_message(
                message.chat.id,
                "👨‍💻 Admin menyusiga xush kelibsiz!",
                reply_markup=admin_menu_keyboard()
            )
        else:
            bot.send_message(message.chat.id, "❌ Sizda admin huquqi yo'q!")

    # /addgroup — qo'lda guruh qo'shish
    @bot.message_handler(commands=['addgroup'])
    def add_group_manual(message):
        if message.from_user.id not in ADMINS:
            bot.send_message(message.chat.id, "❌ Sizda admin huquqi yo'q!")
            return

        try:
            # Format: /addgroup -4902306438 "Guruh Nomi"
            parts = message.text.split(' ', 2)
            if len(parts) < 3:
                bot.send_message(
                    message.chat.id,
                    "❌ Noto'g'ri format!\nTo'g'ri format: /addgroup -4902306438 \"Guruh Nomi\""
                )
                return

            group_id = int(parts[1])
            group_title = parts[2]

            success = add_admin_group(group_id, group_title)

            if success:
                bot.send_message(
                    message.chat.id,
                    f"✅ Guruh muvaffaqiyatli qo'shildi!\nID: {group_id}\nNomi: {group_title}"
                )
            else:
                bot.send_message(message.chat.id, "❌ Guruh qo'shishda xatolik!")
        except (IndexError, ValueError):
            bot.send_message(
                message.chat.id,
                "❌ Noto'g'ri format!\nTo'g'ri format: /addgroup -4902306438 \"Guruh Nomi\""
            )

    # ===================== /givepoint — BALL BERISH =====================

    @bot.message_handler(commands=['givepoint'])
    def cmd_givepoint(message):
        """
        Admin uchun manual ball berish:
        1) /givepoint
        2) @username so'raymiz
        3) ball miqdorini so'raymiz
        4) admin izohini so'raymiz
        5) userga xabar + bazaga ball qo'shamiz
        """
        if message.from_user.id not in ADMINS:
            bot.send_message(message.chat.id, "❌ Sizda bu buyruqni ishlatish huquqi yo'q!")
            return

        msg = bot.send_message(
            message.chat.id,
            "🎯 Ball bermoqchi bo'lgan foydalanuvchining @username'ini yuboring:"
        )
        bot.register_next_step_handler(msg, _gp_step_username)

    def _gp_step_username(message):
        """
        2-bosqich: admin @username yuboradi, biz DB dan userni qidiramiz.
        """
        if message.from_user.id not in ADMINS:
            bot.send_message(message.chat.id, "❌ Bu bo'lim faqat adminlar uchun.")
            return

        raw_username = message.text.strip()
        user = find_user_by_username(raw_username)

        if not user:
            bot.send_message(
                message.chat.id,
                "❌ Bunday username bazada topilmadi.\n"
                "Iltimos, /givepoint ni qaytadan boshlang va to'g'ri @username yuboring."
            )
            return

        user_id, username, full_name, joined_at, pts, refs = user

        display_name = (full_name or "").strip() or "Ismi ko'rsatilmagan"
        username_part = f"@{username}" if username else f"ID: {user_id}"

        text = (
            "✅ Foydalanuvchi topildi:\n\n"
            f"👤 {display_name} ({username_part})\n"
            f"🆔 ID: {user_id}\n"
            f"💰 Hozirgi ballari: {pts}\n"
            f"🤝 Takliflari: {refs}\n\n"
            "Nechta ball beramiz? (masalan: 50, 120, 1000...)"
        )

        msg = bot.send_message(
            message.chat.id,
            text
        )
        # Keyingi bosqichga user ma'lumotlarini uzatamiz
        bot.register_next_step_handler(msg, _gp_step_points, user_id, username, display_name)

    def _gp_step_points(message, user_id, username, display_name):
        """
        3-bosqich: ball miqdorini kiritish.
        """
        if message.from_user.id not in ADMINS:
            bot.send_message(message.chat.id, "❌ Bu bo'lim faqat adminlar uchun.")
            return

        text = message.text.strip()
        try:
            points = int(text)
            if points <= 0:
                raise ValueError
        except ValueError:
            bot.send_message(
                message.chat.id,
                "❌ Iltimos, musbat butun son kiriting.\n"
                "Jarayon bekor qilindi. Yangi ball berish uchun yana /givepoint yozing."
            )
            return

        msg = bot.send_message(
            message.chat.id,
            "✉️ Admin izohini yozing (masalan: \"Kun savoli g'olibi uchun\"),\n"
            "yoki shunchaki biror sabab yozing:"
        )
        bot.register_next_step_handler(msg, _gp_step_comment, user_id, username, display_name, points)

    def _gp_step_comment(message, user_id, username, display_name, points):
        """
        4-bosqich: admin izohi, ballni yozish va xabarlarni yuborish.
        """
        if message.from_user.id not in ADMINS:
            bot.send_message(message.chat.id, "❌ Bu bo'lim faqat adminlar uchun.")
            return

        admin_comment = (message.text or "").strip()
        if not admin_comment:
            admin_comment = "Bonus ballar berildi 🎁"

        # 1) Bazaga ball qo'shamiz
        give_points_to_user(user_id, points)

        # 2) Foydalanuvchiga xabar
        bonus_text = (
            "🎁 Sizga yangi ball berildi!\n\n"
            f"💰 Berilgan ball: {points}\n"
            f"💬 Sabab: {admin_comment}\n\n"
            "📌 Ballaringizni \"🎁 Sovg'a yutish\" bo'limida kuzatib boring."
        )
        try:
            bot.send_message(
                user_id,
                bonus_text
            )
        except Exception as e:
            print(f"⚠️ Bonus xabarini userga yuborib bo'lmadi ({user_id}): {e}")

        # 3) Adminga tasdiqlash
        username_part = f"@{username}" if username else f"ID: {user_id}"
        confirm_text = (
            "✅ Ball berish yakunlandi!\n\n"
            f"👤 Foydalanuvchi: {display_name} ({username_part})\n"
            f"💰 Berilgan ball: {points}\n"
            f"💬 Izoh: {admin_comment}"
        )
        bot.send_message(
            message.chat.id,
            confirm_text
        )

    # ===================== /stats — BOT STATISTIKASI =====================

    @bot.message_handler(commands=['stats'])
    def cmd_stats(message):
        if message.from_user.id not in ADMINS:
            bot.send_message(message.chat.id, "❌ Bu buyruq faqat adminlar uchun.")
            return

        stats = get_bot_stats()

        top_user_text = "Top foydalanuvchi hali yo'q."
        tu = stats.get("top_user")
        if tu:
            top_user_text = (
                f"{tu['display']}\n"
                f"   ID: {tu['user_id']}\n"
                f"   Ballari: {tu['points']}"
            )

        text = (
            "📊 BOT STATISTIKASI\n\n"
            f"👥 Jami foydalanuvchilar: {stats['total_users']}\n"
            f"💰 Jami ball: {stats['total_points']}\n"
            f"📈 O'rtacha ball: {stats['avg_points']}\n"
            f"🤝 Jami takliflar (referrals): {stats['total_referrals']}\n\n"
            f"📚 Kurslar soni: {stats['total_courses']}\n"
            f"🎓 Talabalar: {stats['total_students']} ta\n"
            f"✅ Tasdiqlangan talabalar: {stats['approved_students']} ta\n\n"
            f"📢 E'lonlar soni: {stats['total_announcements']}\n"
            f"❤️ Sovg'a bo'limi likelari: {stats['total_gift_likes']}\n\n"
            f"🏆 Eng ko'p ball to'plagan foydalanuvchi:\n{top_user_text}\n\n"
            f"💾 Oxirgi backup vaqti: {stats['last_backup']}"
        )

        bot.send_message(message.chat.id, text)
