from data.loader import bot
from telebot.types import CallbackQuery
from database.database import Database
from keyboards.inline import teachers_inline_for_course
from keyboards.default import main_menu, request_contact_markup

db = Database()
user_states = {}

@bot.callback_query_handler(func=lambda call: call.data.startswith("course_"))
def course_detail(call: CallbackQuery):
    course_id = int(call.data.split("_", 1)[1])
    course = db.get_course_by_id(course_id)
    if course:
        _id, name, desc, price, teacher_id, schedule, image_url = course
        caption = f"📚 <b>{name}</b>\n\n💰 Narxi: {price or '—'}\n🕒 Vaqti: {schedule or '—'}\n\n{desc or '—'}"
        markup = None
        from keyboards.inline import course_detail_inline
        markup = course_detail_inline(_id)
        try:
            bot.edit_message_media  # just to check
            # try to edit message if possible
            if image_url:
                bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id, caption=caption, reply_markup=markup)
            else:
                bot.edit_message_text(caption, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)
        except Exception:
            # send new message
            if image_url:
                bot.send_photo(call.message.chat.id, photo=image_url, caption=caption, reply_markup=markup)
            else:
                bot.send_message(call.message.chat.id, caption, reply_markup=markup)

    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("teacher_"))
def teacher_list_for_course(call: CallbackQuery):
    course_id = int(call.data.split("_", 1)[1])
    # show list of teachers inline
    markup = teachers_inline_for_course(course_id)
    bot.edit_message_text("Ustozlardan birini tanlang:", call.message.chat.id, call.message.message_id, reply_markup=markup)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("teacherid_"))
def teacher_detail(call: CallbackQuery):
    teacher_id = int(call.data.split("_", 1)[1])
    t = db.get_teacher_by_id(teacher_id)
    if t:
        _id, full_name, bio, achievements, image_url, course_id = t
        text = f"👨‍🏫 <b>{full_name}</b>\n\n{bio or ''}\n\n🏆 Yutuqlar:\n{achievements or ''}"
        try:
            if image_url:
                bot.send_photo(call.message.chat.id, photo=image_url, caption=text)
            else:
                bot.send_message(call.message.chat.id, text)
        except Exception:
            bot.send_message(call.message.chat.id, text)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("enroll_"))
def enroll_callback(call: CallbackQuery):
    course_id = int(call.data.split("_",1)[1])
    user_id = call.from_user.id
    # set user state to awaiting name
    user_states[user_id] = {"step": "awaiting_name", "course_id": course_id}
    bot.send_message(call.message.chat.id, "Iltimos ismingiz va familiyangizni kiriting:")
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "back_courses")
def back_courses(call: CallbackQuery):
    from keyboards.inline import courses_inline
    try:
        bot.edit_message_text("Kurslardan birini tanlang:", call.message.chat.id, call.message.message_id, reply_markup=courses_inline())
    except Exception:
        bot.send_message(call.message.chat.id, "Kurslardan birini tanlang:", reply_markup=courses_inline())
    bot.answer_callback_query(call.id)
