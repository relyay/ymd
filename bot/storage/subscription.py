import math
import time
import sqlite3

from bot.config import SUBSCRIPTIONS_DB, SUBSCRIBE_DURATION_DAYS


def init_db():
    conn = sqlite3.connect(SUBSCRIPTIONS_DB)
    try:
        c = conn.cursor()
        c.execute(
            """CREATE TABLE IF NOT EXISTS subscriptions
               (
                   user_id
                   INTEGER
                   PRIMARY
                   KEY,
                   expires_at
                   INTEGER
               )"""
        )
        conn.commit()
    finally:
        conn.close()


def add_subscription(user_id: int, days: int = SUBSCRIBE_DURATION_DAYS) -> None:
    conn = sqlite3.connect(SUBSCRIPTIONS_DB)
    try:
        c = conn.cursor()
        c.execute("SELECT expires_at FROM subscriptions WHERE user_id = ?", (user_id,))
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

        c.execute("INSERT OR REPLACE INTO subscriptions (user_id, expires_at) VALUES (?, ?)",
                  (user_id, new_expires))
        conn.commit()
    finally:
        conn.close()


def get_subscription_days_left(user_id: int) -> int:
    conn = sqlite3.connect(SUBSCRIPTIONS_DB)
    try:
        c = conn.cursor()
        c.execute("SELECT expires_at FROM subscriptions WHERE user_id = ?", (user_id,))
        row = c.fetchone()
    finally:
        conn.close()

    if not row:
        return 0
    expires_at = int(row[0])
    if expires_at == -1:
        return -1
    now = int(time.time())
    if expires_at <= now:
        return 0
    seconds_left = expires_at - now
    days_left = math.ceil(seconds_left / 86400)
    return days_left


def is_subscribed(user_id: int) -> bool:
    days = get_subscription_days_left(user_id)
    return days == -1 or days > 0
