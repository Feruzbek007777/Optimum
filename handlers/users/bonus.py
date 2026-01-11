import time
import threading

from keyboards.default import gift_menu_keyboard
from utils.safe_telegram import safe_send_message
from database.database import create_connection, claim_bonus_atomic, get_points

# Tugma textlari (keyboardda qaysi bo'lsa shuni qo'y)
BONUS_BUTTON_TEXTS = {"🎲 Bonus", "🎁 Bonus", "Bonus", "🎰 Bonus"}

# 6 soat (xohlasang o'zing 12/6 qilib o'zgartirasan)
BONUS_COOLDOWN_SECONDS = 6 * 60 * 60

_LAST_BONUS_CLICK = {}


def _cooldown_click(user_id: int, seconds: float = 1.2) -> bool:
    """1-2 sekund ichida spam bosishni pasaytiradi (429 chiqmasin)."""
    now = time.time()
    last = _LAST_BONUS_CLICK.get(user_id, 0)
    if now - last < seconds:
        return True
    _LAST_BONUS_CLICK[user_id] = now
    return False


def _format_hms(seconds: int) -> str:
    if seconds < 0:
        seconds = 0
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


def _check_bonus_cooldown(user_id: int, cooldown_seconds: int):
    """
    Slot yuborishdan oldin faqat cooldownni tekshiradi (editsiz flow uchun).
    return: (ok: bool, wait_hms: str)
    """
    now = int(time.time())
    conn = create_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT last_claim_ts FROM bonus_claims WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        if row and row[0] is not None:
            last_ts = int(row[0])
            passed = now - last_ts
            if passed < cooldown_seconds:
                wait = cooldown_seconds - passed
                return False, _format_hms(wait)
        return True, "00:00:00"
    except Exception:
        # DBda muammo bo'lsa, userni qiynamaymiz
        return False, _format_hms(60)
    finally:
        try:
            conn.close()
        except Exception:
            pass


def _slot_reels_from_value(value: int):
    """
    Telegram 🎰 slot dice.value 1..64.
    value==64 -> jackpot (777) deb olamiz.
    Qolganlari 3 ta belgi bo'lib decode qilinadi (bizga faqat tenglik kerak).
    """
    if value == 64:
        return ("7", "7", "7")

    v = value - 1
    # 2-bit bo'lib ajratamiz
    a = (v & 3)
    b = ((v >> 2) & 3)
    c = ((v >> 4) & 3)

    # Telegram slot mapping
    m = [1, 2, 3, 0]
    return (m[a], m[b], m[c])


def _reward_and_reason_from_slot_value(value: int):
    """
    Sening qoidang:
    - 2 ta bir xil -> 70 ball
    - 3 ta bir xil -> 100 ball
    - 777 -> 200 ball
    - har xil -> 35 ball

    return: (reward:int, reason:str)
    """
    reels = _slot_reels_from_value(value)

    if value == 64:
        return 200, "👑 *JACKPOT!* Uchta *7️⃣* tushdi — (777). Shuning uchun *+200*!"

    if reels[0] == reels[1] == reels[2]:
        return 100, "🔥 *SUPER KOMBO!* Uchta bir xil belgi tushdi. Shuning uchun *+100*!"

    if reels[0] == reels[1] or reels[0] == reels[2] or reels[1] == reels[2]:
        return 70, "✨ *KOMBO!* Ikki dona bir xil belgi tushdi. Shuning uchun *+70*!"

    return 35, "🙂 *Oddiy holat.* Hammasi har xil tushdi. Shuning uchun *+35*!"


def _send_result_later(bot, chat_id: int, user_id: int, reward: int, reason: str):
    """
    Slot animatsiya tugashini kutib, keyin natijani yuboradi.
    Thread ichida ishlaydi (bot qotib qolmasin).
    """
    # slot animatsiya tugashi uchun
    time.sleep(3.8)

    try:
        total = get_points(user_id)
    except Exception:
        total = None

    text = (
        "🎰 *KAZINO BONUS NATIJASI*\n\n"
        f"{reason}\n\n"
        f"✅ Sizga *+{reward}* ball yozildi.\n"
    )
    if total is not None:
        text += f"💰 Jami ballaringiz: *{total}*\n"

    text += f"\n⏳ Keyingi bonus: *{BONUS_COOLDOWN_SECONDS // 3600} soatdan keyin*."

    safe_send_message(
        bot,
        chat_id,
        text,
        parse_mode="Markdown",
        reply_markup=gift_menu_keyboard()
    )


def setup_bonus_handlers(bot):
    @bot.message_handler(func=lambda m: m.chat.type == "private" and (m.text or "").strip() in BONUS_BUTTON_TEXTS)
    def handle_bonus(message):
        user_id = message.from_user.id
        chat_id = message.chat.id

        # kichik anti-spam
        if _cooldown_click(user_id, 1.2):
            return

        # Avval cooldownni tekshiramiz (slotni bekorga yubormaslik uchun)
        ok, wait_hms = _check_bonus_cooldown(user_id, BONUS_COOLDOWN_SECONDS)
        if not ok:
            text = (
                "⏳ *Bonus hali yopiq!*\n\n"
                f"Keyingi bonusni olishgacha: *{wait_hms}*\n\n"
                "Shoshilmang, vaqt kelganda yana bosasiz."
            )
            safe_send_message(
                bot,
                chat_id,
                text,
                parse_mode="Markdown",
                reply_markup=gift_menu_keyboard()
            )
            return

        # ✅ Slotni yuboramiz (Telegramning o'zi animatsiya qiladi)
        try:
            slot_msg = bot.send_dice(chat_id, emoji="🎰")
            slot_value = int(slot_msg.dice.value)
        except Exception:
            safe_send_message(
                bot,
                chat_id,
                "❌ Slot yuborishda muammo bo'ldi. Birozdan keyin qayta urinib ko'ring.",
                reply_markup=gift_menu_keyboard()
            )
            return

        reward, reason = _reward_and_reason_from_slot_value(slot_value)

        # ✅ Endi DBga atomik yozamiz (6 soatni DB ham tekshiradi)
        ok2, given, wait_seconds, wait_hms2 = claim_bonus_atomic(
            user_id,
            reward,
            cooldown_seconds=BONUS_COOLDOWN_SECONDS
        )

        if not ok2:
            # race bo'lsa (ikki joydan bosib yuborsa) — slot ko'rindi, lekin ball berilmaydi
            text = (
                "⏳ *Bonus allaqachon olingan!* \n\n"
                f"Keyingi bonusni olishgacha: *{wait_hms2}*\n\n"
                "Yana vaqt kelganda urinasiz."
            )
            safe_send_message(
                bot,
                chat_id,
                text,
                parse_mode="Markdown",
                reply_markup=gift_menu_keyboard()
            )
            return

        # Slot natijasi + sababini 3.8 sekunddan keyin yuboramiz
        threading.Thread(
            target=_send_result_later,
            args=(bot, chat_id, user_id, given, reason),
            daemon=True
        ).start()
