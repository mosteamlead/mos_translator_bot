import aiosqlite
from typing import Optional, Tuple

from bot.config import settings


CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS user_settings (
    user_id     INTEGER PRIMARY KEY,
    lang_from   TEXT,
    lang_to     TEXT,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


async def init_db() -> None:
    """Initialize SQLite database and tables."""
    async with aiosqlite.connect(settings.database_path) as db:
        await db.execute(CREATE_TABLE_SQL)
        await db.commit()


async def set_lang_from(user_id: int, lang_from: str) -> None:
    """Set or update the first language for a user."""
    async with aiosqlite.connect(settings.database_path) as db:
        await db.execute(
            """
            INSERT INTO user_settings (user_id, lang_from, lang_to)
            VALUES (?, ?, NULL)
            ON CONFLICT(user_id) DO UPDATE SET
                lang_from = excluded.lang_from,
                lang_to   = NULL,
                updated_at = CURRENT_TIMESTAMP
            """,
            (user_id, lang_from),
        )
        await db.commit()


async def set_lang_to(user_id: int, lang_to: str) -> None:
    """Set or update the second language for a user."""
    async with aiosqlite.connect(settings.database_path) as db:
        await db.execute(
            """
            UPDATE user_settings
            SET lang_to = ?, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
            """,
            (lang_to, user_id),
        )
        await db.commit()


async def get_user_languages(
    user_id: int,
) -> Optional[Tuple[Optional[str], Optional[str]]]:
    """Return (lang_from, lang_to) for the user, or None if not found."""
    async with aiosqlite.connect(settings.database_path) as db:
        async with db.execute(
            "SELECT lang_from, lang_to FROM user_settings WHERE user_id = ?",
            (user_id,),
        ) as cursor:
            row = await cursor.fetchone()

    if row is None:
        return None
    return row[0], row[1]