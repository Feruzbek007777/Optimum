# keyboards/default.py
from telebot.types import ReplyKeyboardMarkup, KeyboardButton


def main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        KeyboardButton("ℹ️ Kurslar haqida ma’lumot"),
        KeyboardButton("📚 Kursga yozilish"),
        KeyboardButton("📞 Biz haqimizda"),
        KeyboardButton("📢 E’lonlar")
    )
    return markup


def admin_main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        KeyboardButton("➕ Kurs qo‘shish"),
        KeyboardButton("📝 Kursga ma’lumot qo‘shish"),
        KeyboardButton("👨‍🏫 Ustoz qo‘shish"),
        KeyboardButton("📢 Guruhlarga xabar yuborish"),
        KeyboardButton("📋 Kurslar ro‘yxati"),
        KeyboardButton("❌ Kursni o‘chirish"),
        KeyboardButton("👥 Students"),
        KeyboardButton("🔙 Orqaga")
    )
    return markup


def make_buttons(names: list, row_width: int = 2, back: bool = False):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=row_width)
    buttons = [KeyboardButton(name) for name in names]
    markup.add(*buttons)
    if back:
        markup.add(KeyboardButton("🔙 Orqaga"))
    return markup


def request_contact_markup():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    button = KeyboardButton("📱 Raqamni yuborish", request_contact=True)
    markup.add(button)
    return markup
