import telebot
import sqlite3
import os
from config import DATABASE_PATH
from keyboards.default import admin_menu_keyboard
from database.database import delete_course, delete_teacher, add_course_details, add_teacher, get_all_admin_groups


def setup_admin_callbacks(bot) :
    @bot.callback_query_handler(func=lambda call : call.data.startswith("add_info_"))
    def add_info_callback(call) :
        course_id = call.data.split("_")[2]
        msg = bot.send_message(call.message.chat.id, "🖼️ Kurs rasmini yuboring:")
        bot.register_next_step_handler(msg, process_course_image, bot, course_id)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda call : call.data.startswith("add_teacher_"))
    def add_teacher_callback(call) :
        course_id = call.data.split("_")[2]
        msg = bot.send_message(call.message.chat.id, "🖼️ Ustoz rasmini yuboring:")
        bot.register_next_step_handler(msg, process_teacher_image, bot, course_id)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda call : call.data.startswith("delete_teacher_"))
    def delete_teacher_callback(call) :
        teacher_id = call.data.split("_")[2]
        success = delete_teacher(teacher_id)
        if success :
            bot.send_message(call.message.chat.id, "✅ Ustoz muvaffaqiyatli o'chirildi!",
                             reply_markup=admin_menu_keyboard())
        else :
            bot.send_message(call.message.chat.id, "❌ Ustozni o'chirishda xatolik yuz berdi!",
                             reply_markup=admin_menu_keyboard())
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda call : call.data.startswith("delete_course_"))
    def delete_course_callback(call) :
        course_id = call.data.split("_")[2]
        success = delete_course(course_id)
        if success :
            bot.send_message(call.message.chat.id, "✅ Kurs muvaffaqiyatli o'chirildi!",
                             reply_markup=admin_menu_keyboard())
        else :
            bot.send_message(call.message.chat.id, "❌ Kursni o'chirishda xatolik yuz berdi!",
                             reply_markup=admin_menu_keyboard())
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda call : call.data.startswith("send_group_"))
    def send_group_callback(call) :
        data = call.data.split("_")
        group_id = data[2]
        msg = bot.send_message(call.message.chat.id, "📝 Guruhga yubormoqchi bo'lgan xabaringizni kiriting:")
        bot.register_next_step_handler(msg, process_group_message, bot, group_id)
        bot.answer_callback_query(call.id)


def process_course_image(message, bot, course_id) :
    if message.photo :
        # Rasmni saqlash
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        image_path = f"images/course_{course_id}.jpg"

        os.makedirs("images", exist_ok=True)
        with open(image_path, 'wb') as new_file :
            new_file.write(downloaded_file)

        msg = bot.send_message(message.chat.id, "💰 Kurs narxini kiriting:")
        bot.register_next_step_handler(msg, process_course_price, bot, course_id, image_path)
    else :
        bot.send_message(message.chat.id, "❌ Iltimos, rasm yuboring!")
        bot.register_next_step_handler(message, process_course_image, bot, course_id)


def process_course_price(message, bot, course_id, image_path) :
    price = message.text
    msg = bot.send_message(message.chat.id, "📅 Kurs vaqtini kiriting (masalan: Dushanba-Chorshanba-Juma, 18:00-20:00):")
    bot.register_next_step_handler(msg, process_course_schedule, bot, course_id, image_path, price)


def process_course_schedule(message, bot, course_id, image_path, price) :
    schedule = message.text
    msg = bot.send_message(message.chat.id, "📝 Kurs haqida qisqacha tavsif kiriting (150 ta belgidan oshmasin):")
    bot.register_next_step_handler(msg, process_course_description, bot, course_id, image_path, price, schedule)


def process_course_description(message, bot, course_id, image_path, price, schedule) :
    description = message.text
    if len(description) > 150 :
        bot.send_message(message.chat.id, "❌ Tavsif 150 ta belgidan oshmasligi kerak!")
        bot.register_next_step_handler(message, process_course_description, bot, course_id, image_path, price, schedule)
        return

    # Ma'lumotlarni saqlash
    add_course_details(course_id, price, schedule, description, image_path)

    bot.send_message(message.chat.id, "✅ Kurs ma'lumotlari muvaffaqiyatli saqlandi!",
                     reply_markup=admin_menu_keyboard())


