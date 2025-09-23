import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from database.database import get_course_details, get_teacher, add_student, approve_student, delete_student
from keyboards.inline import back_button
from keyboards.default import phone_keyboard, yes_no_keyboard, main_menu_keyboard, admin_menu_keyboard
from config import ADMINS, CHANNEL_USERNAME


def setup_user_callbacks(bot):
    @bot.callback_query_handler(func=lambda call: call.data.startswith("info_"))
    def course_info_callback(call):
        try:
            if not check_subscription(bot, call.from_user.id):
                show_subscription_request(bot, call.message)
                return

            course_id = call.data.split("_")[1]
            show_course_info(bot, call.message, course_id)
            bot.answer_callback_query(call.id)
        except Exception as e:
            print(f"Xatolik course_info_callback: {e}")
            try:
                bot.answer_callback_query(call.id)
            except:
                pass

    @bot.callback_query_handler(func=lambda call: call.data.startswith("register_"))
    def course_register_callback(call):
        try:
            if not check_subscription(bot, call.from_user.id):
                show_subscription_request(bot, call.message)
                return

            course_id = call.data.split("_")[1]
            start_registration(bot, call.message, course_id)
            bot.answer_callback_query(call.id)
        except Exception as e:
            print(f"Xatolik course_register_callback: {e}")
            try:
                bot.answer_callback_query(call.id)
            except:
                pass

    @bot.callback_query_handler(func=lambda call: call.data.startswith("teacher_"))
    def teacher_info_callback(call):
        try:
            if not check_subscription(bot, call.from_user.id):
                show_subscription_request(bot, call.message)
                return

            course_id = call.data.split("_")[1]
            show_teacher_info(bot, call.message, course_id)
            bot.answer_callback_query(call.id)
        except Exception as e:
            print(f"Xatolik teacher_info_callback: {e}")
            try:
                bot.answer_callback_query(call.id)
            except:
                pass

    @bot.callback_query_handler(func=lambda call: call.data == "back")
    def back_callback(call):
        try:
            # Avval callback query ni javob berish
            bot.answer_callback_query(call.id)
            # Keyin xabarni o'chirish
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception as e:
            print(f"Xatolik back_callback: {e}")
            try:
                bot.answer_callback_query(call.id)
            except:
                pass

    # Bu callback ishlatilsin: "check_subscription"
    @bot.callback_query_handler(func=lambda call: call.data == "check_subscription")
    def check_subscription_callback(call):
        try:
            if check_subscription(bot, call.from_user.id):
                bot.answer_callback_query(call.id, "✅ Obuna tekshirildi!")
                try:
                    bot.delete_message(call.message.chat.id, call.message.message_id)
                except:
                    pass  # Agar o'chirib bo'lmasa, davom etish

                if call.from_user.id in ADMINS:
                    bot.send_message(call.message.chat.id, "👨‍💻 Admin menyusiga xush kelibsiz!",
                                     reply_markup=admin_menu_keyboard())
                else:
                    bot.send_message(call.message.chat.id,
                                     "🤖 Xush kelibsiz! Quyidagi menyudan kerakli bo'limni tanlang:",
                                     reply_markup=main_menu_keyboard())
            else:
                # Obuna bo'lmasa alert ko'rsatamiz
                bot.answer_callback_query(call.id, "❌ Siz hali kanalga obuna bo'lmagansiz!", show_alert=True)
        except Exception as e:
            print(f"Xatolik check_subscription_callback: {e}")
            try:
                bot.answer_callback_query(call.id)
            except:
                pass


