import os
import datetime
from database.database import create_connection


def _safe_count(cursor, query: str, params: tuple = ()) -> int:
    """
    COUNT(*) so'rovlari uchun xavfsiz helper.
    Jadval bo'lmasa yoki xato bo'lsa, 0 qaytaramiz.
    """
    try:
        cursor.execute(query, params)
        row = cursor.fetchone()
        return row[0] if row and row[0] is not None else 0
    except Exception as e:
        print(f"[stats] COUNT xatosi: {e} | query={query}")
        return 0


def _safe_sum(cursor, query: str, params: tuple = ()) -> int:
    """
    SUM() so'rovlari uchun xavfsiz helper.
    """
    try:
        cursor.execute(query, params)
        row = cursor.fetchone()
        return row[0] if row and row[0] is not None else 0
    except Exception as e:
        print(f"[stats] SUM xatosi: {e} | query={query}")
        return 0


def get_last_backup_time(backup_dir: str = "backups") -> str:
    """
    Backups papkasidagi eng oxirgi .zip fayl vaqtini topish.
    topilmasa – mos matn qaytaramiz.
    """
    try:
        if not os.path.isdir(backup_dir):
            return "Backup topilmadi"

        files = [
            os.path.join(backup_dir, f)
            for f in os.listdir(backup_dir)
            if f.endswith(".zip")
        ]
        if not files:
            return "Backup topilmadi"

        latest = max(files, key=os.path.getmtime)
        ts = os.path.getmtime(latest)
        dt = datetime.datetime.fromtimestamp(ts)
        # O'zbekcha o'qilishi uchun oddiy format
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        print(f"[stats] last backup xatosi: {e}")
        return "Aniqlab bo'lmadi"


def get_bot_stats() -> dict:
    """
    Bot bo'yicha asosiy statistikalar.
    Natija dict ko'rinishida qaytadi.
    """
    conn = create_connection()
    cursor = conn.cursor()

    # Foydalanuvchilar
    total_users = _safe_count(cursor, "SELECT COUNT(*) FROM users")
    total_points = _safe_sum(cursor, "SELECT SUM(COALESCE(points, 0)) FROM users")
    total_referrals = _safe_count(cursor, "SELECT COUNT(*) FROM referrals")

    # Kurslar / talabalar
    total_courses = _safe_count(cursor, "SELECT COUNT(*) FROM courses")
    total_students = _safe_count(cursor, "SELECT COUNT(*) FROM students")
    approved_students = _safe_count(
        cursor,
        "SELECT COUNT(*) FROM students WHERE approved = 1"
    )

    # E'lonlar
    total_announcements = _safe_count(cursor, "SELECT COUNT(*) FROM announcements")

    # Sovg'a likelari
    total_gift_likes = _safe_count(cursor, "SELECT COUNT(*) FROM gift_likes")

    # Top foydalanuvchi (eng ko'p ball)
    top_user = None
    try:
        cursor.execute(
            """
            SELECT user_id, username, full_name, COALESCE(points,0) AS pts
            FROM users
            ORDER BY pts DESC, joined_at ASC
            LIMIT 1
            """
        )
        row = cursor.fetchone()
        if row:
            u_id, uname, fname, pts = row
            name_part = (fname or "").strip() or "Ismi ko'rsatilmagan"
            if uname:
                name_part = f"{name_part} (@{uname})"
            top_user = {
                "user_id": u_id,
                "display": name_part,
                "points": pts,
            }
    except Exception as e:
        print(f"[stats] top user xatosi: {e}")
        top_user = None

    conn.close()

    # Oxirgi backup vaqti
    last_backup = get_last_backup_time("backups")

    # O'rtacha ball (taxminiy)
    avg_points = 0
    if total_users > 0:
        avg_points = round(total_points / total_users, 1)

    stats = {
        "total_users": total_users,
        "total_points": total_points,
        "avg_points": avg_points,
        "total_referrals": total_referrals,
        "total_courses": total_courses,
        "total_students": total_students,
        "approved_students": approved_students,
        "total_announcements": total_announcements,
        "total_gift_likes": total_gift_likes,
        "top_user": top_user,
        "last_backup": last_backup,
    }

    return stats
