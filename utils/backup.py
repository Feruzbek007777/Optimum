import os
import shutil
from datetime import datetime
from config import DATABASE_PATH


def safe_backup_database():
    """Bazani va rasmlarni xavfsiz backup qilish"""
    try:
        if not os.path.exists(DATABASE_PATH):
            print("⚠️ Ma'lumotlar bazasi topilmadi.")
            return None

        os.makedirs("backups", exist_ok=True)

        # 🔹 Vaqt belgisi
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_folder = os.path.join("backups", f"backup_{timestamp}")
        os.makedirs(backup_folder, exist_ok=True)

        # 1️⃣ Database faylni saqlaymiz
        db_backup = os.path.join(backup_folder, "data.db")
        shutil.copy2(DATABASE_PATH, db_backup)

        # 2️⃣ Rasmlar papkasini saqlaymiz (agar mavjud bo‘lsa)
        if os.path.exists("images") and os.listdir("images"):
            images_backup = os.path.join(backup_folder, "images")
            shutil.copytree("images", images_backup, dirs_exist_ok=True)

        print(f"✅ To‘liq backup yaratildi: {backup_folder}")
        return backup_folder
    except Exception as e:
        print(f"❌ Backupda xatolik: {e}")
        return None


def get_latest_backup():
    """Eng so‘nggi backupni topish"""
    if not os.path.exists("backups"):
        return None

    folders = [f for f in os.listdir("backups") if f.startswith("backup_")]
    if not folders:
        return None

    latest = max(folders)
    return os.path.join("backups", latest)


def safe_restore_database():
    """Oxirgi backupdan bazani va rasmlarni tiklash"""
    try:
        latest_backup = get_latest_backup()
        if not latest_backup:
            print("⚠️ Backup topilmadi.")
            return None

        db_file = os.path.join(latest_backup, "data.db")
        images_folder = os.path.join(latest_backup, "images")

        # 1️⃣ Bazani tiklash
        if os.path.exists(db_file):
            shutil.copy2(db_file, DATABASE_PATH)
            print("✅ Ma'lumotlar bazasi tiklandi.")

        # 2️⃣ Rasmlarni tiklash
        if os.path.exists(images_folder):
            os.makedirs("images", exist_ok=True)
            shutil.copytree(images_folder, "images", dirs_exist_ok=True)
            print("🖼️ Rasmlar tiklandi.")

        print(f"✅ To‘liq restore yakunlandi: {latest_backup}")
        return latest_backup
    except Exception as e:
        print(f"❌ Restoreda xatolik: {e}")
        return None
