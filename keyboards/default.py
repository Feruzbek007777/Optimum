from telebot.types import ReplyKeyboardMarkup, KeyboardButton

def main_menu_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("📚 Kurslar haqida ma'lumot"), KeyboardButton("📝 Kursga yozilish"))
    keyboard.add(KeyboardButton("📞 Biz bilan bog'lanish"), KeyboardButton("📢 E'lonlar"))
    return keyboard

def admin_menu_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("➕ Kurs qo'shish"), KeyboardButton("ℹ️ Kursga ma'lumot qo'shish"))
    keyboard.add(KeyboardButton("👨‍🏫 Ustoz qo'shish"), KeyboardButton("🗑️ Ustozni o'chirish"))
    keyboard.add(KeyboardButton("❌ Kursni o'chirish"), KeyboardButton("👥 Guruhlarga xabar yuborish"))
    keyboard.add(KeyboardButton("📋 Guruhlar ro'yxati"), KeyboardButton("📢 E'lon yuborish"))
    keyboard.add(KeyboardButton("🎓 Students"))
    keyboard.add(KeyboardButton("🔙 Asosiy menyu"))
    return keyboard

def yes_no_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("✅ Ha"), KeyboardButton("❌ Yo'q"))
    return keyboard

def phone_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("📞 Telefon raqamini yuborish", request_contact=True))
    return keyboard