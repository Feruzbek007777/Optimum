import os
import shutil
from datetime import datetime
from config import DATABASE_PATH


def safe_backup_database():
    """To‘liq (bazani va rasmlarni) xavfsiz backup qilish"""
    try:
        if not os.path.exists(DATABASE_PATH):
            print("⚠️ Ma'lumotlar bazasi topilmadi.")
            return None

        os.makedirs("backups", exist_ok=True)

        # Sana-vaqt bilan nomlangan katalog
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = os.path.join("backups", f"backup_{timestamp}")
        os.makedirs(backup_dir, exist_ok=True)

        # 1️⃣ Database ni nusxalash
        db_backup_path = os.path.join(backup_dir, os.path.basename(DATABASE_PATH))
        shutil.copy2(DATABASE_PATH, db_backup_path)

        # 2️⃣ Rasmlar papkasini nusxalash (agar mavjud bo‘lsa)
        images_src = "images"
        images_dest = os.path.join(backup_dir, "images")
        if os.path.exists(images_src):
            shutil.copytree(images_src, images_dest)

        print(f"✅ To‘liq backup yaratildi: {backup_dir}")
        return db_backup_path

    except Exception as e:
        print(f"❌ Backupda xatolik: {e}")
        return None


def get_latest_backup_folder():
    """Eng so‘nggi backup papkasini topish"""
    if not os.path.exists("backups"):
        return None

    folders = [f for f in os.listdir("backups") if f.startswith("backup_")]
    if not folders:
        return None

    latest = max(folders)
    return os.path.join("backups", latest)


def safe_restore_database():
    """Oxirgi backupdan (bazani va rasmlarni) qayta tiklash"""
    try:
        latest_backup_folder = get_latest_backup_folder()
        if not latest_backup_folder or not os.path.exists(latest_backup_folder):
            print("⚠️ Backup topilmadi.")
            return None

        # 1️⃣ Database ni tiklash
        db_backup_path = os.path.join(latest_backup_folder, os.path.basename(DATABASE_PATH))
        if os.path.exists(db_backup_path):
            shutil.copy2(db_backup_path, DATABASE_PATH)
            print(f"✅ Ma'lumotlar bazasi tiklandi: {db_backup_path}")
        else:
            print("⚠️ Database fayli backupda topilmadi!")

        # 2️⃣ Rasmlarni tiklash
        images_backup_path = os.path.join(latest_backup_folder, "images")
        if os.path.exists(images_backup_path):
            if os.path.exists("images"):
                shutil.rmtree("images")
            shutil.copytree(images_backup_path, "images")
            print("🖼️ Rasmlar tiklandi.")
        else:
            print("⚠️ Backupda rasm papkasi topilmadi.")

        print("♻️ To‘liq tiklash yakunlandi!")
        return latest_backup_folder

    except Exception as e:
        print(f"❌ Restoreda xatolik: {e}")
        return None
