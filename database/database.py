# database/database.py
import sqlite3
from typing import Optional, List, Tuple, Any


class Database:
    def __init__(self, db_name: str = "main.db"):
        self.database = db_name

    # Universal execute helper
    def execute(self, sql: str, *args,
                commit: bool = False,
                fetchone: bool = False,
                fetchall: bool = False) -> Optional[Any]:
        with sqlite3.connect(self.database) as db:
            cur = db.cursor()
            cur.execute(sql, args)
            res = None
            if fetchone:
                res = cur.fetchone()
            elif fetchall:
                res = cur.fetchall()
            if commit:
                db.commit()
        return res

    # ---------- USERS ----------
    def create_table_users(self):
        sql = '''CREATE TABLE IF NOT EXISTS users(
            telegram_id INTEGER NOT NULL UNIQUE,
            full_name TEXT,
            phone_number VARCHAR(13),
            lang VARCHAR(3)
        )'''
        self.execute(sql, commit=True)

    def insert_telegram_id(self, telegram_id: int):
        sql = "INSERT OR IGNORE INTO users(telegram_id) VALUES (?)"
        self.execute(sql, telegram_id, commit=True)

    def update_lang(self, lang: str, telegram_id: int):
        sql = "UPDATE users SET lang = ? WHERE telegram_id = ?"
        self.execute(sql, lang, telegram_id, commit=True)

    def get_user(self, telegram_id: int):
        sql = "SELECT * FROM users WHERE telegram_id = ?"
        return self.execute(sql, telegram_id, fetchone=True)

    def save_phone_number_and_full_name(self, full_name: str, phone_number: str, telegram_id: int):
        sql = "UPDATE users SET full_name = ?, phone_number = ? WHERE telegram_id = ?"
        self.execute(sql, full_name, phone_number, telegram_id, commit=True)

    # ---------- COURSES ----------
    def create_table_courses(self):
        sql = """CREATE TABLE IF NOT EXISTS courses(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            description TEXT,
            price TEXT,
            schedule TEXT,
            image_url TEXT,
            teacher_id INTEGER
        )"""
        self.execute(sql, commit=True)

    def insert_course(self, name: str) -> Optional[int]:
        # need lastrowid, so use manual connection
        with sqlite3.connect(self.database) as db:
            cur = db.cursor()
            cur.execute("INSERT OR IGNORE INTO courses(name) VALUES (?)", (name,))
            db.commit()
            if cur.lastrowid:
                return cur.lastrowid
            cur.execute("SELECT id FROM courses WHERE name = ?", (name,))
            row = cur.fetchone()
            return row[0] if row else None

    def update_course(self, course_id: int,
                      name: str = None,
                      description: str = None,
                      price: str = None,
                      schedule: str = None,
                      image_url: str = None,
                      teacher_id: int = None):
        fields, params = [], []
        if name is not None:
            fields.append("name = ?"); params.append(name)
        if description is not None:
            fields.append("description = ?"); params.append(description)
        if price is not None:
            fields.append("price = ?"); params.append(price)
        if schedule is not None:
            fields.append("schedule = ?"); params.append(schedule)
        if image_url is not None:
            fields.append("image_url = ?"); params.append(image_url)
        if teacher_id is not None:
            fields.append("teacher_id = ?"); params.append(teacher_id)

        if not fields:
            return
        params.append(course_id)
        sql = f"UPDATE courses SET {', '.join(fields)} WHERE id = ?"
        self.execute(sql, *params, commit=True)

    def delete_course(self, course_id: int):
        sql = "DELETE FROM courses WHERE id = ?"
        self.execute(sql, course_id, commit=True)

    def get_courses(self) -> List[Tuple[int, str]]:
        sql = "SELECT id, name FROM courses ORDER BY id"
        rows = self.execute(sql, fetchall=True)
        return rows or []

    def get_course_by_id(self, course_id: int):
        sql = "SELECT id, name, description, price, schedule, image_url, teacher_id FROM courses WHERE id = ?"
        return self.execute(sql, course_id, fetchone=True)

    # add_course_info helper (update subset)
    def add_course_info(self, course_id: int,
                        description: str = None,
                        price: str = None,
                        schedule: str = None):
        fields, params = [], []
        if description is not None:
            fields.append("description = ?"); params.append(description)
        if price is not None:
            fields.append("price = ?"); params.append(price)
        if schedule is not None:
            fields.append("schedule = ?"); params.append(schedule)

        if not fields:
            return
        params.append(course_id)
        sql = f"UPDATE courses SET {', '.join(fields)} WHERE id = ?"
        self.execute(sql, *params, commit=True)

    # ---------- TEACHERS ----------
    def create_table_teachers(self):
        sql = """CREATE TABLE IF NOT EXISTS teachers(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT,
            bio TEXT,
            achievements TEXT,
            image_url TEXT,
            course_id INTEGER
        )"""
        self.execute(sql, commit=True)

    def insert_teacher(self, full_name: str, bio: str, achievements: str, image_url: str, course_id: int) -> int:
        with sqlite3.connect(self.database) as db:
            cur = db.cursor()
            cur.execute(
                "INSERT INTO teachers(full_name, bio, achievements, image_url, course_id) VALUES (?, ?, ?, ?, ?)",
                (full_name, bio, achievements, image_url, course_id)
            )
            db.commit()
            return cur.lastrowid

    def update_teacher(self, teacher_id: int,
                       full_name: str = None,
                       bio: str = None,
                       achievements: str = None,
                       image_url: str = None,
                       course_id: int = None):
        fields, params = [], []
        if full_name is not None:
            fields.append("full_name = ?"); params.append(full_name)
        if bio is not None:
            fields.append("bio = ?"); params.append(bio)
        if achievements is not None:
            fields.append("achievements = ?"); params.append(achievements)
        if image_url is not None:
            fields.append("image_url = ?"); params.append(image_url)
        if course_id is not None:
            fields.append("course_id = ?"); params.append(course_id)

        if not fields:
            return
        params.append(teacher_id)
        sql = f"UPDATE teachers SET {', '.join(fields)} WHERE id = ?"
        self.execute(sql, *params, commit=True)

    def get_teacher_by_id(self, teacher_id: int):
        sql = "SELECT id, full_name, bio, achievements, image_url, course_id FROM teachers WHERE id = ?"
        return self.execute(sql, teacher_id, fetchone=True)

    def get_teachers_by_course(self, course_id: int):
        sql = "SELECT id, full_name FROM teachers WHERE course_id = ?"
        rows = self.execute(sql, course_id, fetchall=True)
        return rows or []

    # ---------- STUDENTS ----------
    def create_table_students(self):
        sql = """CREATE TABLE IF NOT EXISTS students(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            full_name TEXT,
            phone TEXT,
            course_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )"""
        self.execute(sql, commit=True)

    def add_student(self, user_id: int, full_name: str, phone: str, course_id: int):
        sql = "INSERT INTO students(user_id, full_name, phone, course_id) VALUES (?, ?, ?, ?)"
        self.execute(sql, user_id, full_name, phone, course_id, commit=True)

    def get_all_students(self):
        sql = """SELECT s.id, s.full_name, s.phone, c.name as course_name, s.created_at
                 FROM students s
                 LEFT JOIN courses c ON s.course_id = c.id
                 ORDER BY s.created_at DESC"""
        rows = self.execute(sql, fetchall=True)
        return rows or []

    # ---------- GROUPS ----------
    def create_table_groups(self):
        sql = """CREATE TABLE IF NOT EXISTS groups(
            chat_id INTEGER PRIMARY KEY,
            title TEXT,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )"""
        self.execute(sql, commit=True)

    def add_group(self, chat_id: int, title: str = None):
        sql = "INSERT OR REPLACE INTO groups(chat_id, title) VALUES (?, ?)"
        self.execute(sql, chat_id, title, commit=True)

    def get_groups(self):
        sql = "SELECT chat_id FROM groups"
        rows = self.execute(sql, fetchall=True)
        return [r[0] for r in rows] if rows else []

    # ---------- ANNOUNCEMENTS ----------
    def create_table_announcements(self):
        sql = """CREATE TABLE IF NOT EXISTS announcements(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )"""
        self.execute(sql, commit=True)

    def insert_announcement(self, text: str):
        sql = "INSERT INTO announcements(text) VALUES (?)"
        self.execute(sql, text, commit=True)

    def get_announcements(self, limit: int = 20):
        sql = "SELECT id, text FROM announcements ORDER BY id DESC LIMIT ?"
        rows = self.execute(sql, limit, fetchall=True)
        return rows or []

    # ---------- INIT ----------
    def init_db(self):
        self.create_table_users()
        self.create_table_courses()
        self.create_table_teachers()
        self.create_table_students()
        self.create_table_groups()
        self.create_table_announcements()
