import telebot
import sqlite3
import os
import csv
from io import StringIO
from telebot.types import ReplyKeyboardRemove
from config import DATABASE_PATH, ADMINS
from database.database import (
    get_approved_students, add_announcement, get_courses,
    get_all_teachers, delete_teacher, delete_course,
    get_all_admin_groups, get_all_users
)
from keyboards.default import admin_menu_keyboard, yes_no_keyboard
from keyboards.inline import (
    generate_courses_keyboard, generate_teachers_keyboard,
    generate_courses_delete_keyboard, generate_teachers_delete_keyboard,
    generate_groups_keyboard
)


def setup_admin_text_handlers(bot):
    @bot.message_handler(func=lambda message: message.text == "🔙 Asosiy menyu" and message.from_user.id in ADMINS)
    def back_to_admin_main(message):
        bot.send_message(message.chat.id, "Admin menyu:", reply_markup=admin_menu_keyboard())

    @bot.message_handler(func=lambda message: message.text == "➕ Kurs qo'shish" and message.from_user.id in ADMINS)
    def add_course(message):
        msg = bot.send_message(message.chat.id, "📝 Yangi kurs nomini kiriting:")
        bot.register_next_step_handler(msg, process_course_name, bot)

    @bot.message_handler(func=lambda message: message.text == "ℹ️ Kursga ma'lumot qo'shish" and message.from_user.id in ADMINS)
    def add_course_info(message):
        keyboard = generate_courses_keyboard("add_info")
        if keyboard.keyboard:
            bot.send_message(message.chat.id, "Qaysi kursga ma'lumot qo'shmoqchisiz?", reply_markup=keyboard)
        else:
            bot.send_message(message.chat.id, "❌ Hozircha hech qanday kurs mavjud emas. Avval kurs qo'shing.")

    @bot.message_handler(func=lambda message: message.text == "👨‍🏫 Ustoz qo'shish" and message.from_user.id in ADMINS)
    def add_teacher(message):
        keyboard = generate_courses_keyboard("add_teacher")
        if keyboard.keyboard:
            bot.send_message(message.chat.id, "Qaysi kursga ustoz qo'shmoqchisiz?", reply_markup=keyboard)
        else:
            bot.send_message(message.chat.id, "❌ Hozircha hech qanday kurs mavjud emas. Avval kurs qo'shing.")

    @bot.message_handler(func=lambda message: message.text == "🗑️ Ustozni o'chirish" and message.from_user.id in ADMINS)
    def delete_teacher_handler(message):
        teachers = get_all_teachers()
        if teachers:
            keyboard = generate_teachers_delete_keyboard()
            bot.send_message(message.chat.id, "Qaysi ustozni o'chirmoqchisiz?", reply_markup=keyboard)
        else:
            bot.send_message(message.chat.id, "❌ Hozircha hech qanday ustoz mavjud emas.")

    @bot.message_handler(func=lambda message: message.text == "❌ Kursni o'chirish" and message.from_user.id in ADMINS)
    def delete_course_handler(message):
        courses = get_courses()
        if courses:
            keyboard = generate_courses_delete_keyboard()
            bot.send_message(message.chat.id, "Qaysi kursni o'chirmoqchisiz?", reply_markup=keyboard)
        else:
            bot.send_message(message.chat.id, "❌ Hozircha hech qanday kurs mavjud emas.")

    @bot.message_handler(func=lambda message: message.text == "👥 Guruhlarga xabar yuborish" and message.from_user.id in ADMINS)
    def send_to_groups(message):
        groups = get_all_admin_groups()
        if groups:
            keyboard = generate_groups_keyboard("send_group")
            bot.send_message(message.chat.id, "📝 Xabarni qaysi guruhga yubormoqchisiz?", reply_markup=keyboard)
        else:
            bot.send_message(message.chat.id,
                             "❌ Hozircha hech qanday guruh mavjud emas. Botni guruhga qo'shing va admin qiling.")

    @bot.message_handler(func=lambda message: message.text == "📢 E'lon yuborish" and message.from_user.id in ADMINS)
    def send_announcement(message):
        msg = bot.send_message(message.chat.id, "📝 E'lon matnini kiriting yoki rasm bilan birga yuboring:")
        bot.register_next_step_handler(msg, process_announcement, bot)

    @bot.message_handler(func=lambda message: message.text == "🎓 Students" and message.from_user.id in ADMINS)
    def export_students(message):
        students = get_approved_students()

        if students:
            # CSV ma'lumotlarini yaratish
            output = StringIO()
            writer = csv.writer(output)
            writer.writerow(['ID', 'Ism Familiya', 'Telefon', 'Username', "Ro'yxatdan o'tgan vaqt", 'Kurs'])

            for student in students:
                writer.writerow(student)

            # CSV ni fayl sifatida yuborish
            output.seek(0)
            bot.send_document(message.chat.id, ('students.csv', output.getvalue()), caption="✅ Talabalar ro'yxati")
        else:
            bot.send_message(message.chat.id, "❌ Hozircha tasdiqlangan talabalar mavjud emas.")

    # Guruhlar ro'yxatini ko'rish
    @bot.message_handler(func=lambda message: message.text == "📋 Guruhlar ro'yxati" and message.from_user.id in ADMINS)
    def show_groups_list(message):
        groups = get_all_admin_groups()
        if groups:
            response = "📋 Bot admin bo'lgan guruhlar:\n\n"
            for i, (group_id, group_title) in enumerate(groups, 1):
                response += f"{i}. {group_title}\nID: `{group_id}`\n\n"
            bot.send_message(message.chat.id, response, parse_mode='Markdown')
        else:
            bot.send_message(message.chat.id, "❌ Hozircha hech qanday guruh mavjud emas.")


def process_course_name(message, bot):
    course_name = message.text
    from database.database import add_course
    success = add_course(course_name)
    if success:
        bot.send_message(message.chat.id, f"✅ '{course_name}' kursi muvaffaqiyatli qo'shildi!",
                         reply_markup=admin_menu_keyboard())
    else:
        bot.send_message(message.chat.id, "❌ Bu nomdagi kurs allaqachon mavjud!", reply_markup=admin_menu_keyboard())


def process_announcement(message, bot):
    announcement_text = message.text
    image_path = None

    if message.photo:
        # Rasmni saqlash
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        image_path = f"images/announcement_{message.message_id}.jpg"

        os.makedirs("images", exist_ok=True)
        with open(image_path, 'wb') as new_file:
            new_file.write(downloaded_file)

    # E'londan DB ga saqlash
    add_announcement(announcement_text, image_path)

    # 🔥 Hamma foydalanuvchilarga yuborish
    users = get_all_users()
    for user_id in users:
        try:
            if image_path:
                with open(image_path, 'rb') as photo:
                    bot.send_photo(user_id, photo, caption=announcement_text)
            else:
                bot.send_message(user_id, announcement_text)
        except Exception as e:
            print(f"❌ {user_id} ga yuborishda xatolik: {e}")

    bot.send_message(message.chat.id,
                     "✅ E'lon saqlandi va barcha foydalanuvchilarga yuborildi!",
                     reply_markup=admin_menu_keyboard())