def check_subscription(bot, user_id):
    """
    Foydalanuvchi kanalga obuna ekanligini tekshirish.
    Eslatma: CHANNEL_USERNAME config da @ bilan turganiga e'tibor bering.
    """
    try:
        # Chat identifikatorini ishonchli shaklda tayyorlaymiz: boshlanishida @ bo'lsa shunday qoldiramiz
        chat_identifier = CHANNEL_USERNAME if CHANNEL_USERNAME.startswith("@") else f"@{CHANNEL_USERNAME}"

        # get_chat_member uchun @username to'g'ri bo'lishi kerak (Telegram API @username qabul qiladi)
        member = bot.get_chat_member(chat_identifier, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        # Logga to'liq xatoni chiqarish — foydali bo'ladi
        print(f"Obuna tekshirish xatosi: {e}")

        # Agar xato "chat not found" bo'lsa, ehtimol username noto'g'ri yoki bot kanalga qo'shilmagan
        # Keyin False qaytaramiz (foydalanuvchini obuna bo'lmagan deb hisoblaymiz)
        return False


def show_subscription_request(bot, message):
    """Obuna so'rovi ko'rsatish: 2 ta tugma — Kanalga o'tish va Tekshirish"""
    try:
        keyboard = InlineKeyboardMarkup()
        # Kanalga o'tish (url)
        keyboard.add(InlineKeyboardButton("📢 Kanalga obuna bo'lish", url=f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}"))
        # Tekshirish tugmasi — callback ishlaydi (callback_data = "check_subscription")
        keyboard.add(InlineKeyboardButton("✅ Tekshirish", callback_data="check_subscription"))

        # Oddiy plain text (parse_mode ishlatmaymiz — avvalgi 'can't parse entities' xatosini oldini olamiz)
        text = (
            "🤖 Botdan foydalanish uchun quyidagi kanalga obuna bo'ling:\n\n"
            f"📢 {CHANNEL_USERNAME}\n\n"
            "Obuna bo'lgach, «✅ Tekshirish» tugmasini bosing."
        )

        bot.send_message(message.chat.id, text, reply_markup=keyboard)
    except Exception as e:
        print(f"Obuna so'rovi xatosi: {e}")


def show_course_info(bot, message, course_id):
    try:
        course_info = get_course_details(course_id)
        teacher_info = get_teacher(course_id)

        if course_info:
            price, schedule, description, image_path, course_name = course_info

            response = f"""
📚 {course_name}

💰 Narxi: {price}
🕒 Vaqti: {schedule}
📝 Tavsifi: {description}
"""
            keyboard = InlineKeyboardMarkup()
            if teacher_info:
                keyboard.add(InlineKeyboardButton("👨‍🏫 Ustoz haqida", callback_data=f"teacher_{course_id}"))
            keyboard.add(InlineKeyboardButton("🔙 Orqaga", callback_data="back"))

            if image_path:
                try:
                    with open(image_path, 'rb') as photo:
                        bot.send_photo(message.chat.id, photo, caption=response, reply_markup=keyboard)
                except:
                    bot.send_message(message.chat.id, response, reply_markup=keyboard)
            else:
                bot.send_message(message.chat.id, response, reply_markup=keyboard)
        else:
            bot.send_message(message.chat.id, "❌ Bu kurs haqida ma'lumot topilmadi.")
    except Exception as e:
        print(f"Kurs ma'lumotlari ko'rsatish xatosi: {e}")
        bot.send_message(message.chat.id, "❌ Ma'lumotlarni yuklashda xatolik yuz berdi.")


def show_teacher_info(bot, message, course_id):
    try:
        teacher_info = get_teacher(course_id)

        if teacher_info:
            teacher_id, full_name, achievements, image_path = teacher_info

            response = f"""
👨‍🏫 {full_name}

🏆 Erishgan yutuqlari: {achievements}
"""
            keyboard = back_button()

            if image_path:
                try:
                    with open(image_path, 'rb') as photo:
                        bot.send_photo(message.chat.id, photo, caption=response, reply_markup=keyboard)
                except:
                    bot.send_message(message.chat.id, response, reply_markup=keyboard)
            else:
                bot.send_message(message.chat.id, response, reply_markup=keyboard)
        else:
            bot.send_message(message.chat.id, "❌ Bu kurs uchun o'qituvchi ma'lumotlari topilmadi.")
    except Exception as e:
        print(f"Ustoz ma'lumotlari ko'rsatish xatosi: {e}")
        bot.send_message(message.chat.id, "❌ Ma'lumotlarni yuklashda xatolik yuz berdi.")


def start_registration(bot, message, course_id):
    try:
        msg = bot.send_message(message.chat.id, "✍️ Ism va familiyangizni kiriting (masalan: Azizov Aziz):",
                               reply_markup=ReplyKeyboardRemove())
        bot.register_next_step_handler(msg, process_name_step, bot, course_id)
    except Exception as e:
        print(f"Ro'yxatdan o'tish boshlash xatosi: {e}")


def process_name_step(message, bot, course_id):
    try:
        full_name = message.text
        msg = bot.send_message(message.chat.id, "📞 Telefon raqamingizni yuboring:", reply_markup=phone_keyboard())
        bot.register_next_step_handler(msg, process_phone_step, bot, course_id, full_name)
    except Exception as e:
        print(f"Ism qadamida xatolik: {e}")


def process_phone_step(message, bot, course_id, full_name):
    try:
        if message.contact:
            phone_number = message.contact.phone_number
        else:
            phone_number = message.text

        add_student(full_name, phone_number, message.from_user.username, course_id)

        response = f"""
✅ Sizning ma'lumotlaringiz qabul qilindi!

👤 Ism: {full_name}
📞 Telefon: {phone_number}

⚠️ Diqqat! Agar «Ha» tugmasini bosangiz, adminlarimiz sizga telefon qilib bog'lanishadi va kurs haqida ma'lumot berishadi.
"""
        bot.send_message(message.chat.id, response, reply_markup=yes_no_keyboard())
        bot.register_next_step_handler(message, process_confirmation, bot, full_name, phone_number, course_id)
    except Exception as e:
        print(f"Telefon qadamida xatolik: {e}")


def process_confirmation(message, bot, full_name, phone_number, course_id):
    try:
        if message.text == "✅ Ha":
            approve_student(full_name, phone_number, course_id)

            for admin_id in ADMINS:
                try:
                    bot.send_message(admin_id,
                                     f"🎓 Yangi talaba ro'yxatdan o'tdi:\n\nIsm: {full_name}\nTel: {phone_number}\nKurs ID: {course_id}")
                except:
                    pass

            bot.send_message(message.chat.id, "✅ Rahmat! Tez orada adminlarimiz siz bilan bog'lanishadi.",
                             reply_markup=main_menu_keyboard())
        else:
            delete_student(full_name, phone_number, course_id)
            bot.send_message(message.chat.id, "❌ Ro'yxatdan o'tish bekor qilindi.", reply_markup=main_menu_keyboard())
    except Exception as e:
        print(f"Tasdiqlash qadamida xatolik: {e}")
