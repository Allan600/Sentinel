import asyncpg
import os
from config import DATABASE_URL

pool = None
DB_ENABLED = False


async def connect():
    """
    Initialize database connection.
    If DATABASE_URL is missing or invalid, DB is disabled safely.
    """
    global pool, DB_ENABLED

    if not DATABASE_URL:
        print("⚠️ DATABASE_URL not set — database disabled.")
        DB_ENABLED = False
        return

    try:
        pool = await asyncpg.create_pool(DATABASE_URL)
        DB_ENABLED = True
        print("✅ Database connected successfully.")
    except Exception as e:
        DB_ENABLED = False
        print("⚠️ Database connection failed — running without DB.")
        print("Reason:", e)


async def fetch_user(user_id: int):
    """
    Fetch a user from DB or return defaults if DB is disabled.
    """
    if not DB_ENABLED or pool is None:
        return {
            "id": user_id,
            "power": 0,
            "trust": 50
        }

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM users WHERE id=$1",
            user_id
        )

        if not row:
            await conn.execute(
                "INSERT INTO users (id, power, trust) VALUES ($1, 0, 50)",
                user_id
            )
            return {
                "id": user_id,
                "power": 0,
                "trust": 50
            }

        return dict(row)


async def log_action(mod_id: int, action: str, target_id: int):
    """
    Log moderation actions if DB is enabled.
    """
    if not DB_ENABLED or pool is None:
        print(f"[LOG] {action} | mod={mod_id} target={target_id}")
        return

    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO mod_logs (mod_id, action, target_id) VALUES ($1, $2, $3)",
            mod_id,
            action,
            target_id
        )
