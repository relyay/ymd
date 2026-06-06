import math
import sqlite3
import time

from bot.config import ADMIN_IDS, SUBSCRIBE_DURATION_DAYS, SUBSCRIPTIONS_DB


def init_users_table():
    conn = sqlite3.connect(SUBSCRIPTIONS_DB)
    try:
        c = conn.cursor()
        c.execute(
            """CREATE TABLE IF NOT EXISTS users
               (
                   user_id INTEGER PRIMARY KEY,
                   lang TEXT NOT NULL DEFAULT 'ru',
                   expires_at INTEGER NOT NULL DEFAULT 0,
                   is_admin INTEGER NOT NULL DEFAULT 0
               )"""
        )
        conn.commit()
    finally:
        conn.close()


def register_user(user_id: int) -> None:
    conn = sqlite3.connect(SUBSCRIPTIONS_DB)
    try:
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
        if user_id in ADMIN_IDS:
            c.execute("UPDATE users SET is_admin = 1 WHERE user_id = ?", (user_id,))
        conn.commit()
    finally:
        conn.close()


def sync_admins() -> None:
    conn = sqlite3.connect(SUBSCRIPTIONS_DB)
    try:
        c = conn.cursor()
        c.execute("UPDATE users SET is_admin = 0")
        for uid in ADMIN_IDS:
            c.execute(
                "INSERT INTO users (user_id, is_admin) VALUES (?, 1) "
                "ON CONFLICT(user_id) DO UPDATE SET is_admin = 1",
                (uid,),
            )
        conn.commit()
    finally:
        conn.close()


def get_user_lang(user_id: int) -> str:
    conn = sqlite3.connect(SUBSCRIPTIONS_DB)
    try:
        c = conn.cursor()
        c.execute("SELECT lang FROM users WHERE user_id = ?", (user_id,))
        row = c.fetchone()
    finally:
        conn.close()
    return row[0] if row else "ru"


def set_user_lang(user_id: int, lang: str) -> None:
    conn = sqlite3.connect(SUBSCRIPTIONS_DB)
    try:
        c = conn.cursor()
        c.execute("UPDATE users SET lang = ? WHERE user_id = ?", (lang, user_id))
        conn.commit()
    finally:
        conn.close()


def add_subscription(user_id: int, days: int = SUBSCRIBE_DURATION_DAYS) -> None:
    conn = sqlite3.connect(SUBSCRIPTIONS_DB)
    try:
        c = conn.cursor()
        c.execute("SELECT expires_at FROM users WHERE user_id = ?", (user_id,))
        row = c.fetchone()

        if days == -1:
            new_expires = -1
        elif row:
            current = int(row[0])
            if current == -1:
                return
            now = int(time.time())
            base = current if current > now else now
            new_expires = base + days * 86400
        else:
            new_expires = int(time.time()) + days * 86400

        if not row:
            register_user(user_id)

        c.execute(
            "UPDATE users SET expires_at = ? WHERE user_id = ?",
            (new_expires, user_id),
        )
        conn.commit()
    finally:
        conn.close()


def get_subscription_days_left(user_id: int) -> int:
    conn = sqlite3.connect(SUBSCRIPTIONS_DB)
    try:
        c = conn.cursor()
        c.execute("SELECT expires_at FROM users WHERE user_id = ?", (user_id,))
        row = c.fetchone()
    finally:
        conn.close()

    if not row:
        return 0
    expires_at = int(row[0])
    if expires_at == -1:
        return -1
    if expires_at == 0:
        return 0
    now = int(time.time())
    if expires_at <= now:
        return 0
    seconds_left = expires_at - now
    days_left = math.ceil(seconds_left / 86400)
    return days_left


def is_subscribed(user_id: int) -> bool:
    days = get_subscription_days_left(user_id)
    return days == -1 or days > 0
