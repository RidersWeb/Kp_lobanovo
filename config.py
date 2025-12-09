"""Конфигурация бота."""
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS_STR = os.getenv("ADMIN_IDS", "")
GROUP_ID = os.getenv("GROUP_ID")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в .env файле")

# Поддержка нескольких админов (через запятую в .env)
if ADMIN_IDS_STR:
    ADMIN_IDS = [int(admin_id.strip()) for admin_id in ADMIN_IDS_STR.split(",") if admin_id.strip()]
else:
    # Обратная совместимость: если ADMIN_IDS не указан, пробуем ADMIN_ID
    old_admin_id = os.getenv("ADMIN_ID", "0")
    ADMIN_IDS = [int(old_admin_id)] if old_admin_id != "0" else []

if not ADMIN_IDS:
    raise ValueError("ADMIN_IDS не найден в .env файле (укажите ID админов через запятую)")

if not GROUP_ID:
    raise ValueError("GROUP_ID не найден в .env файле")


def is_admin(user_id: int) -> bool:
    """Проверить, является ли пользователь админом."""
    return user_id in ADMIN_IDS


