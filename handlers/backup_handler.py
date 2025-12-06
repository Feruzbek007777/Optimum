import os
import zipfile
import shutil

from telebot.types import ReplyKeyboardMarkup, KeyboardButton

from config import ADMINS, DATABASE_PATH
from database.database import add_admin_group, delete_admin_group

BACKUP_DIR = "backups"


# ---------- MANUAL BACKUP / RESTORE FUNKSIYALAR ----------

def safe_backup_database() -> str | None:
    """
    Admin tugmasi uchun manual backup.
    DATABASE_PATH, images/, data/quiz, data/fastwords ni ZIP qilib BACKUP_DIR ichiga saqlaydi.
    Avto-backupdan mustaqil, lekin tuzilishi o'xshash.
    """
    os.makedirs(BACKUP_DIR, exist_ok=True)

    from datetime import datetime
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"manual_backup_{now}.zip"
    backup_path = os.path.join(BACKUP_DIR, backup_name)

    try:
        with zipfile.ZipFile(backup_path, "w", zipfile.ZIP_DEFLATED) as zf:
            # 1) Database
            if os.path.exists(DATABASE_PATH):
                # Zip ichida DB asl yo'li bilan saqlanadi
                zf.write(DATABASE_PATH, arcname=DATABASE_PATH)
            else:
                print(f"[MANUAL BACKUP] Ogohlantirish: DATABASE_PATH topilmadi: {DATABASE_PATH}")

            # 2) Rasmlar
            if os.path.isdir("images"):
                for root, dirs, files in os.walk("images"):
                    for file in files:
                        full_path = os.path.join(root, file)
                        rel_path = os.path.relpath(full_path, ".")
                        zf.write(full_path, arcname=rel_path)

            # 3) Quiz JSON
            quiz_dir = os.path.join("data", "quiz")
            if os.path.isdir(quiz_dir):
                for root, dirs, files in os.walk(quiz_dir):
                    for file in files:
                        full_path = os.path.join(root, file)
                        rel_path = os.path.relpath(full_path, ".")
                        zf.write(full_path, arcname=rel_path)

            # 4) Fastwords JSON
            fast_dir = os.path.join("data", "fastwords")
            if os.path.isdir(fast_dir):
                for root, dirs, files in os.walk(fast_dir):
                    for file in files:
                        full_path = os.path.join(root, file)
                        rel_path = os.path.relpath(full_path, ".")
                        zf.write(full_path, arcname=rel_path)

        print(f"✅ MANUAL BACKUP yaratildi: {backup_path}")
        return backup_path

    except Exception as e:
        print(f"❌ MANUAL BACKUP xatosi: {e}")
        return None


def safe_restore_database() -> str | None:
    """
    Admin tugmasi uchun manual restore.
    BACKUP_DIR ichidan ENGIN YANGI .zip faylni olib:
      - DATABASE_PATH faylini qayta yozadi,
      - images/, data/quiz, data/fastwords ni ustiga yozadi.
    ⚠️ Restore qilgandan keyin botni qayta ishga tushirish tavsiya qilinadi.
    """
    if not os.path.isdir(BACKUP_DIR):
        print("[RESTORE] backups papkasi topilmadi.")
        return None

    # .zip fayllarni topamiz
    zip_files = [
        os.path.join(BACKUP_DIR, f)
        for f in os.listdir(BACKUP_DIR)
        if f.endswith(".zip")
    ]

    if not zip_files:
        print("[RESTORE] Hech qanday backup topilmadi.")
        return None

    # Eng oxirgi (eng yangi) zip faylni tanlaymiz (modification time bo'yicha)
    latest_zip = max(zip_files, key=os.path.getmtime)

    try:
        with zipfile.ZipFile(latest_zip, "r") as zf:
            # 1) Avval DB faylini alohida qayta yozamiz
            db_basename = os.path.basename(DATABASE_PATH)

            for member in zf.namelist():
                # Agar bu DB fayl bo'lsa (yo'li qanday bo'lishidan qat'i nazar)
                if os.path.basename(member) == db_basename:
                    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
                    with zf.open(member) as src, open(DATABASE_PATH, "wb") as dst:
                        shutil.copyfileobj(src, dst)
                    print(f"✅ DB tiklandi: {DATABASE_PATH}")
                    break

            # 2) Qolgan barcha fayllarni odatdagi joyiga extract qilamiz
            for member in zf.namelist():
                # DB faylni yuqorida alohida tiklab bo'ldik
                if os.path.basename(member) == db_basename:
                    continue
                zf.extract(member, ".")

        print(f"✅ RESTORE bajarildi: {latest_zip}")
        return latest_zip

    except Exception as e:
        print(f"❌ RESTORE xatosi: {e}")
        return None


