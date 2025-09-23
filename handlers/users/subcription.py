from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import CHANNEL_USERNAME, ADMINS
from keyboards.default import main_menu_keyboard, admin_menu_keyboard


# 🔎 Obuna tekshirish funksiyasi
def check_subscription(bot, user_id):
    try:
        # @ belgisi olib tashlanadi
        chat_id = CHANNEL_USERNAME.replace("@", "")
        member = bot.get_chat_member(chat_id, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        print(f"Obuna tekshirish xatosi: {e}")
        return False


# 📌 Obuna bo'lishni so'rash
def show_subscription_request(bot, message):
    try:
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("📢 Kanalga o'tish", url=f"https://t.me/{CHANNEL_USERNAME.replace('@','')}"),
            InlineKeyboardButton("✅ Tekshirish", callback_data="check_sub")
        )

        text = (
            "❗ Botdan foydalanish uchun kanalga obuna bo‘ling!\n\n"
            f"📢 {CHANNEL_USERNAME}\n\n"
            "Obuna bo‘lgach, «✅ Tekshirish» tugmasini bosing."
        )

        bot.send_message(
            message.chat.id,
            text,
            reply_markup=markup,
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"Obuna so'rovi xatosi: {e}")


# ✅ Callback tugma handler
def setup_subscription_callbacks(bot):
    @bot.callback_query_handler(func=lambda call: call.data == "check_sub")
    def check_sub_callback(call):
        try:
            if check_subscription(bot, call.from_user.id):
                # Agar admin bo'lsa admin menyu
                if call.from_user.id in ADMINS:
                    bot.send_message(call.message.chat.id,
                                     "👨‍💻 Admin menyusiga xush kelibsiz!",
                                     reply_markup=admin_menu_keyboard())
                else:
                    # Oddiy user uchun menyu
                    bot.send_message(call.message.chat.id,
                                     "✅ Obuna tasdiqlandi! Quyidagi menyudan tanlang:",
                                     reply_markup=main_menu_keyboard())

                # Eski xabarni o‘chirib tashlash
                try:
                    bot.delete_message(call.message.chat.id, call.message.message_id)
                except:
                    pass
            else:
                # Agar hali ham obuna bo‘lmagan bo‘lsa
                bot.answer_callback_query(call.id, "❌ Obuna bo‘lmadingiz, qayta urinib ko‘ring!", show_alert=True)
        except Exception as e:
            print(f"Tekshirish callback xatosi: {e}")
