import time

from keyboards.default import gift_menu_keyboard
from utils.safe_telegram import safe_send_message
from database.database import claim_bonus_atomic, get_points


# Tugma textini shu yerda bir marta belgilab qo'yamiz
BONUS_BUTTON_TEXTS = {"🎲 Bonus", "🎁 Bonus", "Bonus"}  # sen keyboardda qaysini qo'ysang o'sha ishlaydi

_LAST_BONUS_CLICK = {}


def _cooldown_click(user_id: int, seconds: float = 1.2) -> bool:
    """
    1-2 sekund ichida spam bosishni pasaytiradi (429 chiqmasin).
    """
    now = time.time()
    last = _LAST_BONUS_CLICK.get(user_id, 0)
    if now - last < seconds:
        return True
    _LAST_BONUS_CLICK[user_id] = now
    return False


def setup_bonus_handlers(bot):
    @bot.message_handler(func=lambda m: m.chat.type == "private" and (m.text or "").strip() in BONUS_BUTTON_TEXTS)
    def handle_bonus(message):
        user_id = message.from_user.id
        chat_id = message.chat.id

        # kichik anti-spam
        if _cooldown_click(user_id, 1.2):
            return

        ok, amount, wait_seconds, wait_hms = claim_bonus_atomic(user_id)

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

        # bonus olindi
        try:
            total = get_points(user_id)
        except Exception:
            total = None

        text = (
            "🎲 *BONUS TUSHdi!*\n\n"
            f"✅ Sizga *+{amount}* ball berildi.\n"
        )
        if total is not None:
            text += f"💰 Jami ballaringiz: *{total}*\n"

        text += "\n⏳ Keyingi bonus: *12 soatdan keyin*."

        safe_send_message(
            bot,
            chat_id,
            text,
            parse_mode="Markdown",
            reply_markup=gift_menu_keyboard()
        )
