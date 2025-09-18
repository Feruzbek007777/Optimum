# handlers/misc/my_chat_member.py
from data.loader import bot
from telebot.types import ChatMemberUpdated
from database.database import Database

db = Database()

@bot.my_chat_member_handler()
def handle_my_chat_member(my_chat_member: ChatMemberUpdated):
    # when bot is added to group or promoted to admin, store group id
    new_status = my_chat_member.new_chat_member.status
    chat = my_chat_member.chat
    if new_status in ("member", "administrator"):
        db.add_group(chat.id, chat.title if hasattr(chat, "title") else None)
