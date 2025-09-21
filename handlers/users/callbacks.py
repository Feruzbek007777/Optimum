import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from database.database import get_course_details, get_teacher, add_student, approve_student, delete_student
from keyboards.inline import back_button
from keyboards.default import phone_keyboard, yes_no_keyboard, main_menu_keyboard
from config import ADMINS


def setup_user_callbacks(bot) :
    @bot.callback_query_handler(func=lambda call : call.data.startswith("info_"))
    def course_info_callback(call) :
        course_id = call.data.split("_")[1]
        show_course_info(bot, call.message, course_id)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda call : call.data.startswith("register_"))
    def course_register_callback(call) :
        course_id = call.data.split("_")[1]
        start_registration(bot, call.message, course_id)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda call : call.data.startswith("teacher_"))
    def teacher_info_callback(call) :
        course_id = call.data.split("_")[1]
        show_teacher_info(bot, call.message, course_id)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda call : call.data == "back")
    def back_callback(call) :
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id)


def show_course_info(bot, message, course_id) :
    course_info = get_course_details(course_id)
    teacher_info = get_teacher(course_id)

    if course_info :
        price, schedule, description, image_path, course_name = course_info

        response = f"""
📚 {course_name}

💰 Narxi: {price}
🕒 Vaqti: {schedule}
📝 Tavsifi: {description}
"""
        keyboard = InlineKeyboardMarkup()
        if teacher_info :
            keyboard.add(InlineKeyboardButton("👨‍🏫 Ustoz haqida", callback_data=f"teacher_{course_id}"))
        keyboard.add(InlineKeyboardButton("🔙 Orqaga", callback_data="back"))

        if image_path :
            try :
                with open(image_path, 'rb') as photo :
                    bot.send_photo(message.chat.id, photo, caption=response, reply_markup=keyboard)
            except :
                bot.send_message(message.chat.id, response, reply_markup=keyboard)
        else :
            bot.send_message(message.chat.id, response, reply_markup=keyboard)
    else :
        bot.send_message(message.chat.id, "❌ Bu kurs haqida ma'lumot topilmadi.")


def show_teacher_info(bot, message, course_id) :
    teacher_info = get_teacher(course_id)

    if teacher_info :
        teacher_id, full_name, achievements, image_path = teacher_info

        response = f"""
👨‍🏫 {full_name}

🏆 Erishgan yutuqlari: {achievements}
"""
        keyboard = back_button()

        if image_path :
            try :
                with open(image_path, 'rb') as photo :
                    bot.send_photo(message.chat.id, photo, caption=response, reply_markup=keyboard)
            except :
                bot.send_message(message.chat.id, response, reply_markup=keyboard)
        else :
            bot.send_message(message.chat.id, response, reply_markup=keyboard)
    else :
        bot.send_message(message.chat.id, "❌ Bu kurs uchun o'qituvchi ma'lumotlari topilmadi.")


def start_registration(bot, message, course_id) :
    msg = bot.send_message(message.chat.id, "✍️ Ism va familiyangizni kiriting (masalan: Azizov Aziz):",
                           reply_markup=ReplyKeyboardRemove())
    bot.register_next_step_handler(msg, process_name_step, bot, course_id)


def process_name_step(message, bot, course_id) :
    full_name = message.text
    msg = bot.send_message(message.chat.id, "📞 Telefon raqamingizni yuboring:", reply_markup=phone_keyboard())
    bot.register_next_step_handler(msg, process_phone_step, bot, course_id, full_name)


def process_phone_step(message, bot, course_id, full_name) :
    if message.contact :
        phone_number = message.contact.phone_number
    else :
        phone_number = message.text

    # Ma'lumotlarni saqlash
    add_student(full_name, phone_number, message.from_user.username, course_id)

    # Tasdiqlash so'rovi
    response = f"""
✅ Sizning ma'lumotlaringiz qabul qilindi!

👤 Ism: {full_name}
📞 Telefon: {phone_number}

⚠️ Diqqat! Agar «Ha» tugmasini bosangiz, adminlarimiz sizga telefon qilib bog'lanishadi va kurs haqida ma'lumot berishadi.
"""
    bot.send_message(message.chat.id, response, reply_markup=yes_no_keyboard())
    bot.register_next_step_handler(message, process_confirmation, bot, full_name, phone_number, course_id)


def process_confirmation(message, bot, full_name, phone_number, course_id) :
    if message.text == "✅ Ha" :
        # Ma'lumotlarni tasdiqlash
        approve_student(full_name, phone_number, course_id)

        # Adminlarga xabar berish
        for admin_id in ADMINS :
            try :
                bot.send_message(admin_id,
                                 f"🎓 Yangi talaba ro'yxatdan o'tdi:\n\nIsm: {full_name}\nTel: {phone_number}\nKurs ID: {course_id}")
            except :
                pass

        bot.send_message(message.chat.id, "✅ Rahmat! Tez orada adminlarimiz siz bilan bog'lanishadi.",
                         reply_markup=main_menu_keyboard())
    else :
        # Ma'lumotlarni o'chirish
        delete_student(full_name, phone_number, course_id)
        bot.send_message(message.chat.id, "❌ Ro'yxatdan o'tish bekor qilindi.", reply_markup=main_menu_keyboard())