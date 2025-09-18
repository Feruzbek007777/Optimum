# handlers/users/commands.py
from data.loader import bot
from telebot.types import Message
from config import ADMIN_ID
from database.database import Database
from keyboards.default import main_menu, request_contact_markup, make_buttons
from keyboards.inline import courses_inline

db = Database()


@bot.message_handler(commands=['start'])
def start_handler(message: Message):
    user_id = message.from_user.id
    db.insert_telegram_id(user_id)
    if user_id == ADMIN_ID:
        from keyboards.default import admin_main_menu
        bot.send_message(message.chat.id, "👋 Assalomu alaykum, Admin!", reply_markup=admin_main_menu())
    else:
        bot.send_message(message.chat.id, "👋 Assalomu alaykum! Botga xush kelibsiz.\nQuyidagi menyudan tanlang:", reply_markup=main_menu())


@bot.message_handler(func=lambda msg: msg.text == "ℹ️ Kurslar haqida ma’lumot")
def info_courses(message: Message):
    markup = courses_inline(prefix="course")
    if markup:
        bot.send_message(message.chat.id, "Quyidagi kurslardan tanlang:", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "Hozircha kurslar mavjud emas.")


@bot.message_handler(func=lambda msg: msg.text == "📚 Kursga yozilish")
def enroll_menu(message: Message):
    markup = courses_inline(prefix="enroll")
    if markup:
        bot.send_message(message.chat.id, "Qaysi kursga yozilmoqchisiz? Tanlang:", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "Hozircha kurslar mavjud emas.")


@bot.message_handler(func=lambda msg: msg.text == "📞 Biz haqimizda")
def about_us(message: Message):
    text = ("📍 Manzil: Misol ko'chasi 12\n"
            "📞 Telefon: +998 90 000 00 00\n"
            "🌐 Instagram: https://instagram.com/your_instagram\n"
            "📢 Telegram: https://t.me/your_channel")
    bot.send_message(message.chat.id, text)


@bot.message_handler(func=lambda msg: msg.text == "📢 E’lonlar")
def show_announcements(message: Message):
    anns = db.get_announcements(limit=10)
    if not anns:
        bot.send_message(message.chat.id, "Hozircha e'lonlar mavjud emas.")
        return
    text = "📢 Oxirgi e'lonlar:\n\n" + "\n\n".join([f"- {a[1]}" for a in anns])
    bot.send_message(message.chat.id, text)


# back handler for users (shows main menu)
@bot.message_handler(func=lambda msg: msg.text == "🔙 Orqaga")
def go_back(message: Message):
    # if admin show admin menu, else main menu
    if message.from_user.id == ADMIN_ID:
        from keyboards.default import admin_main_menu
        bot.send_message(message.chat.id, "🔙 Admin menyuga qaytdingiz.", reply_markup=admin_main_menu())
    else:
        bot.send_message(message.chat.id, "🔙 Bosh menyuga qaytdingiz.", reply_markup=main_menu())
