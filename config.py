import os
from dotenv import load_dotenv

load_dotenv()  # .env faylini yuklaydi

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMINS = list(map(int, os.getenv("ADMINS", "").split(",")))  # Masalan: 6587587517
DATABASE_PATH = os.getenv("DATABASE_PATH", "data.db")
CONTACT_INFO = os.getenv("CONTACT_INFO", "")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME")
