"""
Все операции с SQLite. Используется aiosqlite для неблокирующего доступа.
"""
import logging

import aiosqlite

import config

logger = logging.getLogger(__name__)


async def init_db() -> None:
    """Создаёт таблицы, если их нет."""
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS seen_jobs (
                job_id     TEXT PRIMARY KEY,
                source     TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS keywords (
                word TEXT PRIMARY KEY
            )
        """)
        await db.commit()
    logger.info("База данных инициализирована: %s", config.DB_PATH)


async def seed_keywords_if_empty(default_keywords: list[str]) -> None:
    """Если таблица keywords пуста — заполняет её стартовым набором."""
    async with aiosqlite.connect(config.DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM keywords") as cursor:
            row = await cursor.fetchone()
            count = row[0] if row else 0
        if count > 0:
            logger.info("В БД уже %d ключевых слов, сид не нужен.", count)
            return
        for word in default_keywords:
            await db.execute(
                "INSERT OR IGNORE INTO keywords (word) VALUES (?)", (word.lower(),)
            )
        await db.commit()
    logger.info("Загружено %d ключевых слов из конфига.", len(default_keywords))


async def is_job_seen(job_id: str) -> bool:
    async with aiosqlite.connect(config.DB_PATH) as db:
        async with db.execute(
            "SELECT 1 FROM seen_jobs WHERE job_id = ?", (job_id,)
        ) as cursor:
            return await cursor.fetchone() is not None


async def mark_job_seen(job_id: str, source: str) -> None:
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO seen_jobs (job_id, source) VALUES (?, ?)",
            (job_id, source),
        )
        await db.commit()


async def count_seen_jobs() -> int:
    async with aiosqlite.connect(config.DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM seen_jobs") as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0


async def load_keywords() -> list[str]:
    async with aiosqlite.connect(config.DB_PATH) as db:
        async with db.execute("SELECT word FROM keywords ORDER BY word") as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]


async def save_keyword(word: str) -> None:
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO keywords (word) VALUES (?)", (word.lower(),)
        )
        await db.commit()


async def delete_keyword(word: str) -> None:
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute("DELETE FROM keywords WHERE word = ?", (word.lower(),))
        await db.commit()
