# utils/safe_telegram.py
import time
import json
from telebot.apihelper import ApiTelegramException


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


def safe_send_message(bot, chat_id, text, **kwargs) -> bool:
    for _ in range(3):
        try:
            bot.send_message(chat_id, text, **kwargs)
            return True
        except ApiTelegramException as e:
            s = str(e)
            if "403" in s or "blocked by the user" in s or "Forbidden" in s:
                return False
            if "429" in s or "Too Many Requests" in s:
                time.sleep(_extract_retry_after(e) + 1)
                continue
            raise
        except Exception:
            time.sleep(1.5)
            continue
    return False


def safe_send_photo(bot, chat_id, photo_file, **kwargs) -> bool:
    for _ in range(3):
        try:
            bot.send_photo(chat_id, photo_file, **kwargs)
            return True
        except ApiTelegramException as e:
            s = str(e)
            if "403" in s or "blocked by the user" in s or "Forbidden" in s:
                return False
            if "429" in s or "Too Many Requests" in s:
                time.sleep(_extract_retry_after(e) + 1)
                continue
            raise
        except Exception:
            time.sleep(1.5)
            continue
    return False
