import os
import shutil
from datetime import datetime
from config import DATABASE_PATH


def safe_backup_database():
    """Bazani xavfsiz backup qilish"""
    try:
        if not os.path.exists(DATABASE_PATH):
            print("⚠️ Ma'lumotlar bazasi topilmadi.")
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
    """Eng so‘nggi backupni topish"""
    if not os.path.exists("backups"):
        return None

    files = [f for f in os.listdir("backups") if f.endswith(".db")]
    if not files:
        return None

    latest = max(files)  # eng oxirgisi
    return os.path.join("backups", latest)


def safe_restore_database():
    """Oxirgi backupdan qayta tiklash"""
    try:
        latest_backup = get_latest_backup()
        if not latest_backup:
            print("⚠️ Backup topilmadi.")
            return None

        shutil.copy2(latest_backup, DATABASE_PATH)
        print(f"✅ Restore qilindi: {latest_backup}")
        return latest_backup
    except Exception as e:
        print(f"❌ Restoreni tiklashda xatolik: {e}")
        return None
