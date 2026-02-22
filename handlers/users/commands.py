import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

from config import ADMINS
from keyboards.default import main_menu_keyboard, admin_menu_keyboard
from handlers.users.callbacks import check_subscription, show_subscription_request

from database.database import add_user, create_connection
from handlers.users.referrals import set_pending_referral, try_activate_pending_referral


# Referral: we store "pending" referrals in DB (pending_referrals table)
# so it survives bot restarts and is consistent everywhere.


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

        # 4) Agar /start argument bor bo'lsa va bu user YANGI bo'lsa va self-ref bo'lmasa,
        # referrerni DB pending_referrals ga yozib qo'yamiz.
        if (not was_exists) and referrer_id and referrer_id != user_id:
            set_pending_referral(referrer_id, user_id)

        # 5) Avval kanalga obunani tekshiramiz
        # Obuna bo'lmagan bo'lsa: subscribe sahifasini chiqaramiz va shu joyda to'xtaymiz.
        # Pending referrer_id saqlanib qoladi.
        if not check_subscription(bot, user_id):
            show_subscription_request(bot, message)
            return

        # 6) Agar user obuna bo'lgan bo'lsa, pending referral bo'lsa bonusni faollashtiramiz.
        # (Bonus berish logikasi bitta joyda: handlers/users/referrals.py)
        # Eslatma: bonus faqat 1 marta (referred_id UNIQUE).
        if not was_exists:
            # Agar pending bo'lsa va user obuna bo'lsa, shu yerning o'zida ham faollashadi.
            _ = try_activate_pending_referral(bot, user_id, bonus_points=200)

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
