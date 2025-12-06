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

from database.database import init_database

from utils.backup import start_auto_backup   # faqat avto-backup shu yerdan
from keyboards.default import main_menu_keyboard
from handlers.users.quiz import setup_quiz_handlers
from handlers.users.fastwords import setup_fastwords_handlers
from handlers.users.referrals import setup_referral_handlers
from handlers.backup_handler import setup_backup_handlers   # 🔥 YANGI: backup + /database handlerlari


# ---------- BOT ----------

bot = telebot.TeleBot(BOT_TOKEN)

# Kerakli papkalar
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
setup_quiz_handlers(bot)
setup_fastwords_handlers(bot)
setup_referral_handlers(bot)

# 🔥 Backup, restore va guruh handlerlari
setup_backup_handlers(bot)


if __name__ == "__main__":
    # 🔥 Bazani ishga tushiramiz
    init_database()

    # 🔥 Har 6 soatda avto-backupni ishga tushiramiz
    start_auto_backup(interval_hours=6)

    print("🚀 Bot ishga tushdi...")
    bot.polling(none_stop=True)
