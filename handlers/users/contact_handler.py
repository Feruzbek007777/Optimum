import telebot
from database.database import add_student, approve_student, delete_student
from keyboards.default import yes_no_keyboard, main_menu_keyboard
from config import ADMINS


def setup_contact_handler(bot) :
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

    return process_phone_step, process_confirmation