# ---------- HANDLERLARNI SOZLASH ----------

def setup_backup_handlers(bot):
    """
    main.py ichida:
        from handlers.backup_handler import setup_backup_handlers
        ...
        setup_backup_handlers(bot)
    deb chaqiriladi.
    """

    # 📌 Guruhga bot qo'shilganda — guruhni DB ga yozish
    @bot.message_handler(content_types=['new_chat_members'])
    def handle_new_chat_members(message):
        for member in message.new_chat_members:
            if member.id == bot.get_me().id:
                group_id = message.chat.id
                group_title = message.chat.title
                success = add_admin_group(group_id, group_title)
                if success:
                    bot.send_message(group_id, "✅ Bot qo‘shildi! Guruh ma'lumotlari saqlandi.")
                else:
                    bot.send_message(group_id, "❌ Guruh ma'lumotlarini saqlashda xatolik!")

    # 📌 Bot guruhdan chiqarilganda — guruhni DB dan o'chirish
    @bot.message_handler(content_types=['left_chat_member'])
    def handle_left_chat_member(message):
        if message.left_chat_member.id == bot.get_me().id:
            group_id = message.chat.id
            success = delete_admin_group(group_id)
            if success:
                print(f"✅ Guruhdan chiqarildi: {group_id}")

    # 📌 Admin uchun database paneli (/database)
    @bot.message_handler(commands=['database'])
    def show_database_panel(message):
        if message.from_user.id in ADMINS:
            markup = ReplyKeyboardMarkup(resize_keyboard=True)
            markup.row(KeyboardButton("💾 Backup"), KeyboardButton("♻️ Restore"))
            markup.add(KeyboardButton("⬅️ Ortga"))
            bot.send_message(message.chat.id, "📂 Ma'lumotlar bazasi paneli:", reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "❌ Siz admin emassiz!")

    # 📌 💾 Backup tugmasi — qo'lda backup
    @bot.message_handler(func=lambda m: m.chat.type == "private" and m.text == "💾 Backup")
    def manual_backup(message):
        if message.from_user.id not in ADMINS:
            bot.send_message(message.chat.id, "❌ Sizda bu amal uchun ruxsat yo'q.")
            return

        backup_file = safe_backup_database()
        if backup_file:
            try:
                with open(backup_file, "rb") as f:
                    bot.send_document(message.chat.id, f, caption="✅ Backup fayli:")
                bot.send_message(message.chat.id, "✅ Backup yaratildi va yuborildi.")
            except Exception as e:
                print(f"❌ Backup yuborishda xatolik: {e}")
                bot.send_message(message.chat.id, "❌ Backup faylini yuborishda xatolik yuz berdi.")
        else:
            bot.send_message(message.chat.id, "❌ Backup yaratishda xatolik!")

    # 📌 ♻️ Restore tugmasi — oxirgi backup'dan tiklash
    @bot.message_handler(func=lambda m: m.chat.type == "private" and m.text == "♻️ Restore")
    def manual_restore(message):
        if message.from_user.id not in ADMINS:
            bot.send_message(message.chat.id, "❌ Sizda bu amal uchun ruxsat yo'q.")
            return

        restored_file = safe_restore_database()
        if restored_file:
            bot.send_message(
                message.chat.id,
                f"✅ Restore qilindi.\nManba backup: {restored_file}\n\n⚠️ Botni qayta ishga tushirish tavsiya qilinadi."
            )
        else:
            bot.send_message(message.chat.id, "❌ Restore uchun mos backup topilmadi.")
