"""
Ballar va takliflar bilan ishlash uchun qulay yordamchi funksiyalar.

Asl ma'lumotlar bazasi logikasi database/database.py ichida.
Bu yerda faqat o'sha funksiyalarga "short-cut" berilgan.
"""

from database.database import (
    add_points as db_add_points,
    get_points as db_get_points,
    set_points as db_set_points,
    increment_referrals as db_increment_referrals,
    get_referrals_count as db_get_referrals_count,
    get_top_users as db_get_top_users,
    get_referrals_for_user as db_get_referrals_for_user,
)


def add_points(user_id: int, amount: int):
    """Userga ball qo'shish"""
    db_add_points(user_id, amount)


def get_points(user_id: int) -> int:
    """User ballini olish"""
    return db_get_points(user_id)


def set_points(user_id: int, value: int):
    """User ballini to'g'ridan to'g'ri o'rnatish"""
    db_set_points(user_id, value)


def increment_referrals(user_id: int):
    """Takliflar sonini +1 qilish (agar kerak bo'lsa)"""
    db_increment_referrals(user_id)


def get_referrals_count(user_id: int) -> int:
    """User nechta odamni taklif qilganini olish"""
    return db_get_referrals_count(user_id)


def get_top_users(limit: int = 10):
    """Top foydalanuvchilarni olish"""
    return db_get_top_users(limit)


def get_user_referrals(referrer_id: int):
    """User taklif qilganlar ro'yxati"""
    return db_get_referrals_for_user(referrer_id)
