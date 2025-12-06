import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from config import ADMINS, CHANNEL_USERNAME
from keyboards.default import main_menu_keyboard, admin_menu_keyboard
from handlers.users.callbacks import check_subscription, show_subscription_request
from database.database import add_user, add_referral, get_referrals_count
from utils.points import get_points


def setup_user_commands(bot):
    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        user_id = message.from_user.id
        user = message.from_user

        # 🔎 /start parametrlari (deep-link) ni ajratamiz
        # misol: "/start", "/start 123456789"
        parts = message.text.split(maxsplit=1)
        referrer_id = None
        if len(parts) > 1 and parts[1].isdigit():
            referrer_id = int(parts[1])

        # 🔥 Foydalanuvchini bazaga qo'shish (users jadvali)
        add_user(
            user_id,
            user.username,
            f"{user.first_name or ''} {user.last_name or ''}".strip()
        )

        # 🔎 Avval kanalga obuna bo'lganini tekshiramiz
        if not check_subscription(bot, user_id):
            show_subscription_request(bot, message)
            return

        # 🔥 Referralni qayd qilish (agar referrer_id bor bo'lsa va o'zi bo'lmasa)
        if referrer_id and referrer_id != user_id:
            added = add_referral(referrer_id=referrer_id, referred_id=user_id)
            if added:
                # Yangi kelgan foydalanuvchi haqida ma'lumot
                ref_user_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
                if user.username:
                    if ref_user_name:
                        ref_user_name = f"{ref_user_name} (@{user.username})"
                    else:
                        ref_user_name = f"@{user.username}"
                if not ref_user_name:
                    ref_user_name = f"ID: {user_id}"

                # Referrerning yangilangan statistikasi
                try:
                    total_points = get_points(referrer_id)
                    total_refs = get_referrals_count(referrer_id)

                    text = (
                        "🎉 Yangi taklif!\n\n"
                        "Sizning taklif havolangiz orqali yangi foydalanuvchi qo'shildi:\n"
                        f"• {ref_user_name}\n\n"
                        f"💰 Sizga +50 ball qo'shildi!\n"
                        f"📊 Umumiy ballaringiz: {total_points}\n"
                        f"👥 Umumiy takliflaringiz: {total_refs}"
                    )

                    bot.send_message(
                        referrer_id,
                        text
                    )
                except Exception:
                    # Agar referrerga xabar yubora olmasak (bloklagan, chat yo'q) jim o'tamiz
                    pass

        # ✅ Agar admin bo'lsa
        if user_id in ADMINS:
            bot.send_message(
                message.chat.id,
                "👨‍💻 Admin menyusiga xush kelibsiz!",
                reply_markup=admin_menu_keyboard()
            )
        else:
            # 👤 Oddiy foydalanuvchi
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
