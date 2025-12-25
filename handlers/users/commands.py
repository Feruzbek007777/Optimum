import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

from config import ADMINS
from keyboards.default import main_menu_keyboard, admin_menu_keyboard
from handlers.users.callbacks import check_subscription, show_subscription_request

from database.database import add_user, add_referral, get_referrals_count, create_connection
from utils.points import get_points


# Agar user /start <referrer_id> bilan kirdi-yu, kanalga obuna bo'lmagan bo'lsa,
# referrer_id ni vaqtincha shu yerda saqlab turamiz.
# Keyin user obuna bo'lib qayta /start qilsa ham bonus yo'qolmaydi.
_PENDING_REFERRAL = {}  # {referred_user_id: referrer_id}


def _is_user_exists_in_db(user_id: int) -> bool:
    """
    users jadvalida user bor-yo'qligini tekshiradi.
    'Yangi user' sharti uchun kerak.
    """
    conn = create_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT 1 FROM users WHERE user_id = ? LIMIT 1", (user_id,))
        return cur.fetchone() is not None
    finally:
        conn.close()


def _format_user_display(user) -> str:
    """
    Referrerga chiroyli ko'rinishdagi user nomini chiqarish.
    """
    uid = user.id
    name = f"{user.first_name or ''} {user.last_name or ''}".strip()
    if user.username:
        if name:
            name = f"{name} (@{user.username})"
        else:
            name = f"@{user.username}"
    if not name:
        name = f"ID: {uid}"
    return name


def setup_user_commands(bot):
    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        user_id = message.from_user.id
        user = message.from_user

        # 1) Bu /start user DB'da bormi? (bonus faqat yangi userga)
        was_exists = _is_user_exists_in_db(user_id)  # True bo'lsa, bu user oldin ham start qilgan

        # 2) /start argumentni o'qiymiz (deep-link)
        parts = (message.text or "").split(maxsplit=1)
        referrer_id = None
        if len(parts) > 1 and parts[1].isdigit():
            referrer_id = int(parts[1])

        # 3) Foydalanuvchini bazaga qo'shamiz (yoki update)
        add_user(
            user_id,
            user.username,
            f"{user.first_name or ''} {user.last_name or ''}".strip()
        )

        # 4) Agar /start argument bor bo'lsa va bu user yangi bo'lsa va self-ref bo'lmasa,
        # referrer_id ni pendingga yozib qo'yamiz.
        # (Agar user obuna bo'lmasa, keyin qaytib kelganda ham bonus yo'qolmaydi)
        if (not was_exists) and referrer_id and referrer_id != user_id:
            _PENDING_REFERRAL[user_id] = referrer_id

        # 5) Avval kanalga obunani tekshiramiz
        # Obuna bo'lmagan bo'lsa: subscribe sahifasini chiqaramiz va shu joyda to'xtaymiz.
        # Pending referrer_id saqlanib qoladi.
        if not check_subscription(bot, user_id):
            show_subscription_request(bot, message)
            return

        # 6) Agar user obuna bo'lgan bo'lsa, endi referral bonusni berishga harakat qilamiz.
        # Shartlar:
        # - user yangi bo'lishi kerak (was_exists = False)
        # - pending referrer bo'lishi kerak
        # - self-ref bo'lmasin
        # - DB add_referral() referred_id UNIQUE -> bir marta ishlaydi
        if not was_exists:
            pending_ref = _PENDING_REFERRAL.get(user_id)
            if pending_ref and pending_ref != user_id:
                added = add_referral(referrer_id=pending_ref, referred_id=user_id, bonus_points=300)

                # Har holda pendingni o'chiramiz (qo'shilgan bo'lsa ham, bo'lmasa ham)
                _PENDING_REFERRAL.pop(user_id, None)

                # Agar referral DBga yozilgan bo'lsa (birinchi marta), referrerga xabar
                if added:
                    try:
                        total_points = get_points(pending_ref)
                        total_refs = get_referrals_count(pending_ref)
                        new_user_display = _format_user_display(user)

                        text = (
                            "🎉 Yangi taklif!\n\n"
                            "Sizning taklif havolangiz orqali yangi foydalanuvchi qo‘shildi:\n"
                            f"• {new_user_display}\n\n"
                            "✅ Shart bajarildi: foydalanuvchi kanalga obuna bo‘lgan.\n\n"
                            "💰 Sizga +300 ball qo‘shildi!\n"
                            f"📊 Umumiy ballaringiz: {total_points}\n"
                            f"👥 Umumiy takliflaringiz: {total_refs}"
                        )
                        bot.send_message(pending_ref, text)
                    except Exception:
                        pass
            else:
                # user yangi, lekin referral yo'q yoki self-ref bo'lgan
                _PENDING_REFERRAL.pop(user_id, None)
        else:
            # user eski bo'lsa, pending bo'lsa ham bekor qilamiz
            _PENDING_REFERRAL.pop(user_id, None)

        # 7) Endi menyu (admin yoki oddiy)
        if user_id in ADMINS:
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

    @bot.message_handler(commands=['id'])
    def get_chat_id(message):
        chat_id = message.chat.id
        chat_type = message.chat.type
        chat_title = message.chat.title or "Shaxsiy chat"

        response = f"""
📋 Chat ma'lumotlari:

🆔 ID: {chat_id}
🏷️ Nomi: {chat_title}
📊 Turi: {chat_type}
"""
        bot.send_message(message.chat.id, response)
