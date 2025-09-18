from data.loader import bot
from telebot.types import Message
from keyboards.default import main_menu, make_buttons, request_contact_markup
from keyboards.inline import course_detail_inline
from database.database import Database

db = Database()


user_states = {}

@bot.message_handler(func=lambda m: m.text == "ℹ️ Kurslar haqida ma’lumot")
def info_courses(message: Message):
    courses = [name for _, name in db.get_courses()]
    if not courses:
        bot.send_message(message.chat.id, "Hozircha kurslar qo‘shilmagan.")
    else:
        bot.send_message(message.chat.id, "Kurslardan birini tanlang:", reply_markup=make_buttons(courses, back=True))

@bot.message_handler(func=lambda m: m.text == "📚 Kursga yozilish")
def enroll_courses(message: Message):
    courses = [name for _, name in db.get_courses()]
    if not courses:
        bot.send_message(message.chat.id, "Hozircha kurslar yo'q.")
    else:
        bot.send_message(message.chat.id, "Qaysi kursga yozilmoqchisiz?", reply_markup=make_buttons(courses, back=True))


@bot.message_handler(func=lambda m: m.text == "📖 Biz haqimizda")
def about_us(message: Message):
    text = ("📍 Manzil: Toshkent, Chilonzor 7\n"
            "📞 Telefon: +998 90 123 45 67\n"
            "🌐 Instagram: https://instagram.com/oqvu_markaz\n"
            "🌐 Telegram: https://t.me/oqvu_markaz\n")
    bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda m: m.text == "📢 E’lonlar")
def announcements(message: Message):
    anns = db.get_announcements()
    if not anns:
        bot.send_message(message.chat.id, "Hozircha e'lonlar yo'q.")
        return
    for aid, text in anns:
        bot.send_message(message.chat.id, f"📢 {text}")

@bot.message_handler(func=lambda m: m.text == "🔙 Orqaga")
def go_back(message: Message):
    bot.send_message(message.chat.id, "Bosh menyu:", reply_markup=main_menu())
    user_states.pop(message.from_user.id, None)

@bot.message_handler(func=lambda m: True, content_types=['text'])
def generic_text_handler(message: Message):
    txt = message.text.strip()
    user_id = message.from_user.id

    state = user_states.get(user_id)
    if state and state.get("step") == "awaiting_name":
        full_name = txt
        state["temp_name"] = full_name
        user_states[user_id] = state
        bot.send_message(message.chat.id, "Iltimos telefon raqamingizni jo'nating:", reply_markup=request_contact_markup())
        return


    course = db.get_course_by_name(txt)
    if course:

        _id, name, desc, price, teacher_id, schedule, image_url = course
        caption = f"📚 <b>{name}</b>\n\n💰 Narxi: {price or '—'}\n🕒 Vaqti: {schedule or '—'}\n\n{desc or '—'}"
        reply_markup = course_detail_inline(_id)
        if image_url:
            try:
                bot.send_photo(message.chat.id, photo=image_url, caption=caption, reply_markup=reply_markup)
            except Exception as e:
                bot.send_message(message.chat.id, caption, reply_markup=reply_markup)
        else:
            bot.send_message(message.chat.id, caption, reply_markup=reply_markup)
        return

    bot.send_message(message.chat.id, "Iltimos menyudan tanlang yoki /start bosing.", reply_markup=main_menu())
