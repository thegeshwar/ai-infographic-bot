"""Seed the default user for Y Vault. Run: python3 -m web.seed"""

import asyncio

from web.auth import hash_password
from web.db import get_db, init_db


async def seed() -> None:
    await init_db()

    email = "y@cucircuits.com"
    password = "tejuisjustbetter"

    db = await get_db()
    try:
        cursor = await db.execute("SELECT id FROM users WHERE email = ?", (email,))
        if await cursor.fetchone():
            print(f"User {email} already exists, skipping.")
            return

        pw_hash = hash_password(password)
        await db.execute(
            "INSERT INTO users (email, password_hash) VALUES (?, ?)",
            (email, pw_hash),
        )
        await db.commit()
        print(f"Seeded user: {email}")
    finally:
        await db.close()


if __name__ == "__main__":
    asyncio.run(seed())
