# utils/safe_telegram.py
import time
import json
import threading
from collections import deque
from typing import Optional, Any

from telebot.apihelper import ApiTelegramException


# =========================
# Config
# =========================

# 1 sekundda maksimum action
RATE_LIMIT_WINDOW = 1.0
RATE_LIMIT_MAX_ACTIONS = 3

# ogohlantirish spam bo'lmasin (har userga 2 sekundda 1 marta)
WARN_COOLDOWN = 2.0

# Retry policy
MAX_RETRIES = 3
GENERIC_RETRY_SLEEP = 1.5


# =========================
# Internal state (thread-safe)
# =========================

_lock = threading.Lock()

# key -> deque[timestamps]
# key: ("u", user_id) yoki ("c", chat_id) yoki ("g", "global")
_ACTIONS = {}

# key -> last_warn_ts
_LAST_WARN = {}


def _now() -> float:
    return time.time()


def _extract_retry_after(exc: ApiTelegramException) -> int:
    try:
        rj = getattr(exc, "result_json", None)
        if isinstance(rj, str):
            rj = json.loads(rj)
        if isinstance(rj, dict):
            return int(rj.get("parameters", {}).get("retry_after", 5))
    except Exception:
        pass
    return 5


def _rate_key(chat_id: Optional[int] = None, user_id: Optional[int] = None):
    # user bo'lsa user bo'yicha, bo'lmasa chat bo'yicha
    if user_id is not None:
        return ("u", int(user_id))
    if chat_id is not None:
        return ("c", int(chat_id))
    return ("g", "global")


def _too_many_actions(chat_id: Optional[int] = None, user_id: Optional[int] = None) -> bool:
    """
    1 sekund ichida 3 tadan ko'p bo'lsa True.
    """
    key = _rate_key(chat_id, user_id)
    now = _now()

    with _lock:
        dq = _ACTIONS.get(key)
        if dq is None:
            dq = deque()
            _ACTIONS[key] = dq

        # eski timestamp'larni chiqaramiz
        while dq and (now - dq[0]) > RATE_LIMIT_WINDOW:
            dq.popleft()

        if len(dq) >= RATE_LIMIT_MAX_ACTIONS:
            return True

        dq.append(now)
        return False


def _maybe_warn(bot, chat_id: int, user_id: Optional[int] = None):
    """
    Rate limitga tushganda userga ogohlantirish yuboradi,
    lekin spam bo'lmasligi uchun WARN_COOLDOWN bilan.
    """
    key = _rate_key(chat_id, user_id)
    now = _now()

    with _lock:
        last = _LAST_WARN.get(key, 0.0)
        if now - last < WARN_COOLDOWN:
            return
        _LAST_WARN[key] = now

    try:
        bot.send_message(
            chat_id,
            "⚠️ Juda tez bosyapsiz.\n"
            "Iltimos 1-2 sekund kutib, qayta urinib ko‘ring 🙂"
        )
    except Exception:
        # warn yuborilmasa ham problem emas
        pass


# =========================
# Public safe wrappers
# =========================

def safe_send_message(
    bot,
    chat_id: int,
    text: str,
    *,
    user_id: Optional[int] = None,
    return_bool: bool = True,
    **kwargs
) -> Any:
    """
    Xavfsiz send_message:
    - rate limit (1s:3)
    - 429 retry_after
    - 403 blocked -> False
    - xatoliklarda retry

    return_bool=True bo'lsa True/False qaytaradi.
    return_bool=False bo'lsa message object yoki None qaytaradi.
    """
    if _too_many_actions(chat_id=chat_id, user_id=user_id):
        _maybe_warn(bot, chat_id, user_id=user_id)
        return False if return_bool else None

    for _ in range(MAX_RETRIES):
        try:
            msg = bot.send_message(chat_id, text, **kwargs)
            return True if return_bool else msg

        except ApiTelegramException as e:
            s = str(e)

            # user block qilgan / yozib bo'lmaydi
            if "403" in s or "blocked by the user" in s or "Forbidden" in s:
                return False if return_bool else None

            # flood limit
            if "429" in s or "Too Many Requests" in s:
                time.sleep(_extract_retry_after(e) + 1)
                continue

            raise

        except Exception:
            time.sleep(GENERIC_RETRY_SLEEP)
            continue

    return False if return_bool else None


def safe_send_photo(
    bot,
    chat_id: int,
    photo_file,
    *,
    user_id: Optional[int] = None,
    return_bool: bool = True,
    **kwargs
) -> Any:
    """
    Xavfsiz send_photo (xuddi safe_send_message kabi).
    """
    if _too_many_actions(chat_id=chat_id, user_id=user_id):
        _maybe_warn(bot, chat_id, user_id=user_id)
        return False if return_bool else None

    for _ in range(MAX_RETRIES):
        try:
            msg = bot.send_photo(chat_id, photo_file, **kwargs)
            return True if return_bool else msg

        except ApiTelegramException as e:
            s = str(e)
            if "403" in s or "blocked by the user" in s or "Forbidden" in s:
                return False if return_bool else None
            if "429" in s or "Too Many Requests" in s:
                time.sleep(_extract_retry_after(e) + 1)
                continue
            raise

        except Exception:
            time.sleep(GENERIC_RETRY_SLEEP)
            continue

    return False if return_bool else None


def safe_answer_callback(
    bot,
    callback_query_id: str,
    text: str,
    *,
    chat_id: Optional[int] = None,
    user_id: Optional[int] = None,
    show_alert: bool = False
) -> bool:
    """
    Callback query'ga xavfsiz javob (inline tugma bosilganda).
    Rate limit ham ishlaydi.
    """
    if _too_many_actions(chat_id=chat_id, user_id=user_id):
        # callback uchun warn'ni toast qilib beramiz
        try:
            bot.answer_callback_query(callback_query_id, "Sekinroq 🙂", show_alert=False)
        except Exception:
            pass
        return False

    for _ in range(MAX_RETRIES):
        try:
            bot.answer_callback_query(callback_query_id, text, show_alert=show_alert)
            return True
        except ApiTelegramException as e:
            s = str(e)
            if "429" in s or "Too Many Requests" in s:
                time.sleep(_extract_retry_after(e) + 1)
                continue
            # callback fail bo'lsa ham yiqilmaymiz
            return False
        except Exception:
            time.sleep(0.5)
            continue
    return False
