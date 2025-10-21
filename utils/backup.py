import os
import shutil
from datetime import datetime
from config import DATABASE_PATH


def safe_backup_database():
    """✅ To‘liq (bazani, rasmlarni va yordamchi fayllarni) xavfsiz backup qilish"""
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
        print("📦 Ma'lumotlar bazasi nusxalandi.")

        # 2️⃣ Rasmlar papkasini nusxalash (agar mavjud bo‘lsa)
        images_src = "images"
        if os.path.exists(images_src):
            shutil.copytree(images_src, os.path.join(backup_dir, "images"))
            print("🖼️ Rasmlar nusxalandi.")
        else:
            print("⚠️ 'images' papkasi topilmadi.")

        # 3️⃣ Qo‘shimcha fayllarni nusxalash (agar mavjud bo‘lsa)
        extra_files = ["users.xlsx", "courses.csv", "teachers.csv"]
        for file_name in extra_files:
            if os.path.exists(file_name):
                shutil.copy2(file_name, os.path.join(backup_dir, file_name))
                print(f"📁 {file_name} fayli backupga qo‘shildi.")

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
    """♻️ Oxirgi backupdan (bazani, rasmlarni va qo‘shimcha fayllarni) tiklash"""
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

        # 2️⃣ Rasmlarni tiklash (mavjudlarini saqlab)
        images_backup_path = os.path.join(latest_backup_folder, "images")
        if os.path.exists(images_backup_path):
            os.makedirs("images", exist_ok=True)
            for file_name in os.listdir(images_backup_path):
                src = os.path.join(images_backup_path, file_name)
                dst = os.path.join("images", file_name)
                if os.path.isfile(src):
                    shutil.copy2(src, dst)
            print("🖼️ Rasmlar tiklandi (mavjudlarini o‘chirilmadi).")
        else:
            print("⚠️ Backupda rasm papkasi topilmadi, mavjud rasmlar o‘zgartirilmadi.")

        # 3️⃣ Qo‘shimcha fayllarni qayta tiklash (agar mavjud bo‘lsa)
        extra_files = ["users.xlsx", "courses.csv", "teachers.csv"]
        for file_name in extra_files:
            backup_path = os.path.join(latest_backup_folder, file_name)
            if os.path.exists(backup_path):
                shutil.copy2(backup_path, file_name)
                print(f"📁 {file_name} qayta tiklandi.")

        print("♻️ To‘liq tiklash yakunlandi!")
        return latest_backup_folder

    except Exception as e:
        print(f"❌ Restoreda xatolik: {e}")
        return None
