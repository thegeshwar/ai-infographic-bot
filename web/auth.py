"""Authentication helpers for Y Vault."""

import uuid
from datetime import datetime, timedelta, timezone

import bcrypt

from web.db import get_db


def hash_password(password: str) -> str:
    """Hash a password with bcrypt, 12 rounds."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()


def verify_password(password: str, hashed: str) -> bool:
    """Check a password against a bcrypt hash."""
    return bcrypt.checkpw(password.encode(), hashed.encode())


async def authenticate(email: str, password: str) -> int | None:
    """Verify credentials and return user_id, or None."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT id, password_hash FROM users WHERE email = ?", (email,)
        )
        row = await cursor.fetchone()
        if row and verify_password(password, row["password_hash"]):
            return row["id"]
        return None
    finally:
        await db.close()


async def create_session(user_id: int) -> str:
    """Create a new session with 30-day expiry, return session ID."""
    session_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    expires = now + timedelta(days=30)
    db = await get_db()
    try:
        await db.execute(
            "INSERT INTO sessions (id, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
            (session_id, user_id, now.isoformat(), expires.isoformat()),
        )
        await db.commit()
        return session_id
    finally:
        await db.close()


async def validate_session(session_id: str) -> int | None:
    """Return user_id if session is valid and not expired, else None."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT user_id, expires_at FROM sessions WHERE id = ?", (session_id,)
        )
        row = await cursor.fetchone()
        if not row:
            return None
        expires = datetime.fromisoformat(row["expires_at"])
        if datetime.now(timezone.utc) > expires:
            await db.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
            await db.commit()
            return None
        return row["user_id"]
    finally:
        await db.close()


async def delete_session(session_id: str) -> None:
    """Delete a session (logout)."""
    db = await get_db()
    try:
        await db.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        await db.commit()
    finally:
        await db.close()
