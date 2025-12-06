import os
import time
import threading
import zipfile
import datetime

from config import DATABASE_PATH

# Backuplar saqlanadigan papka
BACKUP_DIR = "backups"

# Rasmlar va ma'lumot papkalari
IMAGES_DIR = "images"
DATA_DIRS = [
    os.path.join("data", "quiz"),
    os.path.join("data", "fastwords"),
]


def ensure_dir(path: str):
    """Papka mavjud bo'lmasa, yaratadi."""
    os.makedirs(path, exist_ok=True)


def create_backup() -> str:
    """
    Bitta backup ZIP fayl yaratadi:
    - SQLite database (DATABASE_PATH)
    - images/
    - data/quiz/
    - data/fastwords/
    """
    ensure_dir(BACKUP_DIR)

    now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"backup_{now}.zip"
    backup_path = os.path.join(BACKUP_DIR, backup_name)

    try:
        with zipfile.ZipFile(backup_path, "w", zipfile.ZIP_DEFLATED) as zf:
            # 1) Database
            if os.path.exists(DATABASE_PATH):
                # Zip ichida chiroyli ko'rinishi uchun "db/" ichiga joylaymiz
                arcname = os.path.join("db", os.path.basename(DATABASE_PATH))
                zf.write(DATABASE_PATH, arcname=arcname)
            else:
                print(f"[BACKUP] Ogohlantirish: DATABASE_PATH topilmadi: {DATABASE_PATH}")

            # 2) Rasmlar papkasi
            if os.path.isdir(IMAGES_DIR):
                for root, dirs, files in os.walk(IMAGES_DIR):
                    for file in files:
                        full_path = os.path.join(root, file)
                        # Zip ichidagi nisbiy yo'l
                        rel_path = os.path.relpath(full_path, ".")
                        zf.write(full_path, arcname=rel_path)
            else:
                print(f"[BACKUP] Ogohlantirish: '{IMAGES_DIR}' papkasi topilmadi.")

            # 3) Ma'lumot papkalari (quiz, fastwords)
            for data_dir in DATA_DIRS:
                if os.path.isdir(data_dir):
                    for root, dirs, files in os.walk(data_dir):
                        for file in files:
                            full_path = os.path.join(root, file)
                            rel_path = os.path.relpath(full_path, ".")
                            zf.write(full_path, arcname=rel_path)
                else:
                    print(f"[BACKUP] Ogohlantirish: '{data_dir}' papkasi topilmadi.")

        print(f"✅ BACKUP yaratildi: {backup_path}")
        return backup_path

    except Exception as e:
        print(f"❌ Backupda xatolik: {e}")
        return ""


def _backup_loop(interval_hours: float):
    """
    Ichki funksiya: cheksiz sikl, har interval_hours soatda backup qiladi.
    Albatta alohida thread'da ishlaydi.
    """
    interval_seconds = int(interval_hours * 3600)

    print(f"⏱ Avto-backup sikli ishga tushdi. Har {interval_hours} soatda backup qilinadi.")

    while True:
        try:
            create_backup()
        except Exception as e:
            print(f"❌ BACKUP loop xatosi: {e}")
        # Keyingi backupgacha kutamiz
        time.sleep(interval_seconds)


def start_auto_backup(interval_hours: float = 6.0):
    """
    Asosiy funksiya: main.py ichida bitta marta chaqiriladi.
    U alohida daemon-thread ochib, _backup_loop'ni ishga tushiradi.
    """
    t = threading.Thread(
        target=_backup_loop,
        args=(interval_hours,),
        daemon=True  # Bot yopilsa, thread ham yopiladi
    )
    t.start()
    print(f"🚀 Avto-backup ishga tushirildi (har {interval_hours} soatda).")
