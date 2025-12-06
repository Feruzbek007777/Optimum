from utils.points import get_top_users


def format_top_users() -> str:
    """
    Top foydalanuvchilar ro'yxatini chiroyli matnga aylantiradi.
    get_top_users() -> (user_id, username, full_name, points, referrals_count)
    """
    rows = get_top_users(limit=10)

    if not rows:
        return "Hali hech kim ball to'plamagan 😊\n\nBirinchi bo'lib ball to'plang!"

    lines = ["🏆 Top 10 foydalanuvchi:\n"]
    for idx, (user_id, username, full_name, points, refs) in enumerate(rows, start=1):
        name_part = (full_name or "").strip()

        if username:
            # full_name + (@username) yoki faqat @username
            if name_part:
                name_part = f"{name_part} (@{username})"
            else:
                name_part = f"@{username}"

        if not name_part:
            # fallback, agar ikkalasi ham bo'lmasa
            name_part = f"ID: {user_id}"

        lines.append(f"{idx}) {name_part} — {points} ball, {refs} ta taklif")

    return "\n".join(lines)
