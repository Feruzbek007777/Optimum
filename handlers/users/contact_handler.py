# handlers/users/contact_handler.py
from data.loader import bot
from telebot.types import Message
from database.database import Database

db = Database()
# We need access to the user_states dict from text_handlers / callbacks.
# For simplicity, we import from there (monolithic but simple).
from handlers.users.text_handlers import user_states as text_user_states
from handlers.users.callbacks import user_states as cb_user_states

@bot.message_handler(content_types=['contact'])
def contact_handler(message: Message):
    if not message.contact:
        bot.send_message(message.chat.id, "Kontakt yuborilmadi.")
        return
    user_id = message.from_user.id
    phone = message.contact.phone_number
    # find user's state - either in text_user_states or cb_user_states
    state = text_user_states.get(user_id) or cb_user_states.get(user_id)
    if state and state.get("step") == "awaiting_name":
        full_name = state.get("temp_name")
        course_id = state.get("course_id")
        if not full_name:
            # fallback
            full_name = message.from_user.full_name
        db.save_phone_number_and_full_name(full_name, phone, user_id)  # update user's table
        db.add_student(user_id, full_name, phone, course_id)
        # clear state
        text_user_states.pop(user_id, None)
        cb_user_states.pop(user_id, None)
        bot.send_message(message.chat.id, "Rahmat! Telefoningiz qabul qilindi. Tez orada biz bilan bog'lanishadi.", reply_markup=None)
    else:
        # Not in registration flow; still save contact info
        db.save_phone_number_and_full_name(message.contact.first_name, phone, user_id)
        bot.send_message(message.chat.id, "Kontakt qabul qilindi.", reply_markup=None)
