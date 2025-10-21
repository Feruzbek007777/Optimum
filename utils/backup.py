import os
import shutil
import zipfile
from datetime import datetime
from config import DATABASE_PATH


# === TO‘LIQ BACKUP ===
def safe_backup_database():
    """💾 To‘liq backup (DB, rasmlar, kurslar, guruhlar, o‘quvchilar, ustozlar, excel fayllar)"""
    try:
        os.makedirs("backups", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = f"backups/backup_{timestamp}"
        os.makedirs(backup_dir, exist_ok=True)

        print("🔄 Backup jarayoni boshlandi...")

        # 1️⃣ Database nusxalash
        if os.path.exists(DATABASE_PATH):
            shutil.copy2(DATABASE_PATH, os.path.join(backup_dir, "data.db"))
            print("✅ Database nusxalandi.")
        else:
            print("⚠️ Database topilmadi!")

        # 2️⃣ Muhim papkalar
        folders = ["images", "courses", "students", "groups", "teachers"]
        for folder in folders:
            if os.path.exists(folder):
                shutil.copytree(folder, os.path.join(backup_dir, folder))
                print(f"📁 {folder} papkasi backupga qo‘shildi.")
            else:
                print(f"⚠️ {folder} topilmadi (o‘tkazib yuborildi).")

        # 3️⃣ Qo‘shimcha fayllar
        extra_files = ["users.xlsx", "courses.csv", "teachers.csv"]
        for file_name in extra_files:
            if os.path.exists(file_name):
                shutil.copy2(file_name, os.path.join(backup_dir, file_name))
                print(f"📄 {file_name} backupga qo‘shildi.")

        # 4️⃣ ZIP yaratish
        zip_path = f"{backup_dir}.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(backup_dir):
                for file in files:
                    abs_path = os.path.join(root, file)
                    rel_path = os.path.relpath(abs_path, backup_dir)
                    zipf.write(abs_path, rel_path)
        print(f"🗜️ ZIP arxiv tayyor: {zip_path}")

        # 5️⃣ Ortiqcha papkani o‘chirish
        shutil.rmtree(backup_dir)
        print("🎯 Backup muvaffaqiyatli yakunlandi!")
        return zip_path

    except Exception as e:
        print(f"❌ Backupda xatolik: {e}")
        return None


# === OXIRGI BACKUPNI QAYTARISH ===
def get_latest_zip_backup():
    """Eng so‘nggi .zip backupni topadi"""
    if not os.path.exists("backups"):
        return None
    backups = [f for f in os.listdir("backups") if f.endswith(".zip")]
    if not backups:
        return None
    latest = max(backups)
    return os.path.join("backups", latest)


# === RESTORE ===
def safe_restore_database():
    """♻️ Oxirgi ZIP backupdan tiklash (barcha ma’lumotlar bilan)"""
    try:
        zip_path = get_latest_zip_backup()
        if not zip_path or not os.path.exists(zip_path):
            print("⚠️ Hech qanday zip backup topilmadi.")
            return None

        print(f"🔄 Restore jarayoni boshlandi: {zip_path}")

        temp_dir = "temp_restore"
        os.makedirs(temp_dir, exist_ok=True)

        # 1️⃣ ZIP faylni ochamiz
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(temp_dir)
        print("🗂️ Backup arxiv ochildi.")

        # 2️⃣ Database tiklash
        db_path = os.path.join(temp_dir, "data.db")
        if os.path.exists(db_path):
            shutil.copy2(db_path, DATABASE_PATH)
            print("✅ Database qayta tiklandi.")
        else:
            print("⚠️ Database fayli topilmadi!")

        # 3️⃣ Papkalarni qaytarish
        folders = ["images", "courses", "students", "groups", "teachers"]
        for folder in folders:
            src_folder = os.path.join(temp_dir, folder)
            if os.path.exists(src_folder):
                os.makedirs(folder, exist_ok=True)
                shutil.copytree(src_folder, folder, dirs_exist_ok=True)
                print(f"📂 {folder} papkasi qayta tiklandi.")
            else:
                print(f"⚠️ {folder} papkasi backupda topilmadi.")

        # 4️⃣ Qo‘shimcha fayllar
        for file_name in ["users.xlsx", "courses.csv", "teachers.csv"]:
            src = os.path.join(temp_dir, file_name)
            if os.path.exists(src):
                shutil.copy2(src, file_name)
                print(f"📄 {file_name} qayta tiklandi.")

        # 5️⃣ Ortiqcha vaqtinchalik papkani o‘chirish
        shutil.rmtree(temp_dir)
        print("♻️ Restore muvaffaqiyatli yakunlandi!")
        return zip_path

    except Exception as e:
        print(f"❌ Restoreda xatolik: {e}")
        return None
