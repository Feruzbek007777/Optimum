import sqlite3
import os
from config import DATABASE_PATH


def create_connection() :
    """Ma'lumotlar bazasiga ulanish yaratish"""
    conn = None
    try :
        conn = sqlite3.connect(DATABASE_PATH)
        return conn
    except sqlite3.Error as e :
        print(f"Xatolik: {e}")
    return conn


def init_database() :
    """Ma'lumotlar bazasini ishga tushirish"""
    conn = create_connection()
    if conn is not None :
        try :
            cursor = conn.cursor()

            # Kurslar jadvali
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS courses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE
                )
            ''')

            # Kurs ma'lumotlari jadvali
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS course_details (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    course_id INTEGER NOT NULL,
                    price TEXT,
                    schedule TEXT,
                    description TEXT,
                    image_path TEXT,
                    FOREIGN KEY (course_id) REFERENCES courses (id)
                )
            ''')

            # O'qituvchilar jadvali
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS teachers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    course_id INTEGER NOT NULL,
                    full_name TEXT NOT NULL,
                    achievements TEXT,
                    image_path TEXT,
                    FOREIGN KEY (course_id) REFERENCES courses (id)
                )
            ''')

            # Talabalar jadvali
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS students (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    full_name TEXT NOT NULL,
                    phone_number TEXT NOT NULL,
                    username TEXT,
                    course_id INTEGER,
                    registered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    approved BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (course_id) REFERENCES courses (id)
                )
            ''')

            # E'lonlar jadvali
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS announcements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message TEXT NOT NULL,
                    image_path TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Admin guruhlari jadvali
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS admin_groups (
                    group_id INTEGER PRIMARY KEY,
                    group_title TEXT NOT NULL,
                    added_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            conn.commit()
            print("✅ Ma'lumotlar bazasi muvaffaqiyatli yaratildi!")
        except sqlite3.Error as e :
            print(f"Xatolik: {e}")
        finally :
            conn.close()
    else :
        print("❌ Ma'lumotlar bazasiga ulanib bo'lmadi!")


# ----------- KURS OPERATSIYALARI -----------
def get_courses() :
    """Barcha kurslarni olish"""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM courses ORDER BY name")
    courses = cursor.fetchall()
    conn.close()
    return courses


def get_course_details(course_id) :
    """Kurs ma'lumotlarini olish"""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT cd.price, cd.schedule, cd.description, cd.image_path, c.name 
        FROM course_details cd 
        JOIN courses c ON cd.course_id = c.id 
        WHERE cd.course_id = ?
    ''', (course_id,))
    course_info = cursor.fetchone()
    conn.close()
    return course_info


def add_course(name) :
    """Yangi kurs qo'shish"""
    conn = create_connection()
    cursor = conn.cursor()
    try :
        cursor.execute("INSERT INTO courses (name) VALUES (?)", (name,))
        conn.commit()
        return True
    except sqlite3.IntegrityError :
        return False
    finally :
        conn.close()


def add_course_details(course_id, price, schedule, description, image_path) :
    """Kurs ma'lumotlarini qo'shish"""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO course_details (course_id, price, schedule, description, image_path) VALUES (?, ?, ?, ?, ?)",
        (course_id, price, schedule, description, image_path)
    )
    conn.commit()
    conn.close()


def delete_course(course_id) :
    """Kursni o'chirish"""
    conn = create_connection()
    cursor = conn.cursor()
    try :
        # Avval bog'liq ma'lumotlarni o'chiramiz
        cursor.execute("DELETE FROM course_details WHERE course_id = ?", (course_id,))
        cursor.execute("DELETE FROM teachers WHERE course_id = ?", (course_id,))
        cursor.execute("DELETE FROM students WHERE course_id = ?", (course_id,))
        cursor.execute("DELETE FROM courses WHERE id = ?", (course_id,))
        conn.commit()
        return True
    except sqlite3.Error :
        return False
    finally :
        conn.close()


# ----------- O'QITUVCHI OPERATSIYALARI -----------
def get_teacher(course_id) :
    """Kurs o'qituvchisini olish"""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, full_name, achievements, image_path FROM teachers WHERE course_id = ?", (course_id,))
    teacher_info = cursor.fetchone()
    conn.close()
    return teacher_info


def get_all_teachers() :
    """Barcha o'qituvchilarni olish"""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, course_id, full_name FROM teachers ORDER BY full_name")
    teachers = cursor.fetchall()
    conn.close()
    return teachers


def add_teacher(course_id, full_name, achievements, image_path) :
    """Yangi o'qituvchi qo'shish"""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO teachers (course_id, full_name, achievements, image_path) VALUES (?, ?, ?, ?)",
        (course_id, full_name, achievements, image_path)
    )
    conn.commit()
    conn.close()


def delete_teacher(teacher_id) :
    """O'qituvchini o'chirish"""
    conn = create_connection()
    cursor = conn.cursor()
    try :
        cursor.execute("DELETE FROM teachers WHERE id = ?", (teacher_id,))
        conn.commit()
        return True
    except sqlite3.Error :
        return False
    finally :
        conn.close()


# ----------- TALABA OPERATSIYALARI -----------
def add_student(full_name, phone_number, username, course_id) :
    """Talaba qo'shish"""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO students (full_name, phone_number, username, course_id) VALUES (?, ?, ?, ?)",
        (full_name, phone_number, username, course_id)
    )
    conn.commit()
    conn.close()


def approve_student(full_name, phone_number, course_id) :
    """Talabani tasdiqlash"""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE students SET approved = TRUE WHERE full_name = ? AND phone_number = ? AND course_id = ?",
        (full_name, phone_number, course_id)
    )
    conn.commit()
    conn.close()


def delete_student(full_name, phone_number, course_id) :
    """Talabani o'chirish"""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM students WHERE full_name = ? AND phone_number = ? AND course_id = ?",
        (full_name, phone_number, course_id)
    )
    conn.commit()
    conn.close()


def get_approved_students() :
    """Tasdiqlangan talabalarni olish"""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT s.id, s.full_name, s.phone_number, s.username, s.registered_at, c.name 
        FROM students s 
        LEFT JOIN courses c ON s.course_id = c.id 
        WHERE s.approved = TRUE
    ''')
    students = cursor.fetchall()
    conn.close()
    return students


