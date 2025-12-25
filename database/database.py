import sqlite3
import os
from config import DATABASE_PATH


def create_connection():
    """Ma'lumotlar bazasiga ulanish yaratish"""
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        return conn
    except sqlite3.Error as e:
        print(f"Xatolik: {e}")
    return conn


def init_database():
    """Ma'lumotlar bazasini ishga tushirish"""
    conn = create_connection()
    if conn is not None:
        try:
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

            # 🎬 Kurs videosi ko‘rganlar (unique userlar)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS course_video_views (
                    user_id INTEGER PRIMARY KEY,
                    viewed_at DATETIME DEFAULT CURRENT_TIMESTAMP
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

            # Foydalanuvchilar jadvali (asosiy)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    full_name TEXT,
                    joined_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # 🔥 Yangi ustunlar: points, referrals_count
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN points INTEGER DEFAULT 0")
            except sqlite3.OperationalError:
                # allaqachon mavjud bo'lsa xato beradi — e'tibor bermaymiz
                pass

            try:
                cursor.execute("ALTER TABLE users ADD COLUMN referrals_count INTEGER DEFAULT 0")
            except sqlite3.OperationalError:
                pass

            # 🔥 Yangi jadval: referrals (takliflar logi)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS referrals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    referrer_id INTEGER NOT NULL,
                    referred_id INTEGER NOT NULL UNIQUE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (referrer_id) REFERENCES users (user_id),
                    FOREIGN KEY (referred_id) REFERENCES users (user_id)
                )
            ''')

            cursor.execute('''
                           CREATE TABLE IF NOT EXISTS gift_likes (
                               user_id INTEGER PRIMARY KEY,
                               liked_at DATETIME DEFAULT CURRENT_TIMESTAMP
                           )
                       ''')

            conn.commit()
            print("✅ Ma'lumotlar bazasi muvaffaqiyatli yaratildi!")
        except sqlite3.Error as e:
            print(f"Xatolik: {e}")
        finally:
            conn.close()
    else:
        print("❌ Ma'lumotlar bazasiga ulanib bo'lmadi!")


# ----------- YORDAMCHI: rasmlarni o'chirish -----------

def _delete_file_if_exists(path: str):
    if path and os.path.exists(path):
        try:
            os.remove(path)
        except OSError as e:
            print(f"Rasmni o'chirishda xatolik ({path}): {e}")


# ----------- KURS OPERATSIYALARI -----------

def get_courses():
    """Barcha kurslarni olish"""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM courses ORDER BY name")
    courses = cursor.fetchall()
    conn.close()
    return courses


def get_course_details(course_id):
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


def add_course(name):
    """Yangi kurs qo'shish"""
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO courses (name) VALUES (?)", (name,))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def add_course_details(course_id, price, schedule, description, image_path):
    """Kurs ma'lumotlarini qo'shish"""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO course_details (course_id, price, schedule, description, image_path) VALUES (?, ?, ?, ?, ?)",
        (course_id, price, schedule, description, image_path)
    )
    conn.commit()
    conn.close()


def delete_course(course_id):
    """Kursni o'chirish (rasmlar bilan birga)"""
    conn = create_connection()
    cursor = conn.cursor()
    try:
        # Avval course_details rasmlarini o'chiramiz
        cursor.execute("SELECT image_path FROM course_details WHERE course_id = ?", (course_id,))
        for (img,) in cursor.fetchall():
            _delete_file_if_exists(img)

        # Ustozlar rasmlarini o'chiramiz
        cursor.execute("SELECT image_path FROM teachers WHERE course_id = ?", (course_id,))
        for (img,) in cursor.fetchall():
            _delete_file_if_exists(img)

        # Bog'liq ma'lumotlarni o'chiramiz
        cursor.execute("DELETE FROM course_details WHERE course_id = ?", (course_id,))
        cursor.execute("DELETE FROM teachers WHERE course_id = ?", (course_id,))
        cursor.execute("DELETE FROM students WHERE course_id = ?", (course_id,))
        cursor.execute("DELETE FROM courses WHERE id = ?", (course_id,))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Kursni o'chirishda xatolik: {e}")
        return False
    finally:
        conn.close()


# ----------- O'QITUVCHI OPERATSIYALARI -----------

def get_teacher(course_id):
    """Kurs o'qituvchisini olish"""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, full_name, achievements, image_path FROM teachers WHERE course_id = ?", (course_id,))
    teacher_info = cursor.fetchone()
    conn.close()
    return teacher_info


def get_all_teachers():
    """Barcha o'qituvchilarni olish"""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, course_id, full_name FROM teachers ORDER BY full_name")
    teachers = cursor.fetchall()
    conn.close()
    return teachers


def add_teacher(course_id, full_name, achievements, image_path):
    """Yangi o'qituvchi qo'shish"""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO teachers (course_id, full_name, achievements, image_path) VALUES (?, ?, ?, ?)",
        (course_id, full_name, achievements, image_path)
    )
    conn.commit()
    conn.close()


def delete_teacher(teacher_id):
    """O'qituvchini o'chirish (rasmi bilan)"""
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT image_path FROM teachers WHERE id = ?", (teacher_id,))
        row = cursor.fetchone()
        if row:
            _delete_file_if_exists(row[0])

        cursor.execute("DELETE FROM teachers WHERE id = ?", (teacher_id,))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"O'qituvchini o'chirishda xatolik: {e}")
        return False
    finally:
        conn.close()


# ----------- TALABA OPERATSIYALARI -----------

def add_student(full_name, phone_number, username, course_id):
    """Talaba qo'shish"""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO students (full_name, phone_number, username, course_id) VALUES (?, ?, ?, ?)",
        (full_name, phone_number, username, course_id)
    )
    conn.commit()
    conn.close()


def approve_student(full_name, phone_number, course_id):
    """Talabani tasdiqlash"""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE students SET approved = TRUE WHERE full_name = ? AND phone_number = ? AND course_id = ?",
        (full_name, phone_number, course_id)
    )
    conn.commit()
    conn.close()


def delete_student(full_name, phone_number, course_id):
    """Talabani o'chirish"""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM students WHERE full_name = ? AND phone_number = ? AND course_id = ?",
        (full_name, phone_number, course_id)
    )
    conn.commit()
    conn.close()


def get_approved_students():
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

def get_announcements():
    """E'lonlarni olish"""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT message, image_path FROM announcements ORDER BY created_at DESC LIMIT 5")
    announcements = cursor.fetchall()
    conn.close()
    return announcements


def add_announcement(message, image_path=None):
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

def add_admin_group(group_id, group_title):
    """Yangi admin guruhini qo'shish"""
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT OR REPLACE INTO admin_groups (group_id, group_title) VALUES (?, ?)",
            (group_id, group_title)
        )
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Guruh qo'shishda xatolik: {e}")
        return False
    finally:
        conn.close()


def get_all_admin_groups():
    """Barcha admin guruhlarini olish"""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT group_id, group_title FROM admin_groups ORDER BY group_title")
    groups = cursor.fetchall()
    conn.close()
    return groups


def delete_admin_group(group_id):
    """Admin guruhini o'chirish"""
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM admin_groups WHERE group_id = ?", (group_id,))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Guruh o'chirishda xatolik: {e}")
        return False
    finally:
        conn.close()


# ----------- USER OPERATSIYALARI (FOYDALANUVCHI) -----------

def add_user(user_id, username, full_name):
    """
    Foydalanuvchini qo'shish yoki yangilash.
    Muhim: points/referrals_count qayta nol bo'lib ketmasligi uchun
    REPLACE emas, ON CONFLICT UPDATE ishlatamiz.
    """
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO users (user_id, username, full_name)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            username = excluded.username,
            full_name = excluded.full_name
    ''', (user_id, username, full_name))
    conn.commit()
    conn.close()


