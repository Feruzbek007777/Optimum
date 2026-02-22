import sqlite3
import os
import time
from config import DATABASE_PATH


# ===================== POINTS FORMAT / ROUND =====================

POINTS_DECIMALS = 1  # nuqtadan keyin 1 ta raqam

def fmt_points(x) -> str:
    """
    UI uchun chiroyli format:
    9.80000000001 -> 9.8
    10.0 -> 10
    """
    try:
        v = round(float(x), POINTS_DECIMALS)
    except Exception:
        v = 0.0
    s = f"{v:.{POINTS_DECIMALS}f}"
    if s.endswith(".0"):
        s = s[:-2]
    return s


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

            # ✅ BONUS CLAIMS
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS bonus_claims (
                    user_id INTEGER PRIMARY KEY,
                    last_claim_ts INTEGER NOT NULL
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

            # 🎬 Kurs videosi ko‘rganlar
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

            # Foydalanuvchilar jadvali
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    full_name TEXT,
                    points REAL DEFAULT 0,
                    referrals_count INTEGER DEFAULT 0,
                    joined_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # 🔥 Yangi ustunlar: points, referrals_count
            # IMPORTANT: points REAL bo'lsin (0.2 / 0.5 uchun)
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN points REAL DEFAULT 0.0")
            except sqlite3.OperationalError:
                pass

            try:
                cursor.execute("ALTER TABLE users ADD COLUMN referrals_count INTEGER DEFAULT 0")
            except sqlite3.OperationalError:
                pass

            # 🔥 Yangi jadval: referrals
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
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM courses ORDER BY name")
    courses = cursor.fetchall()
    conn.close()
    return courses


def get_course_details(course_id):
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
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO course_details (course_id, price, schedule, description, image_path) VALUES (?, ?, ?, ?, ?)",
        (course_id, price, schedule, description, image_path)
    )
    conn.commit()
    conn.close()


def delete_course(course_id):
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT image_path FROM course_details WHERE course_id = ?", (course_id,))
        for (img,) in cursor.fetchall():
            _delete_file_if_exists(img)

        cursor.execute("SELECT image_path FROM teachers WHERE course_id = ?", (course_id,))
        for (img,) in cursor.fetchall():
            _delete_file_if_exists(img)

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
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, full_name, achievements, image_path FROM teachers WHERE course_id = ?", (course_id,))
    teacher_info = cursor.fetchone()
    conn.close()
    return teacher_info


def get_all_teachers():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, course_id, full_name FROM teachers ORDER BY full_name")
    teachers = cursor.fetchall()
    conn.close()
    return teachers


def add_teacher(course_id, full_name, achievements, image_path):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO teachers (course_id, full_name, achievements, image_path) VALUES (?, ?, ?, ?)",
        (course_id, full_name, achievements, image_path)
    )
    conn.commit()
    conn.close()


def delete_teacher(teacher_id):
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
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO students (full_name, phone_number, username, course_id) VALUES (?, ?, ?, ?)",
        (full_name, phone_number, username, course_id)
    )
    conn.commit()
    conn.close()


def approve_student(full_name, phone_number, course_id):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE students SET approved = TRUE WHERE full_name = ? AND phone_number = ? AND course_id = ?",
        (full_name, phone_number, course_id)
    )
    conn.commit()
    conn.close()


def delete_student(full_name, phone_number, course_id):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM students WHERE full_name = ? AND phone_number = ? AND course_id = ?",
        (full_name, phone_number, course_id)
    )
    conn.commit()
    conn.close()


def get_approved_students():
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
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT message, image_path FROM announcements ORDER BY created_at DESC LIMIT 5")
    announcements = cursor.fetchall()
    conn.close()
    return announcements


def add_announcement(message, image_path=None):
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
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT group_id, group_title FROM admin_groups ORDER BY group_title")
    groups = cursor.fetchall()
    conn.close()
    return groups


def delete_admin_group(group_id):
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


# ----------- USER OPERATSIYALARI -----------

