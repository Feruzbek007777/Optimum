import telebot
import os
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from config import BOT_TOKEN
from handlers.users.commands import setup_user_commands
from handlers.users.text_handlers import setup_user_text_handlers
from handlers.users.callbacks import setup_user_callbacks
from handlers.admins.commands import setup_admin_commands
from handlers.admins.text_handlers import setup_admin_text_handlers
from handlers.admins.callbacks import setup_admin_callbacks
from handlers.translate.handler import setup_translate_handlers
from database.database import add_admin_group, delete_admin_group, get_all_admin_groups
from utils.backup import safe_backup_database, safe_restore_database


# Bot yaratish
bot = telebot.TeleBot(BOT_TOKEN)

# Papkalarni yaratish
os.makedirs("images", exist_ok=True)
os.makedirs("backups", exist_ok=True)

# Handlerlarni sozlash
setup_user_commands(bot)
setup_user_text_handlers(bot)
setup_user_callbacks(bot)
setup_admin_commands(bot)
setup_admin_text_handlers(bot)
setup_admin_callbacks(bot)
setup_translate_handlers(bot)


# 📌 Guruhlarni qo‘shish
@bot.message_handler(content_types=['new_chat_members'])
def handle_new_chat_members(message):
    for member in message.new_chat_members:
        if member.id == bot.get_me().id:
            group_id = message.chat.id
            group_title = message.chat.title
            success = add_admin_group(group_id, group_title)
            if success:
                bot.send_message(group_id, "✅ Bot qo‘shildi! Guruh ma'lumotlari saqlandi.")
            else:
                bot.send_message(group_id, "❌ Guruh ma'lumotlarini saqlashda xatolik!")


# 📌 Guruhdan chiqarilganda
@bot.message_handler(content_types=['left_chat_member'])
def handle_left_chat_member(message):
    if message.left_chat_member.id == bot.get_me().id:
        group_id = message.chat.id
        success = delete_admin_group(group_id)
        if success:
            print(f"✅ Guruhdan chiqarildi: {group_id}")


# 📌 Admin panel tugmalari
@bot.message_handler(commands=['database'])
def show_database_panel(message):
    if message.from_user.id in [6587587517]:  # Admin ID
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(KeyboardButton("💾 Backup"), KeyboardButton("♻️ Restore"))
        bot.send_message(message.chat.id, "📂 Ma'lumotlar bazasi paneli:", reply_markup=markup)


# 📌 Backup
@bot.message_handler(func=lambda m: m.text == "💾 Backup" and m.from_user.id in [6587587517])
def manual_backup(message):
    backup_file = safe_backup_database()
    if backup_file:
        bot.send_document(message.chat.id, open(backup_file, "rb"))
        bot.send_message(message.chat.id, "✅ Backup yaratildi va yuborildi.")
    else:
        bot.send_message(message.chat.id, "❌ Backup yaratishda xatolik!")


# 📌 Restore
@bot.message_handler(func=lambda m: m.text == "♻️ Restore" and m.from_user.id in [6587587517])
def manual_restore(message):
    restored_file = safe_restore_database()
    if restored_file:
        bot.send_message(message.chat.id, f"✅ Restore qilindi: `{restored_file}`", parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, "❌ Restore uchun backup topilmadi.")


print("🚀 Bot ishga tushdi...")

if __name__ == "__main__":
    bot.polling(none_stop=True)
