import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from config import ADMINS
from keyboards.default import main_menu_keyboard, admin_menu_keyboard


def setup_user_commands(bot) :
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

    @bot.message_handler(commands=['id'])
    def get_chat_id(message) :
        chat_id = message.chat.id
        chat_type = message.chat.type
        chat_title = message.chat.title or "Shaxsiy chat"

        response = f"""
📋 Chat ma'lumotlari:

🆔 ID: `{chat_id}`
🏷️ Nomi: {chat_title}
📊 Turi: {chat_type}
"""
        bot.send_message(message.chat.id, response, parse_mode='Markdown')