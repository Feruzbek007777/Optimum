# handlers/admins/commands.py
from data.loader import bot
from telebot.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMIN_ID
from database.database import Database
from keyboards.default import admin_main_menu, request_contact_markup, make_buttons, main_menu
from keyboards.inline import courses_inline

db = Database()

# temp storages for multi-step flows (use admin_id or user_id as key)
temp_teachers = {}   # admin_user_id -> dict {course_id, full_name, image_url, achievements}
temp_enrolls = {}    # user_id -> dict {course_id, full_name}
pending_delete = {}  # admin_user_id -> course_id


def is_admin(user_id):
    return user_id == ADMIN_ID


# Admin panel
@bot.message_handler(commands=['admin'])
def admin_panel(message: Message):
    if not is_admin(message.from_user.id):
        bot.send_message(message.chat.id, "❌ Siz admin emassiz.")
        return
    bot.send_message(message.chat.id, "👨‍💻 Admin panelga xush kelibsiz!", reply_markup=admin_main_menu())


# ➕ Kurs qo‘shish
@bot.message_handler(func=lambda msg: msg.text == "➕ Kurs qo‘shish")
def add_course_cmd(message: Message):
    if not is_admin(message.from_user.id):
        return
    bot.send_message(message.chat.id, "Yangi kurs nomini kiriting:")
    bot.register_next_step_handler(message, add_course_name)


def add_course_name(message: Message):
    if not is_admin(message.from_user.id):
        return
    name = message.text.strip()
    if not name:
        bot.send_message(message.chat.id, "❌ Noto'g'ri nom.")
        return
    course_id = db.insert_course(name)
    bot.send_message(message.chat.id, f"✅ Kurs qo'shildi: <b>{name}</b> (id: {course_id})", parse_mode="HTML")


# 📋 Kurslar ro'yxati
@bot.message_handler(func=lambda msg: msg.text == "📋 Kurslar ro‘yxati")
def list_courses_cmd(message: Message):
    if not is_admin(message.from_user.id):
        return
    courses = db.get_courses()
    if not courses:
        bot.send_message(message.chat.id, "Kurslar mavjud emas.")
        return
    text = "📚 Kurslar ro‘yxati:\n" + "\n".join([f"{cid} — {name}" for cid, name in courses])
    bot.send_message(message.chat.id, text)


# 📝 Kursga ma'lumot qo'shish -> shows edit inline
@bot.message_handler(func=lambda msg: msg.text == "📝 Kursga ma’lumot qo‘shish")
def add_course_info_cmd(message: Message):
    if not is_admin(message.from_user.id):
        return
    bot.send_message(message.chat.id, "Qaysi kursga ma'lumot qo'shmoqchisiz?", reply_markup=courses_inline(prefix="edit"))


# 👨‍🏫 Ustoz qo'shish -> shows teacher inline
@bot.message_handler(func=lambda msg: msg.text == "👨‍🏫 Ustoz qo‘shish")
def add_teacher_cmd(message: Message):
    if not is_admin(message.from_user.id):
        return
    bot.send_message(message.chat.id, "Qaysi kurs uchun ustoz qo'shmoqchisiz?", reply_markup=courses_inline(prefix="teacher"))


# ❌ Kursni o'chirish -> shows delete inline
@bot.message_handler(func=lambda msg: msg.text == "❌ Kursni o‘chirish")
def delete_course_cmd(message: Message):
    if not is_admin(message.from_user.id):
        return
    bot.send_message(message.chat.id, "Qaysi kursni o'chirmoqchisiz?", reply_markup=courses_inline(prefix="del"))


# 👥 Students -> show all students
@bot.message_handler(func=lambda msg: msg.text == "👥 Students")
def admin_show_students(message: Message):
    if not is_admin(message.from_user.id):
        return
    rows = db.get_all_students()
    if not rows:
        bot.send_message(message.chat.id, "Students jadvalida yozilganlar yo'q.")
        return
    chunks = []
    for r in rows:
        sid, full_name, phone, course_name, created_at = r
        course_name = course_name or "—"
        chunks.append(f"{full_name} | {phone} ({course_name})")
    # split into messages of reasonable length
    text = "👥 Ro'yxatdan o'tganlar:\n\n" + "\n".join(chunks)
    bot.send_message(message.chat.id, text)


# Guruhlarga xabar yuborish
@bot.message_handler(func=lambda msg: msg.text == "📢 Guruhlarga xabar yuborish")
def broadcast_cmd(message: Message):
    if not is_admin(message.from_user.id):
        return
    bot.send_message(message.chat.id, "📨 Yubormoqchi bo'lgan xabarni kiriting:")
    bot.register_next_step_handler(message, broadcast_send)


def broadcast_send(message: Message):
    if not is_admin(message.from_user.id):
        return
    text = message.text
    groups = db.get_groups()
    success = fail = 0
    for chat_id in groups:
        try:
            bot.send_message(chat_id, f"📢 Admin xabari:\n\n{text}")
            success += 1
        except Exception:
            fail += 1
    bot.send_message(message.chat.id, f"✅ Xabar yuborildi. Muvaffaqiyatli: {success} | Xato: {fail}")


