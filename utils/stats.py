import os
import datetime
from database.database import create_connection

# Online deb hisoblash oynasi (daqiqada)
ONLINE_WINDOW_MIN = 10

# Bugungi ballni olish uchun qidiriladigan jadval nomlari (qaysi biri bo‘lsa, shundan oladi)
POINTS_LOG_TABLE_CANDIDATES = [
    "points_log",
    "points_logs",
    "points_history",
    "points_histories",
    "points_events",
    "points_transactions",
    "points_tx",
]


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


def _table_exists(cursor, table_name: str) -> bool:
    try:
        cursor.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1",
            (table_name,),
        )
        return cursor.fetchone() is not None
    except Exception as e:
        print(f"[stats] table_exists xatosi: {e} | table={table_name}")
        return False


def _get_table_columns(cursor, table_name: str) -> list[str]:
    try:
        cursor.execute(f"PRAGMA table_info({table_name})")
        rows = cursor.fetchall() or []
        # PRAGMA table_info: (cid, name, type, notnull, dflt_value, pk)
        return [r[1] for r in rows if r and len(r) > 1]
    except Exception as e:
        print(f"[stats] get_table_columns xatosi: {e} | table={table_name}")
        return []


def _pick_time_column(columns: list[str], preferred: list[str]) -> str | None:
    cols = set(columns or [])
    for c in preferred:
        if c in cols:
            return c
    return None


def _is_numeric_time_column(cursor, table: str, col: str) -> bool:
    """
    Col unix timestamp (integer/real) bo'lishi mumkinmi, shuni tekshiradi.
    """
    try:
        cursor.execute(
            f"SELECT typeof({col}) FROM {table} WHERE {col} IS NOT NULL LIMIT 1"
        )
        row = cursor.fetchone()
        if not row or row[0] is None:
            return False
        return str(row[0]).lower() in ("integer", "real")
    except Exception:
        return False


def _count_today_rows(cursor, table: str, time_col: str) -> int:
    """
    Bugungi yozuvlarni sanash.
    time_col TEXT bo'lsa: 'YYYY-MM-DD...' formatidan substr bilan oladi.
    time_col UNIX timestamp bo'lsa: start_ts/end_ts orasini oladi.
    """
    today = datetime.date.today()
    today_str = today.strftime("%Y-%m-%d")

    # numeric timestamp bo'lsa
    if _is_numeric_time_column(cursor, table, time_col):
        start_dt = datetime.datetime.combine(today, datetime.time.min)
        end_dt = start_dt + datetime.timedelta(days=1)
        start_ts = int(start_dt.timestamp())
        end_ts = int(end_dt.timestamp())
        return _safe_count(
            cursor,
            f"SELECT COUNT(*) FROM {table} WHERE {time_col} >= ? AND {time_col} < ?",
            (start_ts, end_ts),
        )

    # text datetime bo'lsa
    return _safe_count(
        cursor,
        f"SELECT COUNT(*) FROM {table} WHERE substr({time_col}, 1, 10) = ?",
        (today_str,),
    )


def _sum_today_points(cursor, table: str, points_col: str, time_col: str) -> int:
    """
    Bugun qo'shilgan ballarni SUM qiladi.
    points_col: delta/points/amount va hokazo
    """
    today = datetime.date.today()
    today_str = today.strftime("%Y-%m-%d")

    if _is_numeric_time_column(cursor, table, time_col):
        start_dt = datetime.datetime.combine(today, datetime.time.min)
        end_dt = start_dt + datetime.timedelta(days=1)
        start_ts = int(start_dt.timestamp())
        end_ts = int(end_dt.timestamp())
        return _safe_sum(
            cursor,
            f"SELECT SUM(COALESCE({points_col}, 0)) FROM {table} "
            f"WHERE {time_col} >= ? AND {time_col} < ?",
            (start_ts, end_ts),
        )

    return _safe_sum(
        cursor,
        f"SELECT SUM(COALESCE({points_col}, 0)) FROM {table} "
        f"WHERE substr({time_col}, 1, 10) = ?",
        (today_str,),
    )


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

    try:
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

        # Oxirgi backup vaqti
        last_backup = get_last_backup_time("backups")

        # O'rtacha ball (taxminiy)
        avg_points = 0
        if total_users > 0:
            avg_points = round(total_points / total_users, 1)

        # =========================
        # ✅ ONLINE USERS (aktivlar)
        # =========================
        online_users = 0
        try:
            if _table_exists(cursor, "users"):
                cols = _get_table_columns(cursor, "users")
                # qaysi biri bo‘lsa o‘shani olamiz
                time_col = _pick_time_column(
                    cols,
                    ["last_active", "last_seen", "updated_at", "last_activity", "joined_at"]
                )
                if time_col:
                    now = datetime.datetime.now()
                    start = now - datetime.timedelta(minutes=ONLINE_WINDOW_MIN)

                    if _is_numeric_time_column(cursor, "users", time_col):
                        start_ts = int(start.timestamp())
                        online_users = _safe_count(
                            cursor,
                            f"SELECT COUNT(*) FROM users WHERE {time_col} >= ?",
                            (start_ts,),
                        )
                    else:
                        # ISO text bo‘lsa
                        start_str = start.strftime("%Y-%m-%d %H:%M:%S")
                        online_users = _safe_count(
                            cursor,
                            f"SELECT COUNT(*) FROM users WHERE {time_col} >= ?",
                            (start_str,),
                        )
                else:
                    online_users = 0
        except Exception as e:
            print(f"[stats] online_users xatosi: {e}")
            online_users = 0

        # =========================
        # ✅ BUGUNGI: referrals + points
        # =========================
        today_referrals = 0
        try:
            if _table_exists(cursor, "referrals"):
                rcols = _get_table_columns(cursor, "referrals")
                r_time = _pick_time_column(
                    rcols,
                    ["created_at", "referred_at", "joined_at", "date", "timestamp"]
                )
                if r_time:
                    today_referrals = _count_today_rows(cursor, "referrals", r_time)
                else:
                    today_referrals = 0
        except Exception as e:
            print(f"[stats] today_referrals xatosi: {e}")
            today_referrals = 0

        today_points = 0
        today_points_available = False
        try:
            # points log jadvali bormi?
            found_table = None
            for t in POINTS_LOG_TABLE_CANDIDATES:
                if _table_exists(cursor, t):
                    found_table = t
                    break

            if found_table:
                pcols = _get_table_columns(cursor, found_table)
                p_time = _pick_time_column(
                    pcols,
                    ["created_at", "time", "timestamp", "added_at", "date"]
                )
                p_points = _pick_time_column(
                    pcols,
                    ["points", "delta", "amount", "value"]
                )

                if p_time and p_points:
                    today_points = _sum_today_points(cursor, found_table, p_points, p_time)
                    today_points_available = True
        except Exception as e:
            print(f"[stats] today_points xatosi: {e}")
            today_points = 0
            today_points_available = False

        stats = {
            # eski statlar (buzilmasin)
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

            # yangi qo‘shimchalar
            "online_users": online_users,
            "today_referrals": today_referrals,
            "today_points": today_points,
            "today_points_available": today_points_available,
            "online_window_min": ONLINE_WINDOW_MIN,
        }

        return stats

    finally:
        try:
            conn.close()
        except Exception:
            pass
