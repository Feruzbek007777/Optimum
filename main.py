import telebot
import os
from config import BOT_TOKEN
from database.database import init_database
from handlers.users.commands import setup_user_commands
from handlers.users.text_handlers import setup_user_text_handlers
from handlers.users.callbacks import setup_user_callbacks
from handlers.admins.commands import setup_admin_commands
from handlers.admins.text_handlers import setup_admin_text_handlers
from handlers.admins.callbacks import setup_admin_callbacks
from handlers.translate.handler import setup_translate_handlers  # YANGI IMPORT
from database.database import add_admin_group

# Botni yaratish
bot = telebot.TeleBot(BOT_TOKEN)

# Papkalarni yaratish
os.makedirs("images", exist_ok=True)

# Handlerlarni sozlash
setup_user_commands(bot)
setup_user_text_handlers(bot)
setup_user_callbacks(bot)
setup_admin_commands(bot)
setup_admin_text_handlers(bot)
setup_admin_callbacks(bot)
setup_translate_handlers(bot)

# Ma'lumotlar bazasini ishga tushirish
init_database()


# Guruhlarni avto-qo'shish uchun handler
@bot.message_handler(content_types=['new_chat_members'])
def handle_new_chat_members(message) :
    for member in message.new_chat_members :
        if member.id == bot.get_me().id :
            # Bot yangi guruhga qo'shildi
            group_id = message.chat.id
            group_title = message.chat.title
            success = add_admin_group(group_id, group_title)
            if success :
                bot.send_message(group_id, f"✅ Bot qo'shildi! Guruh ma'lumotlari saqlandi.")
            else :
                bot.send_message(group_id, f"❌ Guruh ma'lumotlarini saqlashda xatolik!")


# Guruhdan chiqarilganda o'chirish
@bot.message_handler(content_types=['left_chat_member'])
def handle_left_chat_member(message) :
    if message.left_chat_member.id == bot.get_me().id :
        # Bot guruhdan chiqarildi
        from database.database import delete_admin_group
        group_id = message.chat.id
        success = delete_admin_group(group_id)
        if success :
            print(f"✅ Bot {group_id} guruhidan chiqarildi, ma'lumotlar o'chirildi")


# Start bosilganda mavjud guruhlarni tekshirish va qo'shish
@bot.message_handler(commands=['start'])
def check_existing_groups(message) :
    # Foydalanuvchi start bosganda, bot qaysi guruhlarda ekanligini tekshiradi
    if message.from_user.id in [6587587517] :  # Sizning ID ingiz
        try :
            # Bu yerda siz bot qaysi guruhlarda ekanligini qo'lda qo'shishingiz mumkin
            from database.database import add_admin_group, get_all_admin_groups

            # Avval mavjud guruhlarni ko'rsatish
            groups = get_all_admin_groups()
            if groups :
                response = "📋 Bot admin bo'lgan guruhlar:\n\n"
                for i, (group_id, group_title) in enumerate(groups, 1) :
                    response += f"{i}. {group_title}\nID: `{group_id}`\n\n"
                bot.send_message(message.chat.id, response, parse_mode='Markdown')
            else :
                bot.send_message(message.chat.id,
                                 "❌ Hozircha hech qanday guruh mavjud emas. Botni guruhga qo'shing va admin qiling.")

        except Exception as e :
            bot.send_message(message.chat.id, f"❌ Xatolik: {e}")


print("Bot ishga tushdi...")
bot.polling(none_stop=True)