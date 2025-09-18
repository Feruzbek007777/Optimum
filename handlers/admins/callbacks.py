# handlers/admins/callbacks.py
from data.loader import bot
from telebot.types import CallbackQuery
from database.database import Database

db = Database()

# admin selects course to add teacher, we will ask for teacher details via messages
@bot.callback_query_handler(func=lambda call: call.data.startswith("course_") and call.from_user.id == __import__('config').ADMIN_ID)
def admin_course_selected(call: CallbackQuery):
    # This handler will be triggered for admins also when clicking course inline.
    # To avoid conflict with user callback, admin can use /add_teacher to start flow.
    bot.answer_callback_query(call.id)
    # We won't implement full multi-step here to avoid complexity; admin flow via /add_teacher + messages in commands.py is enough.
    # Could be extended later.
