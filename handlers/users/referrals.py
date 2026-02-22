import sqlite3
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import DATABASE_PATH, CHANNEL_USERNAME
from database.database import add_referral, get_referrals_count, get_referrals_for_user
from utils.points import get_points

# We reuse the single subscription checker used across the project.
from handlers.users.callbacks import check_subscription


BOT_USERNAME_CACHE = None


# =========================
# DB: pending_referrals
# =========================

def _conn():
    return sqlite3.connect(DATABASE_PATH)


def _init_pending_table():
    """
    Pending referrals: bonus hali berilmagan referral'lar.
    referred_id PRIMARY KEY -> bitta user faqat 1 marta pending bo'ladi.
    """
    conn = _conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS pending_referrals (
                referred_id INTEGER PRIMARY KEY,
                referrer_id INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
    finally:
        conn.close()


def set_pending_referral(referrer_id: int, referred_id: int) -> bool:
    """
    /start arg orqali kelgan referral'ni pending qilib qo'yadi.
    return True = yozildi, False = yozilmadi (bor yoki self-ref)
    """
    if not referrer_id or not referred_id:
        return False
    if referrer_id == referred_id:
        return False

    _init_pending_table()
    conn = _conn()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT OR IGNORE INTO pending_referrals (referred_id, referrer_id) VALUES (?, ?)",
            (referred_id, referrer_id)
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def get_pending_referrer(referred_id: int):
    _init_pending_table()
    conn = _conn()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT referrer_id FROM pending_referrals WHERE referred_id = ? LIMIT 1",
            (referred_id,)
        )
        row = cur.fetchone()
        return row[0] if row else None
    finally:
        conn.close()


def clear_pending_referral(referred_id: int):
    _init_pending_table()
    conn = _conn()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM pending_referrals WHERE referred_id = ?", (referred_id,))
        conn.commit()
    finally:
        conn.close()


# =========================
# Bot username cache
# =========================

def get_bot_username(bot):
    """
    Bot username'ini bir marta olib, cache qilib qo'yamiz.
    """
    global BOT_USERNAME_CACHE
    if BOT_USERNAME_CACHE:
        return BOT_USERNAME_CACHE

    try:
        me = bot.get_me()
        BOT_USERNAME_CACHE = me.username
        return BOT_USERNAME_CACHE
    except Exception:
        return None


def try_activate_pending_referral(bot, referred_id: int, bonus_points: int = 200) -> bool:
    """Activate a pending referral if conditions are met.

    Rules:
    - Bonus is given only once (referred_id UNIQUE inside add_referral).
    - Referred user must be subscribed to the channel.
    - Pending record is cleared after attempt.
    """

    # 1) Must be subscribed
    if not check_subscription(bot, referred_id):
        return False

    # 2) Must have pending
    referrer_id = get_pending_referrer(referred_id)
    if not referrer_id:
        return False

    # 3) Give bonus (referred_id UNIQUE inside add_referral)
    success = add_referral(referrer_id, referred_id, bonus_points=bonus_points)

    # 4) Clear pending regardless (prevents repeated prompts)
    clear_pending_referral(referred_id)

    if success:
        try:
            # Referred user haqida info (username/full_name) ni olib, referrerga ko'rsatamiz
            display_name = f"ID: {referred_id}"
            try:
                ch = bot.get_chat(referred_id)
                name = (getattr(ch, "first_name", "") or "").strip()
                last = (getattr(ch, "last_name", "") or "").strip()
                uname = (getattr(ch, "username", None) or None)
                full = (f"{name} {last}".strip() or None)
                if full and uname:
                    display_name = f"{full} (@{uname})"
                elif uname:
                    display_name = f"@{uname}"
                elif full:
                    display_name = full
            except Exception:
                pass

            mention = f'<a href="tg://user?id={referred_id}">{display_name}</a>'

            bot.send_message(
                referrer_id,
                "✅ Sizning havolangiz bilan kelgan foydalanuvchi kanalga obuna bo'ldi.\n"
                f"👤 Foydalanuvchi: {mention}\n"
                f"🎁 Sizga +{bonus_points} ball berildi.",
                parse_mode="HTML",
                disable_web_page_preview=True,
            )
        except Exception:
            pass

    return success


# =========================
# Text builder
# =========================