# ===== CALLBACK HANDLER for course_, edit_, teacher_, enroll_, del_, teacherinfo_, delconfirm_ =====
@bot.callback_query_handler(func=lambda call: call.data and call.data.split("_", 1)[0] in ("course", "edit", "teacher", "enroll", "del", "teacherinfo", "delconfirm"))
def callback_handler(call: CallbackQuery):
    data = call.data

    # ---------- course view for users ----------
    if data.startswith("course_"):
        course_id = int(data.split("_", 1)[1])
        course = db.get_course_by_id(course_id)
        if not course:
            bot.answer_callback_query(call.id, "Kurs topilmadi")
            return
        # get fields in same order as DB
        cid = course[0]; name = course[1]; description = course[2]
        price = course[3]; schedule = course[4]; image_url = course[5]; teacher_id = course[6]
        text = f"📚 <b>{name}</b>\n\n💰 Narxi: {price or '—'}\n🕒 Vaqti: {schedule or '—'}"
        if description:
            text += f"\n\n{description}"
        markup = InlineKeyboardMarkup()
        # show teacher info button if teacher exists
        if teacher_id:
            markup.add(InlineKeyboardButton("👨‍🏫 Ustoz haqida", callback_data=f"teacherinfo_{teacher_id}"))
        bot.send_message(call.message.chat.id, text, parse_mode="HTML", reply_markup=markup)
        return

    # ---------- teacherinfo_ (show teacher details) ----------
    if data.startswith("teacherinfo_"):
        teacher_id = int(data.split("_", 1)[1])
        teacher = db.get_teacher_by_id(teacher_id)
        if not teacher:
            bot.answer_callback_query(call.id, "Ustoz topilmadi")
            return
        tid, full_name, bio, achievements, image_url, course_id = teacher
        text = f"👨‍🏫 <b>{full_name}</b>\n"
        if bio:
            text += f"{bio}\n"
        if achievements:
            text += f"🏆 {achievements}"
        if image_url:
            try:
                bot.send_photo(call.message.chat.id, image_url, caption=text, parse_mode="HTML")
                return
            except Exception:
                pass
        bot.send_message(call.message.chat.id, text, parse_mode="HTML")
        return

    # ---------- admin edit flow (edit_{id}) ----------
    if data.startswith("edit_"):
        if not is_admin(call.from_user.id):
            bot.answer_callback_query(call.id, "Siz admin emassiz")
            return
        course_id = int(data.split("_", 1)[1])
        bot.send_message(call.message.chat.id, "✍️ Kurs tavsifini kiriting:")
        bot.register_next_step_handler(call.message, save_course_description, course_id)
        return

    # ---------- admin teacher add (teacher_{id}) ----------
    if data.startswith("teacher_"):
        if not is_admin(call.from_user.id):
            bot.answer_callback_query(call.id, "Siz admin emassiz")
            return
        course_id = int(data.split("_", 1)[1])
        bot.send_message(call.message.chat.id, "👨‍🏫 Ustozning ism-familiyasin kiriting:")
        bot.register_next_step_handler(call.message, save_teacher_name, course_id)
        return

    # ---------- enroll (enroll_{id}) ----------
    if data.startswith("enroll_"):
        course_id = int(data.split("_", 1)[1])
        course = db.get_course_by_id(course_id)
        if not course:
            bot.answer_callback_query(call.id, "Kurs topilmadi")
            return
        cid, name = course[0], course[1]
        text = f"📚 <b>{name}</b>\n\n"
        price = course[3]; schedule = course[4]; description = course[2]
        text += f"💰 Narxi: {price or '—'}\n🕒 Vaqti: {schedule or '—'}"
        if description:
            text += f"\n\n{description}"
        bot.send_message(call.message.chat.id, text, parse_mode="HTML")
        bot.send_message(call.message.chat.id, "Ismingizni kiriting:")
        bot.register_next_step_handler(call.message, enroll_get_name, course_id)
        return

    # ---------- delete flow start (del_{id}) ----------
    if data.startswith("del_"):
        if not is_admin(call.from_user.id):
            bot.answer_callback_query(call.id, "Siz admin emassiz")
            return
        course_id = int(data.split("_", 1)[1])
        pending_delete[call.from_user.id] = course_id
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("✅ Ha", callback_data=f"delconfirm_yes_{course_id}"),
                   InlineKeyboardButton("❌ Yo'q", callback_data=f"delconfirm_no_{course_id}"))
        bot.send_message(call.message.chat.id, "❗ Haqiqatan o'chirmoqchimisiz?", reply_markup=markup)
        return

    # ---------- delete confirm ----------
    if data.startswith("delconfirm_"):
        parts = data.split("_")
        # format delconfirm_{yes/no}_{id}
        if len(parts) < 3:
            return
        _, choice, cid = parts[0], parts[1], parts[2]
        course_id = int(cid)
        if not is_admin(call.from_user.id):
            bot.answer_callback_query(call.id, "Siz admin emassiz")
            return
        if choice == "yes":
            db.delete_course(course_id)
            bot.send_message(call.message.chat.id, "✅ Kurs o'chirildi.")
        else:
            bot.send_message(call.message.chat.id, "❌ O'chirish bekor qilindi.")
        return