def add_user(user_id, username, full_name):
    """
    Foydalanuvchini qo'shish yoki yangilash.
    REPLACE emas, ON CONFLICT UPDATE (points yo'qolmasin)
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
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()
    conn.close()
    return [u[0] for u in users]


def get_user_stats(user_id):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT user_id, username, full_name, joined_at,
               ROUND(COALESCE(points, 0), 1), COALESCE(referrals_count, 0)
        FROM users
        WHERE user_id = ?
    ''', (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row


# ----------- BALLAR VA TAKLIFLAR (POINTS / REFERRALS) -----------

def add_points(user_id: int, amount):
    """
    Foydalanuvchiga ball qo'shish (+ yoki - bo'lishi mumkin).
    DBda doim 1 xonagacha ROUND qilib saqlaydi.
    """
    try:
        amount = float(amount)
    except Exception:
        amount = 0.0

    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE users
        SET points = ROUND(COALESCE(points, 0) + ?, 1)
        WHERE user_id = ?
    ''', (amount, user_id))
    conn.commit()
    conn.close()


def get_points(user_id: int) -> float:
    """Foydalanuvchining ballarini olish (1 xonagacha)."""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COALESCE(points, 0) FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    try:
        return round(float(row[0] if row else 0.0), 1)
    except Exception:
        return 0.0


def set_points(user_id: int, value):
    """Foydalanuvchining ballini to'g'ridan-to'g'ri o'rnatish (1 xonagacha)."""
    try:
        value = float(value)
    except Exception:
        value = 0.0

    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE users
        SET points = ROUND(?, 1)
        WHERE user_id = ?
    ''', (value, user_id))
    conn.commit()
    conn.close()


def increment_referrals(user_id: int):
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
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COALESCE(referrals_count, 0) FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0


def add_referral(referrer_id: int, referred_id: int, bonus_points: int = 200) -> bool:
    """
    Taklif yozuvi qo'shish (referred_id UNIQUE).
    referrerga ball + referrals_count qo'shadi.
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

        # ✅ points ROUND bilan

        # referrer users jadvalida bo'lmasa, row yaratib qo'yamiz (points yo'qolmasin)
        cursor.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (referrer_id,))

        # ✅ points ROUND bilan
        cursor.execute('''
            UPDATE users
            SET
                points = ROUND(COALESCE(points, 0) + ?, 1),
                referrals_count = COALESCE(referrals_count, 0) + 1
            WHERE user_id = ?
        ''', (float(bonus_points), referrer_id))

        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def get_referrals_for_user(referrer_id: int):
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
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT user_id, username, full_name,
               ROUND(COALESCE(points, 0), 1) AS pts,
               COALESCE(referrals_count, 0) AS refs
        FROM users
        ORDER BY pts DESC, refs DESC, joined_at ASC
        LIMIT ?
    ''', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_all_users_with_stats():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT user_id, username, full_name, joined_at,
               ROUND(COALESCE(points, 0), 1) AS pts,
               COALESCE(referrals_count, 0) AS refs
        FROM users
        ORDER BY pts DESC, joined_at ASC
    ''')
    rows = cursor.fetchall()
    conn.close()
    return rows


# ----------- GIFT LIKE OPERATSIYALARI -----------

def add_gift_like(user_id: int):
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT 1 FROM gift_likes WHERE user_id = ?", (user_id,))
        already = cursor.fetchone() is not None

        if not already:
            cursor.execute("INSERT INTO gift_likes (user_id) VALUES (?)", (user_id,))
            conn.commit()

        cursor.execute("SELECT COUNT(*) FROM gift_likes")
        total = cursor.fetchone()[0]
        return (not already), total
    except sqlite3.Error as e:
        print(f"gift_likes xatosi: {e}")
        return False, 0
    finally:
        conn.close()


def get_gift_likes_count() -> int:
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
    if not username:
        return None

    username = username.lstrip("@")

    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT user_id,
               username,
               full_name,
               joined_at,
               ROUND(COALESCE(points, 0), 1) AS pts,
               COALESCE(referrals_count, 0) AS refs
        FROM users
        WHERE LOWER(username) = LOWER(?)
        LIMIT 1
    ''', (username,))
    row = cursor.fetchone()
    conn.close()
    return row


# ===================== BONUS (6 soat) =====================

BONUS_COOLDOWN_SECONDS = 6 * 60 * 60  # 6 soat


def _format_hms(seconds: int) -> str:
    if seconds < 0:
        seconds = 0
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


def claim_bonus_atomic(user_id: int, amount: int, cooldown_seconds: int = BONUS_COOLDOWN_SECONDS):
    """
    Atomik bonus claim:
    - cooldown tekshiradi
    - ruxsat bo'lsa: amount ni users.points ga qo'shadi (ROUND 1),
      last_claim_ts ni yangilaydi
    """
    now = int(time.time())

    try:
        amount = float(amount)
    except Exception:
        amount = 0.0
    if amount < 0:
        amount = 0.0

    conn = create_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("BEGIN IMMEDIATE")

        cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))

        cursor.execute("SELECT last_claim_ts FROM bonus_claims WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()

        if row and row[0] is not None:
            last_ts = int(row[0])
            passed = now - last_ts
            if passed < cooldown_seconds:
                wait = cooldown_seconds - passed
                conn.commit()
                return False, 0, wait, _format_hms(wait)

        # ✅ points ROUND bilan
        cursor.execute("""
            UPDATE users
            SET points = ROUND(COALESCE(points, 0) + ?, 1)
            WHERE user_id = ?
        """, (amount, user_id))

        cursor.execute("""
            INSERT INTO bonus_claims (user_id, last_claim_ts)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                last_claim_ts = excluded.last_claim_ts
        """, (user_id, now))

        conn.commit()
        return True, amount, 0, "00:00:00"

    except sqlite3.Error as e:
        try:
            conn.rollback()
        except Exception:
            pass
        print(f"claim_bonus_atomic xatosi: {e}")
        return False, 0, 60, _format_hms(60)

    finally:
        conn.close()


if __name__ == "__main__":
    init_database()
