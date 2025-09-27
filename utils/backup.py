import sqlite3
import os
import shutil
from datetime import datetime
from config import DATABASE_PATH


def safe_backup_database():
    """Asl DB ni o‘chirmasdan backup yaratadi"""
    try:
        if not os.path.exists(DATABASE_PATH):
            print("⚠️ Asl DB topilmadi. Yangi yaratilmoqda...")
            from database.database import init_database
            init_database()
            return None

        os.makedirs("backups", exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join("backups", f"backup_{timestamp}.db")

        shutil.copy2(DATABASE_PATH, backup_file)

        print(f"✅ Backup yaratildi: {backup_file}")
        return backup_file

    except Exception as e:
        print(f"❌ Backupda xatolik: {e}")
        return None


def get_latest_backup():
    """Eng oxirgi backup faylini topish"""
    backup_dir = "backups"
    if not os.path.exists(backup_dir):
        return None

    files = [f for f in os.listdir(backup_dir) if f.startswith("backup_") and f.endswith(".db")]
    if not files:
        return None

    latest = max(files)
    return os.path.join(backup_dir, latest)


def manual_restore_database():
    """Eng so‘nggi backup dan DB ni qayta tiklash"""
    try:
        latest_backup = get_latest_backup()
        if not latest_backup:
            print("❌ Backup topilmadi.")
            return False

        shutil.copy2(latest_backup, DATABASE_PATH)
        print(f"✅ Restore qilindi: {latest_backup}")
        return True

    except Exception as e:
        print(f"❌ Restore xatosi: {e}")
        return False