def process_teacher_image(message, bot, course_id) :
    if message.photo :
        # Rasmni saqlash
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        image_path = f"images/teacher_{course_id}.jpg"

        os.makedirs("images", exist_ok=True)
        with open(image_path, 'wb') as new_file :
            new_file.write(downloaded_file)

        msg = bot.send_message(message.chat.id, "👨‍🏫 Ustozning ism va familiyasini kiriting:")
        bot.register_next_step_handler(msg, process_teacher_name, bot, course_id, image_path)
    else :
        bot.send_message(message.chat.id, "❌ Iltimos, rasm yuboring!")
        bot.register_next_step_handler(message, process_teacher_image, bot, course_id)


def process_teacher_name(message, bot, course_id, image_path) :
    full_name = message.text
    msg = bot.send_message(message.chat.id, "🏆 Ustozning erishgan yutuqlari haqida ma'lumot kiriting:")
    bot.register_next_step_handler(msg, process_teacher_achievements, bot, course_id, image_path, full_name)


def process_teacher_achievements(message, bot, course_id, image_path, full_name) :
    achievements = message.text

    # Ma'lumotlarni saqlash
    add_teacher(course_id, full_name, achievements, image_path)

    bot.send_message(message.chat.id, "✅ Ustoz ma'lumotlari muvaffaqiyatli saqlandi!",
                     reply_markup=admin_menu_keyboard())


def process_group_message(message, bot, group_id) :
    # BU YERGA O'Z GURUH ID LARINGIZNI QO'YING!
    group_ids = {
        "all" : "Barcha guruhlar",
        "-4902306438" : "Birinchi guruh",
        "-4805402276" : "Ikkinchi guruh"
    }

    if group_id == "all" :
        # Barcha guruhlarga yuborish
        success_count = 0
        for gid, gname in group_ids.items() :
            if gid != "all" :  # "all" dan boshqa barcha guruhlarga
                try :
                    if message.photo :
                        file_info = bot.get_file(message.photo[-1].file_id)
                        downloaded_file = bot.download_file(file_info.file_path)
                        with open("temp_photo.jpg", 'wb') as f :
                            f.write(downloaded_file)
                        with open("temp_photo.jpg", 'rb') as photo :
                            bot.send_photo(gid, photo, caption=message.caption)
                    else :
                        bot.send_message(gid, message.text)
                    success_count += 1
                    print(f"✅ Xabar {gname} ga yuborildi")
                except Exception as e :
                    print(f"❌ Xatolik {gname} ga yuborishda: {e}")

        bot.send_message(message.chat.id, f"✅ Xabar {success_count} ta guruhga muvaffaqiyatli yuborildi!",
                         reply_markup=admin_menu_keyboard())

    else :
        # Faqat bir guruhga yuborish
        try :
            group_name = group_ids.get(group_id, "Noma'lum guruh")
            if message.photo :
                file_info = bot.get_file(message.photo[-1].file_id)
                downloaded_file = bot.download_file(file_info.file_path)
                with open("temp_photo.jpg", 'wb') as f :
                    f.write(downloaded_file)
                with open("temp_photo.jpg", 'rb') as photo :
                    bot.send_photo(group_id, photo, caption=message.caption)
            else :
                bot.send_message(group_id, message.text)

            bot.send_message(message.chat.id, f"✅ Xabar '{group_name}' guruhiga muvaffaqiyatli yuborildi!",
                             reply_markup=admin_menu_keyboard())
            print(f"✅ Xabar {group_name} ga yuborildi")
        except Exception as e :
            error_msg = f"❌ Xatolik: {e}"
            bot.send_message(message.chat.id, error_msg, reply_markup=admin_menu_keyboard())
            print(error_msg)