def build_referrals_text_and_kb(bot, user_id, username, full_name):
    bot_username = get_bot_username(bot)

    # referral link
    if bot_username:
        display_link = f"t.me/{bot_username}?start={user_id}"
    else:
        display_link = "Bot username aniqlanmadi, iltimos admin bilan bog'laning."

    points = get_points(user_id)
    refs_count = get_referrals_count(user_id)
    refs = get_referrals_for_user(user_id)

    # display name
    name_part = (full_name or "").strip()
    if username:
        name_part = f"{name_part} (@{username})" if name_part else f"@{username}"
    if not name_part:
        name_part = f"ID: {user_id}"

    lines = []
    lines.append("🤝 Takliflar bo'limi")
    lines.append("")
    lines.append(f"👤 Siz: {name_part}")
    lines.append(f"💰 Ballaringiz: {points}")
    lines.append(f"👥 Taklif qilgan odamlaringiz soni: {refs_count}")
    lines.append("")
    lines.append("🔗 Sizning taklif havolangiz:")
    lines.append(display_link)
    lines.append("")
    lines.append("ℹ️ Bonus sharti:")
    lines.append("• Do'stingiz havola bilan kiradi")
    lines.append(f"• {CHANNEL_USERNAME} kanaliga obuna bo'ladi")
    lines.append("• Shundan keyin sizga +200 ball beriladi ✅")
    lines.append("")

    kb = None
    pending_referrer = get_pending_referrer(user_id)

    # Agar user referral bilan kelgan bo'lsa va hali obuna tekshirib bonus bermagan bo'lsa
    if pending_referrer:
        lines.append("⚠️ Siz referral orqali kirgansiz, lekin bonus hali faollashmagan.")
        lines.append(f"1) Avval {CHANNEL_USERNAME} kanaliga obuna bo'ling.")
        lines.append("2) Keyin pastdagi tugmani bosing: ✅ Bonusni faollashtirish")
        kb = InlineKeyboardMarkup(row_width=1)
        kb.add(InlineKeyboardButton("✅ Bonusni faollashtirish", callback_data="ref_check_sub"))

    if refs:
        lines.append("")
        lines.append("🕘 Oxirgi takliflar ro'yxati:")
        for r_user_id, r_username, r_full_name, created_at in refs[:10]:
            r_name = (r_full_name or "").strip()
            if r_username:
                r_name = f"{r_name} (@{r_username})" if r_name else f"@{r_username}"
            if not r_name:
                r_name = f"ID: {r_user_id}"
            lines.append(f"• {r_name} — {created_at}")
    else:
        lines.append("Hozircha takliflaringiz yo'q. Birinchi bo'lib do'stlaringizni taklif qiling 😊")

    return "\n".join(lines), kb


# =========================
# /start hook (1 qator chaqiriladi)
# =========================

def process_start_referral(message) -> bool:
    """
    Sizning mavjud /start handler ichidan chaqiriladi.
    Agar /start argument (referrer_id) bo'lsa -> pending_referrals ga yozadi.
    Ball bermaydi. Ball faqat obuna tekshirilgandan keyin beriladi.

    /start 123456789
    """
    try:
        text = (message.text or "").strip()
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            return False

        arg = parts[1].strip()
        if not arg.isdigit():
            return False

        referrer_id = int(arg)
        referred_id = message.from_user.id
        return set_pending_referral(referrer_id, referred_id)
    except Exception:
        return False


# =========================
# Handlers
# =========================

def setup_referral_handlers(bot):
    _init_pending_table()

    @bot.message_handler(func=lambda m: m.chat.type == "private" and m.text == "🤝 Takliflarim")
    def handle_referrals(message):
        user = message.from_user
        text, kb = build_referrals_text_and_kb(
            bot,
            user_id=user.id,
            username=user.username,
            full_name=(f"{user.first_name or ''} {user.last_name or ''}".strip())
        )
        bot.send_message(message.chat.id, text, reply_markup=kb)

    @bot.callback_query_handler(func=lambda c: c.data == "ref_check_sub")
    def handle_ref_check(call):
        user_id = call.from_user.id

        # 1) Pending bormi? (subscribed bo'lmasa ham, aniqroq xabar beramiz)
        if not get_pending_referrer(user_id):
            bot.answer_callback_query(call.id, "Pending bonus topilmadi.", show_alert=True)
            return

        # 2) Obuna bo'lmagan bo'lsa
        if not check_subscription(bot, user_id):
            bot.answer_callback_query(
                call.id,
                f"❌ Avval {CHANNEL_USERNAME} kanaliga obuna bo'ling.",
                show_alert=True,
            )
            return

        # 3) Bonusni faollashtiramiz
        success = try_activate_pending_referral(bot, user_id, bonus_points=200)
        if success:
            bot.answer_callback_query(call.id, "✅ Bonus faollashdi. Rahmat!", show_alert=True)
        else:
            bot.answer_callback_query(call.id, "Bonus allaqachon berilgan yoki xatolik.", show_alert=True)
