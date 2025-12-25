from database.database import create_connection, add_points


def find_user_by_username(raw_username: str):
    """
    users jadvalidan username bo'yicha foydalanuvchini topish.
    return:
      (user_id, username, full_name, joined_at, points, referrals_count) yoki None
    """
    if not raw_username:
        return None

    username = raw_username.strip()
    if username.startswith("@"):
        username = username[1:]

    if not username:
        return None

    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT 
                user_id,
                username,
                full_name,
                joined_at,
                COALESCE(points, 0) AS pts,
                COALESCE(referrals_count, 0) AS refs
            FROM users
            WHERE LOWER(username) = LOWER(?)
        ''', (username,))
        row = cursor.fetchone()
        return row
    finally:
        conn.close()


def give_points_to_user(user_id: int, points: float):
    """
    Foydalanuvchiga points ustuniga ball qo'shish.
    """
    if points == 0:
        return
    add_points(user_id, points)


def take_points_from_user(user_id: int, points: float):
    """
    Foydalanuvchidan ball ayirish.
    points > 0 bo'lishi kerak; ichida minus qilib yuboramiz.
    """
    if points == 0:
        return
    # manfiy qilib yuboramiz
    add_points(user_id, -abs(points))
