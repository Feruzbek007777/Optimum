# main.py
from data.loader import bot
from database.database import Database





# initialize DB
db = Database()
db.init_db()
print("Database initialized.")


import handlers.users.commands
import handlers.users.text_handlers
import handlers.users.callbacks
import handlers.users.contact_handler
import handlers.admins.commands
import handlers.admins.callbacks
import handlers.misc.my_chat_member

print("Handlers loaded. Bot starting...")

if __name__ == "__main__":
    bot.infinity_polling()