# ----------- E'LON OPERATSIYALARI -----------
def get_announcements() :
    """E'lonlarni olish"""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT message, image_path FROM announcements ORDER BY created_at DESC LIMIT 5")
    announcements = cursor.fetchall()
    conn.close()
    return announcements


def add_announcement(message, image_path=None) :
    """Yangi e'lon qo'shish"""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO announcements (message, image_path) VALUES (?, ?)",
        (message, image_path)
    )
    conn.commit()
    conn.close()


# ----------- GURUH OPERATSIYALARI -----------
def add_admin_group(group_id, group_title) :
    """Yangi admin guruhini qo'shish"""
    conn = create_connection()
    cursor = conn.cursor()
    try :
        cursor.execute(
            "INSERT OR REPLACE INTO admin_groups (group_id, group_title) VALUES (?, ?)",
            (group_id, group_title)
        )
        conn.commit()
        return True
    except sqlite3.Error as e :
        print(f"Guruh qo'shishda xatolik: {e}")
        return False
    finally :
        conn.close()


def get_all_admin_groups() :
    """Barcha admin guruhlarini olish"""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT group_id, group_title FROM admin_groups ORDER BY group_title")
    groups = cursor.fetchall()
    conn.close()
    return groups


def delete_admin_group(group_id) :
    """Admin guruhini o'chirish"""
    conn = create_connection()
    cursor = conn.cursor()
    try :
        cursor.execute("DELETE FROM admin_groups WHERE group_id = ?", (group_id,))
        conn.commit()
        return True
    except sqlite3.Error as e :
        print(f"Guruh o'chirishda xatolik: {e}")
        return False
    finally :
        conn.close()


if __name__ == "__main__" :
    init_database()