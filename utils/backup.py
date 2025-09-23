import sqlite3
import os
import shutil
from datetime import datetime
from config import DATABASE_PATH


def safe_backup_database() :
    """Xavfsiz backup - asl ma'lumotlarni hech qanday holatda o'chirmaydi"""
    try :
        # 1. Avval asl ma'lumotlar bazasi mavjudligini tekshirish
        if not os.path.exists(DATABASE_PATH) :
            print("⚠️ Asl ma'lumotlar bazasi topilmadi. Yangi yaratilmoqda...")
            from database.database import init_database
            init_database()
            return None

        # 2. Backup papkasini yaratish
        backup_dir = "backups"
        os.makedirs(backup_dir, exist_ok=True)

        # 3. Backup fayl nomi
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(backup_dir, f"backup_{timestamp}.db")

        # 4. ASL MA'LUMOTLARNI O'CHIRMASDAN nusxa olish
        shutil.copy2(DATABASE_PATH, backup_file)

        print(f"✅ Backup yaratildi: {backup_file}")
        print(f"📊 Asl fayl hajmi: {os.path.getsize(DATABASE_PATH)} byte")
        print(f"📊 Backup hajmi: {os.path.getsize(backup_file)} byte")

        return backup_file

    except Exception as e :
        print(f"❌ Backupda xatolik: {e}")
        return None


def safe_restore_database(backup_file) :
    """Xavfsiz restore - faqat asl ma'lumotlar yo'qolgan taqdirda tiklaydi"""
    try :
        # 1. Asl ma'lumotlar bazasi mavjudmi?
        if os.path.exists(DATABASE_PATH) :
            print("ℹ️ Asl ma'lumotlar bazasi mavjud. Restore kerak emas.")
            return False

        # 2. Backup fayli mavjudmi?
        if not os.path.exists(backup_file) :
            print(f"❌ Backup fayli topilmadi: {backup_file}")
            return False

        # 3. Faqat asl ma'lumotlar yo'qolgan taqdirda restore qilish
        print(f"🔍 Asl ma'lumotlar yo'qolgan. Backup dan tiklanmoqda...")
        shutil.copy2(backup_file, DATABASE_PATH)

        print(f"✅ Ma'lumotlar qayta tiklandi: {backup_file}")
        return True

    except Exception as e :
        print(f"❌ Restore da xatolik: {e}")
        return False


def get_latest_backup() :
    """Eng so'nggi backup ni topish"""
    backup_dir = "backups"
    if not os.path.exists(backup_dir) :
        return None

    backup_files = [f for f in os.listdir(backup_dir) if f.startswith("backup_") and f.endswith(".db")]
    if not backup_files :
        return None

    latest_backup = max(backup_files)
    return os.path.join(backup_dir, latest_backup)


def safe_auto_restore() :
    """Xavfsiz avtomatik restore - faqat zarurat bo'lsa"""
    # Asl ma'lumotlar mavjudmi?
    if os.path.exists(DATABASE_PATH) :
        print("✅ Asl ma'lumotlar bazasi mavjud. Restore kerak emas.")
        return False

    # Backup dan tiklash
    latest_backup = get_latest_backup()
    if latest_backup :
        return safe_restore_database(latest_backup)
    else :
        print("⚠️ Hech qanday backup topilmadi. Yangi ma'lumotlar bazasi yaratiladi.")
        from database.database import init_database
        init_database()
        return False


def safe_cleanup_old_backups(days_to_keep=7) :
    """Faqat backup fayllarni o'chirish (asl ma'lumotlarni emas)"""
    backup_dir = "backups"
    if not os.path.exists(backup_dir) :
        return

    current_time = datetime.now().timestamp()
    deleted_count = 0

    for filename in os.listdir(backup_dir) :
        filepath = os.path.join(backup_dir, filename)
        if os.path.isfile(filepath) and filename.startswith("backup_") :
            file_time = os.path.getmtime(filepath)
            days_diff = (current_time - file_time) / (24 * 3600)

            if days_diff > days_to_keep :
                os.remove(filepath)
                deleted_count += 1
                print(f"🗑️ Eski backup o'chirildi: {filename}")

    print(f"📊 Jami {deleted_count} ta eski backup o'chirildi")


def initialize_database_safely() :
    """Xavfsiz ishga tushirish"""
    print("🔍 Ma'lumotlar bazasi holati tekshirilmoqda...")

    # 1. Avtomatik restore (faqat zarurat bo'lsa)
    restored = safe_auto_restore()

    # 2. Backup yaratish (asl ma'lumotlarni o'chirmasdan)
    if not restored :  # Agar restore qilinmagan bo'lsa (ya'ni asl ma'lumotlar mavjud)
        safe_backup_database()

    # 3. Eski backup larni tozalash
    safe_cleanup_old_backups()

    print("✅ Xavfsiz ishga tushirish tugallandi")


if __name__ == "__main__" :
    initialize_database_safely()