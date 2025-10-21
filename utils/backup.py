import os
import shutil
import zipfile
from datetime import datetime
from config import DATABASE_PATH


# ===== BACKUP =====
def safe_backup_database():
    """📦 To‘liq tizim backup (DB + rasmlar + kurslar + guruhlar + foydalanuvchilar)"""
    try:
        os.makedirs("backups", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = f"backups/backup_{timestamp}"
        os.makedirs(backup_dir, exist_ok=True)

        # 1️⃣ Baza
        if os.path.exists(DATABASE_PATH):
            shutil.copy2(DATABASE_PATH, os.path.join(backup_dir, "data.db"))
            print("✅ Database nusxalandi.")
        else:
            print("⚠️ Database topilmadi.")

        # 2️⃣ Muhim papkalar ro‘yxati
        folders = ["images", "courses", "students", "groups", "teachers"]
        for folder in folders:
            if os.path.exists(folder):
                shutil.copytree(folder, os.path.join(backup_dir, folder))
                print(f"📁 {folder} papkasi backupga qo‘shildi.")
            else:
                print(f"⚠️ {folder} papkasi topilmadi (o‘tkazib yuborildi).")

        # 3️⃣ Qo‘shimcha fayllar (agar mavjud bo‘lsa)
        extra_files = ["users.xlsx", "courses.csv", "teachers.csv"]
        for file_name in extra_files:
            if os.path.exists(file_name):
                shutil.copy2(file_name, os.path.join(backup_dir, file_name))
                print(f"📄 {file_name} fayli backupga qo‘shildi.")

        # 4️⃣ ZIP arxiv yaratish
        zip_path = f"{backup_dir}.zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(backup_dir):
                for file in files:
                    abs_path = os.path.join(root, file)
                    rel_path = os.path.relpath(abs_path, backup_dir)
                    zipf.write(abs_path, rel_path)
        print(f"🗜️ Arxiv yaratildi: {zip_path}")

        # 5️⃣ Vaqtincha papkani o‘chirish
        shutil.rmtree(backup_dir)

        print("🎯 To‘liq backup tayyor!")
        return zip_path

    except Exception as e:
        print(f"❌ Backupda xatolik: {e}")
        return None


# ===== RESTORE =====
def safe_restore_database():
    """♻️ Oxirgi .zip backupdan to‘liq tiklash"""
    try:
        if not os.path.exists("backups"):
            print("⚠️ Backup papkasi yo‘q.")
            return None

        backups = [f for f in os.listdir("backups") if f.endswith(".zip")]
        if not backups:
            print("⚠️ Hech qanday zip backup topilmadi.")
            return None

        latest_zip = max(backups)
        zip_path = os.path.join("backups", latest_zip)

        temp_dir = "temp_restore"
        os.makedirs(temp_dir, exist_ok=True)

        # 1️⃣ Zip faylni ochish
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        print(f"🗂️ Backup ochildi: {zip_path}")

        # 2️⃣ Database ni tiklash
        db_path = os.path.join(temp_dir, "data.db")
        if os.path.exists(db_path):
            shutil.copy2(db_path, DATABASE_PATH)
            print("✅ Database tiklandi.")
        else:
            print("⚠️ Database fayli topilmadi!")

        # 3️⃣ Muhim papkalarni tiklash
        folders = ["images", "courses", "students", "groups", "teachers"]
        for folder in folders:
            src_folder = os.path.join(temp_dir, folder)
            if os.path.exists(src_folder):
                os.makedirs(folder, exist_ok=True)
                for item in os.listdir(src_folder):
                    src = os.path.join(src_folder, item)
                    dst = os.path.join(folder, item)
                    if os.path.isfile(src):
                        shutil.copy2(src, dst)
                    elif os.path.isdir(src):
                        dst_sub = os.path.join(folder, os.path.basename(src))
                        os.makedirs(dst_sub, exist_ok=True)
                        shutil.copytree(src, dst_sub, dirs_exist_ok=True)
                print(f"📂 {folder} papkasi tiklandi.")
            else:
                print(f"⚠️ {folder} papkasi backupda topilmadi.")

        # 4️⃣ Qo‘shimcha fayllar tiklash
        for file_name in ["users.xlsx", "courses.csv", "teachers.csv"]:
            src = os.path.join(temp_dir, file_name)
            if os.path.exists(src):
                shutil.copy2(src, file_name)
                print(f"📄 {file_name} qayta tiklandi.")

        shutil.rmtree(temp_dir)
        print("♻️ Tiklash yakunlandi!")
        return zip_path

    except Exception as e:
        print(f"❌ Restoreda xatolik: {e}")
        return None
