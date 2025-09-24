import os
from dotenv import load_dotenv

# .env fayldan o‘qish
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

ADMINS = [6587587517]  # Admin ID lari
DATABASE_PATH = "data.db"

CONTACT_INFO = """
📞 Biz bilan bog'lanish:

📍 Manzil: Farg'ona : Yozyovon 
📞 Telefon: +998 99 998 64 21
📧 Telegram : @optimum_LA

🕒 Ish vaqtimiz: 
Dushanba - Yakshanba : 6:00 - 20:00

Made by @Fellixboi 
"""

# Kanal ma’lumotlari
CHANNEL_USERNAME = "@optimum_LA"
