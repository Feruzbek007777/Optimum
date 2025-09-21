from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.database import get_courses, get_all_teachers, get_all_admin_groups


def generate_courses_keyboard(action) :
    courses = get_courses()

    keyboard = InlineKeyboardMarkup(row_width=2)
    buttons = []
    for course_id, course_name in courses :
        buttons.append(InlineKeyboardButton(course_name, callback_data=f"{action}_{course_id}"))

    for i in range(0, len(buttons), 2) :
        if i + 1 < len(buttons) :
            keyboard.add(buttons[i], buttons[i + 1])
        else :
            keyboard.add(buttons[i])

    return keyboard


def generate_teachers_keyboard() :
    teachers = get_all_teachers()

    keyboard = InlineKeyboardMarkup()
    for teacher_id, course_id, full_name in teachers :
        keyboard.add(InlineKeyboardButton(full_name, callback_data=f"teacher_{teacher_id}"))

    return keyboard


def generate_teachers_delete_keyboard() :
    teachers = get_all_teachers()

    keyboard = InlineKeyboardMarkup()
    for teacher_id, course_id, full_name in teachers :
        keyboard.add(InlineKeyboardButton(f"❌ {full_name}", callback_data=f"delete_teacher_{teacher_id}"))

    return keyboard


def generate_courses_delete_keyboard() :
    courses = get_courses()

    keyboard = InlineKeyboardMarkup()
    for course_id, course_name in courses :
        keyboard.add(InlineKeyboardButton(f"❌ {course_name}", callback_data=f"delete_course_{course_id}"))

    return keyboard


def generate_groups_keyboard(action) :
    groups = get_all_admin_groups()

    keyboard = InlineKeyboardMarkup()
    for group_id, group_title in groups :
        keyboard.add(InlineKeyboardButton(group_title, callback_data=f"{action}_{group_id}"))

    # Barcha guruhlarga yuborish tugmasi
    if groups :
        keyboard.add(InlineKeyboardButton("📢 BARCHA GURUHGA YUBORISH", callback_data=f"{action}_all"))

    return keyboard


def back_button() :
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🔙 Orqaga", callback_data="back"))
    return keyboard