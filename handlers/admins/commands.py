import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from config import ADMINS
from keyboards.default import main_menu_keyboard, admin_menu_keyboard
from database.database import add_admin_group


def setup_admin_commands(bot) :
    @bot.message_handler(commands=['start'])
    def send_welcome(message) :
        if message.from_user.id in ADMINS :
            bot.send_message(message.chat.id, "👨‍💻 Admin menyusiga xush kelibsiz!", reply_markup=admin_menu_keyboard())
        else :
            bot.send_message(message.chat.id, "🤖 Xush kelibsiz! Quyidagi menyudan kerakli bo'limni tanlang:",
                             reply_markup=main_menu_keyboard())

    @bot.message_handler(commands=['admin'])
    def admin_panel(message) :
        if message.from_user.id in ADMINS :
            bot.send_message(message.chat.id, "👨‍💻 Admin menyusiga xush kelibsiz!", reply_markup=admin_menu_keyboard())
        else :
            bot.send_message(message.chat.id, "❌ Sizda admin huquqi yo'q!")

    # Qo'lda guruh qo'shish
    @bot.message_handler(commands=['addgroup'])
    def add_group_manual(message) :
        if message.from_user.id in ADMINS :
            try :
                # Format: /addgroup -4902306438 "Guruh Nomi"
                parts = message.text.split(' ', 2)
                if len(parts) < 3 :
                    bot.send_message(message.chat.id,
                                     "❌ Noto'g'ri format! Format: /addgroup -4902306438 \"Guruh Nomi\"")
                    return

                group_id = int(parts[1])
                group_title = parts[2]

                success = add_admin_group(group_id, group_title)

                if success :
                    bot.send_message(message.chat.id,
                                     f"✅ Guruh muvaffaqiyatli qo'shildi!\nID: {group_id}\nNomi: {group_title}")
                else :
                    bot.send_message(message.chat.id, "❌ Guruh qo'shishda xatolik!")
            except (IndexError, ValueError) :
                bot.send_message(message.chat.id, "❌ Noto'g'ri format! Format: /addgroup -4902306438 \"Guruh Nomi\"")