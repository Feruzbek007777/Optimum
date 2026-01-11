from telebot.types import ReplyKeyboardMarkup, KeyboardButton

def main_menu_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    # 1-qator
    markup.row(
        KeyboardButton("📚 Kurslar haqida ma'lumot"),
        KeyboardButton("📝 Kursga yozilish")
    )
    # 2-qator
    markup.row(
        KeyboardButton("🌐 Translate"),
        KeyboardButton("📢 E'lonlar")
    )
    # 3-qator – Sovg'a + Translate
    markup.row(
        KeyboardButton("🎁 Sovg'a yutish"),
        KeyboardButton("🏆 Top foydalanuvchilar")
    )
    # 4-qator – Top foydalanuvchilar
    markup.add(KeyboardButton("📞 Biz bilan bog'lanish"))
    return markup


def gift_menu_keyboard():
    """
    Sovg'a yutish bo'limi uchun menyu:
    🧪 Quiz     ⚡ Tezkor so'zlar
    🤝 Taklif   📊 Mening ballarim
              ⬅️ Ortga
    """
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(
        KeyboardButton("📝 Quiz"),
        KeyboardButton("⚡️ Tezkor mashq")
    )
    markup.row(
        KeyboardButton("🤝 Takliflarim"),
        KeyboardButton("📊 Mening ballarim")
    )
    markup.row(
        KeyboardButton("🎰 Bonus"),
        KeyboardButton("⬅️ Ortga")
    )
    return markup


def admin_menu_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("➕ Kurs qo'shish"), KeyboardButton("ℹ️ Kursga ma'lumot qo'shish"))
    keyboard.add(KeyboardButton("👨‍🏫 Ustoz qo'shish"), KeyboardButton("🗑️ Ustozni o'chirish"))
    keyboard.add(KeyboardButton("❌ Kursni o'chirish"), KeyboardButton("👥 Guruhlarga xabar yuborish"))
    keyboard.add(KeyboardButton("📋 Guruhlar ro'yxati"), KeyboardButton("📢 E'lon yuborish"))
    keyboard.add(KeyboardButton("💾 Backup"), KeyboardButton("🎓 Students"))
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
