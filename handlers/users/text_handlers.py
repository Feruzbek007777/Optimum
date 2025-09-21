import telebot
from telebot.types import ReplyKeyboardRemove
from config import CONTACT_INFO
from database.database import get_announcements
from keyboards.default import main_menu_keyboard, phone_keyboard, yes_no_keyboard
from keyboards.inline import generate_courses_keyboard

def setup_user_text_handlers(bot):
    @bot.message_handler(func=lambda message: message.text == "🔙 Asosiy menyu")
    def back_to_main(message):
        bot.send_message(message.chat.id, "Asosiy menyu:", reply_markup=main_menu_keyboard())

    @bot.message_handler(func=lambda message: message.text == "📚 Kurslar haqida ma'lumot")
    def courses_info(message):
        keyboard = generate_courses_keyboard("info")
        if keyboard.keyboard:
            bot.send_message(message.chat.id, "Kursni tanlang:", reply_markup=keyboard)
        else:
            bot.send_message(message.chat.id, "❌ Hozircha hech qanday kurs mavjud emas.")

    @bot.message_handler(func=lambda message: message.text == "📝 Kursga yozilish")
    def course_registration(message):
        keyboard = generate_courses_keyboard("register")
        if keyboard.keyboard:
            bot.send_message(message.chat.id, "Kursni tanlang:", reply_markup=keyboard)
        else:
            bot.send_message(message.chat.id, "❌ Hozircha hech qanday kurs mavjud emas.")

    @bot.message_handler(func=lambda message: message.text == "📞 Biz bilan bog'lanish")
    def contact_us(message):
        bot.send_message(message.chat.id, CONTACT_INFO)

    @bot.message_handler(func=lambda message: message.text == "📢 E'lonlar")
    def show_announcements(message):
        announcements = get_announcements()
        if announcements:
            for announcement in announcements:
                msg, image_path = announcement
                if image_path:
                    try:
                        with open(image_path, 'rb') as photo:
                            bot.send_photo(message.chat.id, photo, caption=msg)
                    except:
                        bot.send_message(message.chat.id, msg)
                else:
                    bot.send_message(message.chat.id, msg)
        else:
            bot.send_message(message.chat.id, "❌ Hozircha hech qanday e'lon mavjud emas.")