def get_all_users():
    """Barcha foydalanuvchilarning faqat user_id ro'yxati"""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()
    conn.close()
    return [u[0] for u in users]


def get_user_stats(user_id):
    """Bitta foydalanuvchi haqida to'liq statistika"""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT user_id, username, full_name, joined_at, 
               COALESCE(points, 0), COALESCE(referrals_count, 0)
        FROM users
        WHERE user_id = ?
    ''', (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row  # (user_id, username, full_name, joined_at, points, referrals_count)


# ----------- BALLAR VA TAKLIFLAR (POINTS / REFERRALS) -----------

def add_points(user_id: int, amount: int):
    """Foydalanuvchiga ball qo'shish (+ yoki - bo'lishi mumkin)"""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE users
        SET points = COALESCE(points, 0) + ?
        WHERE user_id = ?
    ''', (amount, user_id))
    conn.commit()
    conn.close()


def get_points(user_id: int) -> int:
    """Foydalanuvchining ballarini olish"""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COALESCE(points, 0) FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0


def set_points(user_id: int, value: int):
    """Foydalanuvchining ballini to'g'ridan-to'g'ri o'rnatish"""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE users
        SET points = ?
        WHERE user_id = ?
    ''', (value, user_id))
    conn.commit()
    conn.close()


def increment_referrals(user_id: int):
    """Foydalanuvchining takliflar sonini +1 qilish"""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE users
        SET referrals_count = COALESCE(referrals_count, 0) + 1
        WHERE user_id = ?
    ''', (user_id,))
    conn.commit()
    conn.close()


def get_referrals_count(user_id: int) -> int:
    """Foydalanuvchining takliflar sonini olish"""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COALESCE(referrals_count, 0) FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0