# ===== SAVE COURSE (desc -> price -> schedule) =====
def save_course_description(message: Message, course_id: int):
    if not is_admin(message.from_user.id):
        return
    desc = message.text.strip()
    db.update_course(course_id, description=desc)
    bot.send_message(message.chat.id, "✅ Tavsif saqlandi.\nNarxni kiriting:")
    bot.register_next_step_handler(message, save_course_price, course_id)


def save_course_price(message: Message, course_id: int):
    if not is_admin(message.from_user.id):
        return
    price = message.text.strip()
    db.update_course(course_id, price=price)
    bot.send_message(message.chat.id, "✅ Narx saqlandi.\nVaqtni kiriting:")
    bot.register_next_step_handler(message, save_course_schedule, course_id)


def save_course_schedule(message: Message, course_id: int):
    if not is_admin(message.from_user.id):
        return
    schedule = message.text.strip()
    db.update_course(course_id, schedule=schedule)
    bot.send_message(message.chat.id, "✅ Kurs ma'lumotlari yangilandi.")


# ===== TEACHER FLOW (name -> photo -> achievements) =====
def save_teacher_name(message: Message, course_id: int):
    if not is_admin(message.from_user.id):
        return
    full_name = message.text.strip()
    if not full_name:
        bot.send_message(message.chat.id, "❌ Iltimos ism-familiyani kiriting.")
        return
    admin_id = message.from_user.id
    temp_teachers[admin_id] = {"course_id": course_id, "full_name": full_name}
    bot.send_message(message.chat.id, "📸 Endi ustoz rasmini yuboring:")
    bot.register_next_step_handler(message, save_teacher_photo)


def save_teacher_photo(message: Message):
    admin_id = message.from_user.id
    if admin_id not in temp_teachers:
        bot.send_message(message.chat.id, "❌ Xatolik! Avval kursni tanlang.")
        return
    if not message.photo:
        bot.send_message(message.chat.id, "❌ Iltimos rasm yuboring.")
        bot.register_next_step_handler(message, save_teacher_photo)
        return
    file_id = message.photo[-1].file_id
    temp_teachers[admin_id]["image_url"] = file_id
    bot.send_message(message.chat.id, "🏆 Endi ustoz yutuqlarini (qisqacha) kiriting:")
    bot.register_next_step_handler(message, save_teacher_achievements)


def save_teacher_achievements(message: Message):
    admin_id = message.from_user.id
    if admin_id not in temp_teachers:
        bot.send_message(message.chat.id, "❌ Xatolik! Avval kursni tanlang.")
        return
    achievements = message.text.strip()
    data = temp_teachers.pop(admin_id)
    full_name = data.get("full_name")
    image_url = data.get("image_url")
    course_id = data.get("course_id")
    bio = ""  # optional
    # save teacher
    teacher_id = db.insert_teacher(full_name=full_name, bio=bio, achievements=achievements, image_url=image_url, course_id=course_id)
    # link to course
    db.update_course(course_id, teacher_id=teacher_id)
    bot.send_message(message.chat.id, f"✅ Ustoz qo'shildi: <b>{full_name}</b>", parse_mode="HTML")


# ===== ENROLL FLOW (user name -> contact) =====
def enroll_get_name(message: Message, course_id: int):
    name = message.text.strip()
    if not name:
        bot.send_message(message.chat.id, "❌ Iltimos ismingizni kiriting.")
        bot.register_next_step_handler(message, enroll_get_name, course_id)
        return
    temp_enrolls[message.from_user.id] = {"course_id": course_id, "full_name": name}
    bot.send_message(message.chat.id, "📱 Telefon raqamingizni yuboring:", reply_markup=request_contact_markup())
    bot.register_next_step_handler(message, enroll_get_contact, course_id)


def enroll_get_contact(message: Message, course_id: int):
    # phone could come as contact or text
    phone = None
    if message.contact:
        phone = message.contact.phone_number
    else:
        phone = message.text.strip()
    data = temp_enrolls.pop(message.from_user.id, None)
    if not data:
        bot.send_message(message.chat.id, "❌ Xatolik! Iltimos qayta boshlang.")
        return
    full_name = data["full_name"]
    db.add_student(message.from_user.id, full_name, phone, course_id)
    # After registration send main menu (or show back button)
    bot.send_message(message.chat.id, "✅ Siz muvaffaqiyatli ro'yxatdan o'tdingiz! Tez orada admin siz bilan bog'lanadi.", reply_markup=make_buttons(["🔙 Orqaga"], back=False))
