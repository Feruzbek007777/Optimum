import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

from config import ADMINS
from keyboards.default import main_menu_keyboard, admin_menu_keyboard
from database.database import add_admin_group, get_points, create_connection
from utils.givepoint import find_user_by_username, give_points_to_user, take_points_from_user
from utils.stats import get_bot_stats

# ✅ REFERRAL: /start argumentni pendingga yozib qo'yish uchun
from handlers.users.referrals import process_start_referral


def setup_admin_commands(bot):
    # /start — admin yoki oddiy userga qarab menyu
    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        # ✅ REFERRAL: agar /start <referrer_id> bo'lsa pendingga yozib qo'yadi (ball bermaydi)
        # Bu faqat private chatda mantiqli
        if message.chat.type == "private":
            process_start_referral(message)

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

        msg = bot.send_message(message.chat.id, text)
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
            bot.send_message(user_id, bonus_text)
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
        bot.send_message(message.chat.id, confirm_text)

    # ===================== /takepoint — BALL AYIRISH =====================

    _takepoint_sessions = {}

    @bot.message_handler(commands=['takepoint'])
    def cmd_takepoint(message):
        if message.from_user.id not in ADMINS:
            bot.send_message(message.chat.id, "❌ Sizda bu buyruqni ishlatish huquqi yo'q!")
            return

        msg = bot.send_message(
            message.chat.id,
            "🧾 Ball AYIRISH\n\n"
            "Ball ayirmoqchi bo‘lgan foydalanuvchining @username'ini yuboring:"
        )
        bot.register_next_step_handler(msg, _tp_step_username)

    def _tp_step_username(message):
        if message.from_user.id not in ADMINS:
            bot.send_message(message.chat.id, "❌ Bu bo'lim faqat adminlar uchun.")
            return

        raw_username = (message.text or "").strip()
        user = find_user_by_username(raw_username)

        if not user:
            bot.send_message(
                message.chat.id,
                "❌ Bunday username bazada topilmadi.\n"
                "Iltimos, /takepoint ni qaytadan boshlang va to'g'ri @username yuboring."
            )
            return

        user_id, username, full_name, joined_at, pts, refs = user

        display_name = (full_name or "").strip() or "Ismi ko'rsatilmagan"
        username_part = f"@{username}" if username else f"ID: {user_id}"

        _takepoint_sessions[message.from_user.id] = {
            "user_id": user_id,
            "username": username,
            "display_name": display_name,
            "old_points": pts
        }

        text = (
            "✅ Foydalanuvchi topildi:\n\n"
            f"👤 {display_name} ({username_part})\n"
            f"🆔 ID: {user_id}\n"
            f"💰 Hozirgi ballari: {pts}\n"
            f"🤝 Takliflari: {refs}\n\n"
            "Nechta ball AYIRAMIZ? (masalan: 10 yoki 0.5)"
        )

        msg = bot.send_message(message.chat.id, text)
        bot.register_next_step_handler(msg, _tp_step_points)

    def _tp_step_points(message):
        if message.from_user.id not in ADMINS:
            bot.send_message(message.chat.id, "❌ Bu bo'lim faqat adminlar uchun.")
            return

        text = (message.text or "").strip().replace(",", ".")
        try:
            points = float(text)
            if points <= 0:
                raise ValueError
        except ValueError:
            bot.send_message(
                message.chat.id,
                "❌ Iltimos, 0 dan katta son kiriting.\n"
                "Jarayon bekor qilindi. Qayta urinmoqchi bo'lsangiz /takepoint yozing."
            )
            _takepoint_sessions.pop(message.from_user.id, None)
            return

        sess = _takepoint_sessions.get(message.from_user.id)
        if not sess:
            bot.send_message(message.chat.id, "Session yo‘qolib qoldi. /takepoint dan qayta boshlang.")
            return

        sess["points"] = points
        _takepoint_sessions[message.from_user.id] = sess

        msg = bot.send_message(
            message.chat.id,
            "✉️ Admin izohini yozing (ixtiyoriy).\n"
            "Agar izoh bo‘lmasa `-` deb yuboring:"
        )
        bot.register_next_step_handler(msg, _tp_step_comment)

    def _tp_step_comment(message):
        if message.from_user.id not in ADMINS:
            bot.send_message(message.chat.id, "❌ Bu bo'lim faqat adminlar uchun.")
            return

        sess = _takepoint_sessions.get(message.from_user.id)
        if not sess:
            bot.send_message(message.chat.id, "Session yo‘qolib qoldi. /takepoint dan qayta boshlang.")
            return

        user_id = sess["user_id"]
        username = sess.get("username")
        display_name = sess.get("display_name", "Ismi ko'rsatilmagan")
        old_points = sess.get("old_points", 0)
        points = sess.get("points", 0)

        admin_comment = (message.text or "").strip()
        if admin_comment == "-" or not admin_comment:
            admin_comment = ""

        # bazadan ball ayiramiz (minus bo'lsa ham bo'ladi)
        take_points_from_user(user_id, points)

        try:
            new_points = get_points(user_id)
        except Exception:
            new_points = old_points - points

        # userga xabar
        user_text = (
            "⚠️ Sizning ballaringiz yangilandi.\n\n"
            f"➖ Ayirilgan ball: {points}\n"
            f"💰 Hozirgi ball: {new_points}\n"
        )
        if admin_comment:
            user_text += f"\n💬 Sabab: {admin_comment}"

        try:
            bot.send_message(user_id, user_text)
        except Exception as e:
            print(f"⚠️ Takepoint xabarini userga yuborib bo'lmadi ({user_id}): {e}")

        username_part = f"@{username}" if username else f"ID: {user_id}"
        confirm_text = (
            "✅ Ball ayirish yakunlandi!\n\n"
            f"👤 Foydalanuvchi: {display_name} ({username_part})\n"
            f"➖ Ayirilgan ball: {points}\n"
            f"💰 Oldin: {old_points}\n"
            f"💰 Hozir: {new_points}"
        )
        if admin_comment:
            confirm_text += f"\n💬 Izoh: {admin_comment}"

        bot.send_message(message.chat.id, confirm_text)

        _takepoint_sessions.pop(message.from_user.id, None)

    # ===================== /stats — BOT STATISTIKASI =====================

    @bot.message_handler(commands=['stats'])
    def cmd_stats(message):
        if message.from_user.id not in ADMINS:
            bot.send_message(message.chat.id, "❌ Bu buyruq faqat adminlar uchun.")
            return

        stats = get_bot_stats()

        # ===================== YANGI STATLAR (DBdan) =====================
        total_positive = 0
        total_minus_abs = 0
        negative_users = 0
        zero_users = 0
        new_users_24h = 0
        new_users_7d = 0
        pending_referrals = 0

        conn = create_connection()
        cursor = conn.cursor()
        try:
            # + ball jamlanmasi
            cursor.execute("""
                SELECT COALESCE(SUM(CASE WHEN COALESCE(points,0) > 0 THEN points ELSE 0 END), 0)
                FROM users
            """)
            total_positive = cursor.fetchone()[0] or 0

            # - ball jamlanmasi (musbat ko'rinishda)
            cursor.execute("""
                SELECT COALESCE(SUM(CASE WHEN COALESCE(points,0) < 0 THEN -points ELSE 0 END), 0)
                FROM users
            """)
            total_minus_abs = cursor.fetchone()[0] or 0

            # manfiy balli userlar
            cursor.execute("SELECT COUNT(*) FROM users WHERE COALESCE(points,0) < 0")
            negative_users = cursor.fetchone()[0] or 0

            # 0 balli userlar
            cursor.execute("SELECT COUNT(*) FROM users WHERE COALESCE(points,0) = 0")
            zero_users = cursor.fetchone()[0] or 0

            # so'nggi 24 soatda yangi userlar
            cursor.execute("SELECT COUNT(*) FROM users WHERE joined_at >= DATETIME('now','-1 day')")
            new_users_24h = cursor.fetchone()[0] or 0

            # so'nggi 7 kunda yangi userlar
            cursor.execute("SELECT COUNT(*) FROM users WHERE joined_at >= DATETIME('now','-7 day')")
            new_users_7d = cursor.fetchone()[0] or 0

            # pending referral (jadval bo'lmasa ham xato bermasin)
            try:
                cursor.execute("SELECT COUNT(*) FROM pending_referrals")
                pending_referrals = cursor.fetchone()[0] or 0
            except Exception:
                pending_referrals = 0

        finally:
            conn.close()

        # referral conversion (foydali indikator)
        total_users = stats.get('total_users', 0) or 0
        total_referrals = stats.get('total_referrals', 0) or 0
        if total_users > 0:
            referral_rate = round((total_referrals / total_users) * 100, 2)
        else:
            referral_rate = 0.0

        # top user text
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
            f"👥 Jami foydalanuvchilar: {stats.get('total_users', 0)}\n"
            f"💰 Jami ball (sof): {stats.get('total_points', 0)}\n"
            f"➕ Jami qo‘shilgan ball: {total_positive}\n"
            f"➖ Jami ayirilgan ball: {total_minus_abs}\n"
            f"📈 O'rtacha ball: {stats.get('avg_points', 0)}\n"
            f"⚠️ Manfiy balli userlar: {negative_users}\n"
            f"⭕ 0 balli userlar: {zero_users}\n\n"
            f"🤝 Jami takliflar (referrals): {total_referrals}\n"
            f"📌 Referral konversiya: {referral_rate}%\n"
            f"⏳ Pending referral (hali tasdiqlanmagan): {pending_referrals}\n\n"
            f"🆕 Oxirgi 24 soatda yangi userlar: {new_users_24h}\n"
            f"🗓 Oxirgi 7 kunda yangi userlar: {new_users_7d}\n\n"
            f"📚 Kurslar soni: {stats.get('total_courses', 0)}\n"
            f"🎓 Talabalar: {stats.get('total_students', 0)} ta\n"
            f"✅ Tasdiqlangan talabalar: {stats.get('approved_students', 0)} ta\n\n"
            f"📢 E'lonlar soni: {stats.get('total_announcements', 0)}\n"
            f"❤️ Sovg'a bo'limi likelari: {stats.get('total_gift_likes', 0)}\n\n"
            f"🏆 Eng ko'p ball to'plagan foydalanuvchi:\n{top_user_text}\n\n"
            f"💾 Oxirgi backup vaqti: {stats.get('last_backup', '-')}\n\n"
        )

        bot.send_message(message.chat.id, text)
