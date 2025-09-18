from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.database import Database

db = Database()

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.database import Database

db = Database()

def courses_inline(prefix: str = "course"):
    markup = InlineKeyboardMarkup()
    courses = db.get_courses()
    if not courses:
        return markup

    for course_id, name in courses:
        markup.add(
            InlineKeyboardButton(
                text=name,
                callback_data=f"{prefix}_{course_id}"  # 🔑 prefix bilan
            )
        )
    return markup



def course_detail_inline(course_id: int):
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("👨‍🏫 Ustoz haqida", callback_data=f"teacher_{course_id}"),
        InlineKeyboardButton("📝 Kursga yozilish", callback_data=f"enroll_{course_id}"),
        InlineKeyboardButton("🔙 Orqaga", callback_data="back_courses")
    )
    return markup

def teachers_inline_for_course(course_id: int):
    markup = InlineKeyboardMarkup(row_width=1)
    teachers = db.get_teachers_by_course(course_id)
    if teachers:
        for teacher_id, name in teachers:
            markup.add(InlineKeyboardButton(name, callback_data=f"teacherid_{teacher_id}"))
    markup.add(InlineKeyboardButton("🔙 Orqaga", callback_data="back_course_teachers"))
    return markup
