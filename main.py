import telebot
import os
from config import BOT_TOKEN
from handlers.users.commands import setup_user_commands
from handlers.users.text_handlers import setup_user_text_handlers
from handlers.users.callbacks import setup_user_callbacks
from handlers.admins.commands import setup_admin_commands
from handlers.admins.text_handlers import setup_admin_text_handlers
from handlers.admins.callbacks import setup_admin_callbacks
from handlers.translate.handler import setup_translate_handlers
from database.database import add_admin_group, delete_admin_group, get_all_admin_groups
from utils.backup import safe_backup_database, manual_restore_database
from telebot import types

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


# 📌 Admin tugmalar
def admin_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("💾 Backup", "♻️ Restore")
    return markup


# 📌 Guruhlarni avto-qo'shish uchun handler
@bot.message_handler(content_types=['new_chat_members'])
def handle_new_chat_members(message):
    for member in message.new_chat_members:
        if member.id == bot.get_me().id:
            group_id = message.chat.id
            group_title = message.chat.title
            success = add_admin_group(group_id, group_title)
            if success:
                bot.send_message(group_id, "✅ Bot qo'shildi! Guruh ma'lumotlari saqlandi.")
            else:
                bot.send_message(group_id, "❌ Guruh ma'lumotlarini saqlashda xatolik!")


# 📌 Guruhdan chiqarilganda o‘chirish
@bot.message_handler(content_types=['left_chat_member'])
def handle_left_chat_member(message):
    if message.left_chat_member.id == bot.get_me().id:
        group_id = message.chat.id
        success = delete_admin_group(group_id)
        if success:
            print(f"✅ Bot {group_id} guruhidan chiqarildi, ma'lumotlar o‘chirildi")


# 📌 Start bosilganda admin menyu
@bot.message_handler(commands=['start'])
def check_existing_groups(message):
    if message.from_user.id in [6587587517]:  # Admin ID
        try:
            groups = get_all_admin_groups()
            if groups:
                response = "📋 Bot admin bo‘lgan guruhlar:\n\n"
                for i, (group_id, group_title) in enumerate(groups, 1):
                    response += f"{i}. {group_title}\nID: `{group_id}`\n\n"
                bot.send_message(message.chat.id, response, parse_mode='Markdown')
            else:
                bot.send_message(message.chat.id,
                                 "❌ Hozircha hech qanday guruh mavjud emas. Botni guruhga qo‘shing va admin qiling.")

            # 🔑 Admin menyuni chiqarish
            bot.send_message(message.chat.id, "🔐 Admin panel:", reply_markup=admin_keyboard())

        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Xatolik: {e}")
    else:
        bot.send_message(message.chat.id, "🤖 Salom! Bot ishga tushdi.")


# 📌 Admin uchun backup tugmasi
@bot.message_handler(func=lambda m: m.text == "💾 Backup" and m.from_user.id in [6587587517])
def manual_backup(message):
    backup_file = safe_backup_database()
    if backup_file:
        with open(backup_file, "rb") as f:
            bot.send_document(message.chat.id, f, caption="✅ Backup fayli yaratildi!")
    else:
        bot.send_message(message.chat.id, "❌ Backup yaratishda xatolik!")


# 📌 Admin uchun restore tugmasi
@bot.message_handler(func=lambda m: m.text == "♻️ Restore" and m.from_user.id in [6587587517])
def manual_restore(message):
    success = manual_restore_database()
    if success:
        bot.send_message(message.chat.id, "✅ Ma’lumotlar so‘nggi backupdan tiklandi!")
    else:
        bot.send_message(message.chat.id, "❌ Restore qilishda muammo bo‘ldi!")


print("🚀 Bot ishga tushdi...")

if __name__ == "__main__":
    bot.polling(none_stop=True)
