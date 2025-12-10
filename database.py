"""Модуль для работы с базой данных SQLite."""
import aiosqlite
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

DB_NAME = "village.db"


async def init_db():
    """Инициализация базы данных."""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                full_name TEXT NOT NULL,
                phone TEXT NOT NULL,
                plot_number TEXT NOT NULL,
                document_file_id TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()
        logger.info("База данных инициализирована")


async def create_user(
    telegram_id: int,
    username: Optional[str],
    full_name: str,
    phone: str,
    plot_number: str,
    document_file_id: str
) -> int:
    """Создать нового пользователя."""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("""
            INSERT INTO users (telegram_id, username, full_name, phone, plot_number, document_file_id, status)
            VALUES (?, ?, ?, ?, ?, ?, 'pending')
        """, (telegram_id, username, full_name, phone, plot_number, document_file_id))
        await db.commit()
        user_id = cursor.lastrowid
        logger.info(f"Создан пользователь: telegram_id={telegram_id}, user_id={user_id}")
        return user_id


async def get_user_by_telegram_id(telegram_id: int) -> Optional[Dict[str, Any]]:
    """Получить пользователя по telegram_id."""
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM users WHERE telegram_id = ?",
            (telegram_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return dict(row)
            return None


async def update_user_status(telegram_id: int, status: str):
    """Обновить статус пользователя."""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE users SET status = ? WHERE telegram_id = ?",
            (status, telegram_id)
        )
        await db.commit()
        logger.info(f"Обновлен статус пользователя {telegram_id}: {status}")


async def get_pending_users() -> list:
    """Получить список пользователей со статусом 'pending'."""
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM users WHERE status = 'pending' ORDER BY created_at DESC"
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def search_by_plot_number(plot_number: str) -> list:
    """Поиск пользователей по номеру участка."""
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM users WHERE plot_number LIKE ? ORDER BY created_at DESC",
            (f"%{plot_number}%",)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def search_by_phone(phone: str) -> list:
    """Поиск пользователей по номеру телефона."""
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM users WHERE phone LIKE ? ORDER BY created_at DESC",
            (f"%{phone}%",)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def search_by_full_name(full_name: str) -> list:
    """Поиск пользователей по ФИО."""
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM users WHERE full_name LIKE ? ORDER BY created_at DESC",
            (f"%{full_name}%",)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def get_statistics() -> dict:
    """Получить статистику по пользователям."""
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        
        # Общее количество
        async with db.execute("SELECT COUNT(*) as total FROM users") as cursor:
            total = (await cursor.fetchone())["total"]
        
        # По статусам
        async with db.execute("SELECT status, COUNT(*) as count FROM users GROUP BY status") as cursor:
            status_counts = {row["status"]: row["count"] for row in await cursor.fetchall()}
        
        return {
            "total": total,
            "pending": status_counts.get("pending", 0),
            "approved": status_counts.get("approved", 0),
            "rejected": status_counts.get("rejected", 0)
        }


async def get_all_users() -> list:
    """Получить всех пользователей."""
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM users ORDER BY created_at DESC"
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