def add_referral(referrer_id: int, referred_id: int, bonus_points: int = 200) -> bool:
    """
    Taklif yozuvi qo'shish.
    - referrer_id: kim taklif qildi
    - referred_id: kim taklif bilan keldi
    Bir userni faqat bir marta hisoblaymiz (referred_id UNIQUE).
    """
    if referrer_id == referred_id:
        return False

    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO referrals (referrer_id, referred_id)
            VALUES (?, ?)
        ''', (referrer_id, referred_id))
        # Agar muvaffaqiyatli bo'lsa — referrerga ball va takliflar sonini oshiramiz
        cursor.execute('''
            UPDATE users
            SET 
                points = COALESCE(points, 0) + ?,
                referrals_count = COALESCE(referrals_count, 0) + 1
            WHERE user_id = ?
        ''', (bonus_points, referrer_id))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # Bu referred_id allaqachon ro'yxatda bor (ikki marta sanamaymiz)
        return False
    finally:
        conn.close()


def get_referrals_for_user(referrer_id: int):
    """Berilgan foydalanuvchi taklif qilgan odamlar ro'yxati"""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT u.user_id, u.username, u.full_name, r.created_at
        FROM referrals r
        JOIN users u ON u.user_id = r.referred_id
        WHERE r.referrer_id = ?
        ORDER BY r.created_at DESC
    ''', (referrer_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_top_users(limit: int = 10):
    """Top foydalanuvchilar ro'yxati (ball bo'yicha)"""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute(f'''
        SELECT user_id, username, full_name,
               COALESCE(points, 0) AS pts,
               COALESCE(referrals_count, 0) AS refs
        FROM users
        ORDER BY pts DESC, refs DESC, joined_at ASC
        LIMIT ?
    ''', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return rows  # (user_id, username, full_name, points, referrals_count)


def get_all_users_with_stats():
    """Admin panel uchun: barcha userlar stats bilan, ball bo'yicha tartiblangan"""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT user_id, username, full_name, joined_at,
               COALESCE(points, 0) AS pts,
               COALESCE(referrals_count, 0) AS refs
        FROM users
        ORDER BY pts DESC, joined_at ASC
    ''')
    rows = cursor.fetchall()
    conn.close()
    return rows

# ----------- GIFT LIKE OPERATSIYALARI -----------

def add_gift_like(user_id: int):
    """
    Sovg'a bo'limi uchun like qo'shish.
    return: (new_like: bool, total_likes: int)
    """
    conn = create_connection()
    cursor = conn.cursor()
    try:
        # Avval user allaqachon like bosgan-bosmaganini tekshiramiz
        cursor.execute("SELECT 1 FROM gift_likes WHERE user_id = ?", (user_id,))
        already = cursor.fetchone() is not None

        if not already:
            cursor.execute("INSERT INTO gift_likes (user_id) VALUES (?)", (user_id,))
            conn.commit()

        # Jami likelar soni
        cursor.execute("SELECT COUNT(*) FROM gift_likes")
        total = cursor.fetchone()[0]

        return (not already), total
    except sqlite3.Error as e:
        print(f"gift_likes xatosi: {e}")
        return False, 0
    finally:
        conn.close()


def get_gift_likes_count() -> int:
    """Sovg'a bo'limi uchun jami likelar soni"""
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM gift_likes")
        row = cursor.fetchone()
        return row[0] if row else 0
    except sqlite3.Error as e:
        print(f"gift_likes count xatosi: {e}")
        return 0
    finally:
        conn.close()

def get_user_by_username(username: str):
    """
    Username bo'yicha foydalanuvchini topish.
    return:
      (user_id, username, full_name, joined_at, points, referrals_count) yoki None
    """
    if not username:
        return None

    # @ belgisini olib tashlaymiz, agar bo'lsa
    username = username.lstrip("@")

    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT user_id,
               username,
               full_name,
               joined_at,
               COALESCE(points, 0) AS pts,
               COALESCE(referrals_count, 0) AS refs
        FROM users
        WHERE LOWER(username) = LOWER(?)
        LIMIT 1
    ''', (username,))
    row = cursor.fetchone()
    conn.close()
    return row

def add_course_video_view(user_id: int) -> bool:
    """
    /video bosgan userni 1 marta hisoblash (unique).
    return: True bo‘lsa yangi qo‘shildi, False bo‘lsa oldin ham ko‘rgan.
    """
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT 1 FROM course_video_views WHERE user_id = ?", (user_id,))
        already = cursor.fetchone() is not None

        if not already:
            cursor.execute("INSERT INTO course_video_views (user_id) VALUES (?)", (user_id,))
            conn.commit()
            return True
        return False
    except sqlite3.Error as e:
        print(f"course_video_views xatosi: {e}")
        return False
    finally:
        conn.close()


def get_course_video_views_count() -> int:
    """/video ko‘rgan unique userlar soni"""
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM course_video_views")
        row = cursor.fetchone()
        return row[0] if row else 0
    except sqlite3.Error as e:
        print(f"course_video_views count xatosi: {e}")
        return 0
    finally:
        conn.close()




if __name__ == "__main__":
    init_database()
