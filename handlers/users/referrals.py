from database.database import get_referrals_count, get_referrals_for_user
from utils.points import get_points

BOT_USERNAME_CACHE = None


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


def build_referrals_text(bot, user_id, username, full_name):
    """
    Takliflar haqidagi chiroyli matnni yasab beradi.
    """
    bot_username = get_bot_username(bot)

    # t.me bilan chiqaramiz, oddiy kliklanuvchi link bo'lsin
    if bot_username:
        display_link = f"t.me/{bot_username}?start={user_id}"
    else:
        display_link = "Bot username aniqlanmadi, iltimos admin bilan bog'laning."

    points = get_points(user_id)
    refs_count = get_referrals_count(user_id)
    refs = get_referrals_for_user(user_id)

    # Foydalanuvchi ismini yig'ib olamiz
    name_part = full_name or ""
    if username:
        if name_part:
            name_part = f"{name_part} (@{username})"
        else:
            name_part = f"@{username}"
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
    lines.append(display_link)  # Telegram buni avtomatik link qiladi
    lines.append("")
    lines.append("ℹ️ Har bir yangi foydalanuvchi sizning havolangiz orqali kelib, botdan foydalansa:")
    lines.append("• Sizga +300 ball qo'shiladi ✅")
    lines.append("• Takliflar soningiz ortib boradi 📈")
    lines.append("")
    if refs:
        lines.append("Oxirgi takliflar ro'yxati:")
        for r_user_id, r_username, r_full_name, created_at in refs[:10]:
            r_name = r_full_name or ""
            if r_username:
                if r_name:
                    r_name = f"{r_name} (@{r_username})"
                else:
                    r_name = f"@{r_username}"
            if not r_name:
                r_name = f"ID: {r_user_id}"
            lines.append(f"• {r_name} — {created_at}")
    else:
        lines.append("Hozircha takliflaringiz yo'q. Birinchi bo'lib do'stlaringizni taklif qiling 😊")

    return "\n".join(lines)


def setup_referral_handlers(bot):
    """
    main.py ichida:
        from handlers.users.referrals import setup_referral_handlers
        ...
        setup_referral_handlers(bot)
    deb chaqiriladi.
    """

    @bot.message_handler(func=lambda m: m.chat.type == "private" and m.text == "🤝 Takliflarim")
    def handle_referrals(message):
        user = message.from_user
        text = build_referrals_text(
            bot,
            user_id=user.id,
            username=user.username,
            full_name=(f"{user.first_name or ''} {user.last_name or ''}".strip())
        )
        bot.send_message(
            message.chat.id,
            text
        )
