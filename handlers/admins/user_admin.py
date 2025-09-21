# handlers/admins/user_admin.py
# ====================================================
# Adminlarga foydalanuvchilar bilan ishlash:
# - Students (Excel fayl)
# - Ustozni o‘chirish
# - Guruhlarga xabar yuborish
# - Elon yuborish (barchaga)
# ====================================================

from telebot.types import Message, CallbackQuery
from data.loader import bot, db
from config import ADMIN_ID, DB_NAME
from keyboards.inline import courses_inline
import openpyxl
import os
from datetime import datetime

# ====================================================
# 👥 Students — Excel fayl qilib chiqarish
# ====================================================
@bot.message_handler(func=lambda m: m.text == "👥 Students")
def admin_show_students(message: Message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ Siz admin emassiz.")
        return

    students = db.get_all_students()
    if not students:
        bot.send_message(message.chat.id, "👥 Hali studentlar yo‘q.")
        return

    # Excel fayl yaratamiz
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Students"

    # Sarlavha qatori
    headers = ["ID", "Ism", "Telefon", "Kurs", "Telegram", "Qo‘shilgan vaqt"]
    ws.append(headers)

    # Ma’lumotlar
    for s in students:
        ws.append(list(s))

    # Faylni vaqt bo‘yicha nomlash
    filename = f"students_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    filepath = os.path.join("data", filename)
    wb.save(filepath)

    # Admin ga yuboramiz
    with open(filepath, "rb") as f:
        bot.send_document(message.chat.id, f)

    # Faylni serverdan o‘chirib tashlaymiz
    os.remove(filepath)


# ====================================================
# 👨‍🏫 Ustozni o‘chirish
# ====================================================
@bot.message_handler(func=lambda m: m.text == "🗑 Ustozni o‘chirish")
def admin_delete_teacher(message: Message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ Siz admin emassiz.")
        return

    bot.send_message(message.chat.id, "Qaysi kursdan ustozni o‘chirmoqchisiz?", reply_markup=courses_inline("delteacher"))


@bot.callback_query_handler(func=lambda call: call.data.startswith("delteacher_"))
def process_delete_teacher(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "❌ Siz admin emassiz!")
        return

    course_id = int(call.data.split("_")[1])
    teacher = db.get_teacher_by_course(course_id)

    if not teacher:
        bot.edit_message_text("❌ Bu kursga ustoz biriktirilmagan.", call.message.chat.id, call.message.message_id)
        return

    # Tasdiqlash tugmalari
    markup = db.confirm_delete_markup("teach", teacher[0], course_id)
    bot.edit_message_text(
        f"👨‍🏫 {teacher[1]} ustozni o‘chirmoqchimisiz?",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("confirmteach_"))
def confirm_delete_teacher(call: CallbackQuery):
    _, teacher_id, course_id, choice = call.data.split("_")
    teacher_id = int(teacher_id)

    if choice == "yes":
        db.delete_teacher(teacher_id)
        bot.edit_message_text("✅ Ustoz muvaffaqiyatli o‘chirildi.", call.message.chat.id, call.message.message_id)
    else:
        bot.edit_message_text("❌ Bekor qilindi.", call.message.chat.id, call.message.message_id)


# ====================================================
# 📢 Guruhlarga xabar yuborish
# ====================================================
@bot.message_handler(func=lambda m: m.text == "📢 Guruhlarga xabar yuborish")
def admin_group_message(message: Message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ Siz admin emassiz.")
        return

    bot.send_message(message.chat.id, "✍️ Guruhlarga yubormoqchi bo‘lgan xabaringizni yuboring:")
    bot.register_next_step_handler(message, process_group_message)
def process_group_message(message: Message):
    groups = db.get_groups()
    if not groups:
        bot.send_message(message.chat.id, "❌ Bot hech bir guruhda admin emas.")
        return

    for g in groups:
        try:
            bot.send_message(g[0], message.text)
        except Exception as e:
            print(f"Guruhga yuborilmadi: {e}")

    bot.send_message(message.chat.id, "✅ Guruhlarga xabar yuborildi.")


# ====================================================
# 📢 Barchaga e’lon yuborish
# ====================================================
@bot.message_handler(func=lambda m: m.text == "📢 E’lon yuborish")
def admin_broadcast(message: Message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ Siz admin emassiz.")
        return

    bot.send_message(message.chat.id, "✍️ Foydalanuvchilarga yubormoqchi bo‘lgan elonni yuboring:")
    bot.register_next_step_handler(message, process_broadcast)


def process_broadcast(message: Message):
    users = db.get_all_users()
    if not users:
        bot.send_message(message.chat.id, "❌ Hali foydalanuvchilar yo‘q.")
        return

    for u in users:
        try:
            bot.send_message(u[0], message.text)
        except Exception as e:
            print(f"Foydalanuvchiga yuborilmadi: {e}")

    # E’lonlarni saqlash uchun
    db.save_announcement(message.text)

    bot.send_message(message.chat.id, "✅ E’lon barcha foydalanuvchilarga yuborildi.")