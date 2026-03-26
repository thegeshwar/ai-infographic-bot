"""Database layer for Y Vault — SQLite with aiosqlite."""

import json
from datetime import datetime, timezone
from pathlib import Path

import aiosqlite

DB_PATH = Path(__file__).parent / "vault.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hook TEXT,
    headline TEXT,
    caption TEXT,
    hashtags TEXT,
    body TEXT,
    insight TEXT,
    source TEXT,
    source_url TEXT,
    pillar TEXT,
    template TEXT,
    html TEXT,
    image_filename TEXT,
    status TEXT NOT NULL DEFAULT 'ready',
    created_at TEXT NOT NULL,
    posted_at TEXT,
    posted_platforms TEXT
);
"""


async def get_db() -> aiosqlite.Connection:
    """Open a connection with WAL mode and Row factory."""
    db = await aiosqlite.connect(DB_PATH)
    await db.execute("PRAGMA journal_mode=WAL")
    db.row_factory = aiosqlite.Row
    return db


async def init_db() -> None:
    """Create tables if they don't exist."""
    db = await get_db()
    try:
        await db.executescript(SCHEMA)
        await db.commit()
    finally:
        await db.close()


async def get_posts(status: str = "ready") -> list[dict]:
    """Return all posts with the given status, newest first."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM posts WHERE status = ? ORDER BY created_at DESC",
            (status,),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


async def get_post(post_id: int) -> dict | None:
    """Return a single post by ID."""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM posts WHERE id = ?", (post_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None
    finally:
        await db.close()


async def update_post(post_id: int, caption: str, hashtags: list[str]) -> None:
    """Update caption and hashtags for a post."""
    db = await get_db()
    try:
        await db.execute(
            "UPDATE posts SET caption = ?, hashtags = ? WHERE id = ?",
            (caption, json.dumps(hashtags), post_id),
        )
        await db.commit()
    finally:
        await db.close()


async def mark_posted(post_id: int, platforms: list[str]) -> None:
    """Mark a post as posted with timestamp and platforms."""
    now = datetime.now(timezone.utc).isoformat()
    db = await get_db()
    try:
        await db.execute(
            "UPDATE posts SET status = 'posted', posted_at = ?, posted_platforms = ? WHERE id = ?",
            (now, json.dumps(platforms), post_id),
        )
        await db.commit()
    finally:
        await db.close()


async def insert_post(data: dict) -> int:
    """Insert a new post and return its ID."""
    now = datetime.now(timezone.utc).isoformat()
    db = await get_db()
    try:
        cursor = await db.execute(
            """INSERT INTO posts
               (hook, headline, caption, hashtags, body, insight, source, source_url,
                pillar, template, html, image_filename, status, created_at, posted_platforms)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                data.get("hook"),
                data.get("headline"),
                data.get("caption"),
                json.dumps(data.get("hashtags", [])),
                json.dumps(data.get("body", {})),
                data.get("insight"),
                data.get("source"),
                data.get("source_url"),
                data.get("pillar"),
                data.get("template"),
                data.get("html"),
                data.get("image_filename"),
                data.get("status", "ready"),
                now,
                json.dumps([]),
            ),
        )
        await db.commit()
        return cursor.lastrowid
    finally:
        await db.close()


async def get_counts() -> dict:
    """Return counts of posts by status."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT status, COUNT(*) as count FROM posts GROUP BY status"
        )
        rows = await cursor.fetchall()
        counts = {row["status"]: row["count"] for row in rows}
        counts.setdefault("ready", 0)
        counts.setdefault("posted", 0)
        return counts
    finally:
        await db.close()
