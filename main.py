import telebot
import os
import time

from config import BOT_TOKEN

from handlers.users.commands import setup_user_commands
from handlers.users.text_handlers import setup_user_text_handlers
from handlers.users.callbacks import setup_user_callbacks

from handlers.admins.commands import setup_admin_commands
from handlers.admins.text_handlers import setup_admin_text_handlers
from handlers.admins.callbacks import setup_admin_callbacks

from handlers.translate.handler import setup_translate_handlers

from database.database import init_database


from utils.backup import start_auto_backup
from handlers.users.quiz import setup_quiz_handlers
from handlers.users.fastwords import setup_fastwords_handlers
from handlers.users.referrals import setup_referral_handlers
from handlers.backup_handler import setup_backup_handlers
from handlers.users.bonus import setup_bonus_handlers


# ---------- BOT ----------
bot = telebot.TeleBot(BOT_TOKEN, threaded=True, num_threads=4)

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
setup_bonus_handlers(bot)

# Backup, restore va guruh handlerlari
setup_backup_handlers(bot)


if __name__ == "__main__":
    init_database()

    # Siz 24 qilgansiz - qoldirdim
    start_auto_backup(interval_hours=24)

    print("🚀 Bot ishga tushdi...")

    # ✅ Bot yiqilib qolmasin: crash bo'lsa ham qayta turadi
    while True:
        try:
            bot.infinity_polling(skip_pending=True, timeout=30, long_polling_timeout=30)
        except Exception as e:
            print(f"⚠️ Polling crash: {e}")
            time.sleep(3)
