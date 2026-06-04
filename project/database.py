import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "sushi.db"


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                user_name TEXT,
                guest_name TEXT NOT NULL,
                guests INTEGER NOT NULL,
                date TEXT NOT NULL,
                slot TEXT NOT NULL,
                time TEXT NOT NULL,
                table_id INTEGER,
                occasion TEXT,
                upsells TEXT DEFAULT '[]',
                status TEXT DEFAULT 'pending',
                calendar_event_id TEXT,
                deposit_paid INTEGER DEFAULT 0,
                reminder_24h_sent INTEGER DEFAULT 0,
                reminder_3h_sent INTEGER DEFAULT 0,
                feedback_sent INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS waitlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                user_name TEXT,
                guests INTEGER NOT NULL,
                date TEXT NOT NULL,
                slot TEXT NOT NULL,
                notified INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now'))
            );
        """)


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def create_booking(data: dict) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO bookings
               (user_id, user_name, guest_name, guests, date, slot, time, table_id,
                occasion, upsells, status, calendar_event_id, deposit_paid)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                data["user_id"],
                data.get("user_name", ""),
                data["guest_name"],
                data["guests"],
                data["date"],
                data["slot"],
                data["time"],
                data.get("table_id"),
                data.get("occasion"),
                json.dumps(data.get("upsells", [])),
                data.get("status", "confirmed"),
                data.get("calendar_event_id"),
                int(data.get("deposit_paid", False)),
            ),
        )
        return cur.lastrowid


def update_booking(booking_id: int, **fields):
    if not fields:
        return
    cols = ", ".join(f"{k}=?" for k in fields)
    vals = list(fields.values()) + [booking_id]
    with get_conn() as conn:
        conn.execute(f"UPDATE bookings SET {cols} WHERE id=?", vals)


def get_booking(booking_id: int):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM bookings WHERE id=?", (booking_id,)).fetchone()
        return dict(row) if row else None


def get_bookings_for_slot(date: str, slot: str):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM bookings WHERE date=? AND slot=? AND status IN ('confirmed','pending')",
            (date, slot),
        ).fetchall()
        return [dict(r) for r in rows]


def get_user_active_booking(user_id: int):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM bookings WHERE user_id=? AND status='confirmed' ORDER BY id DESC LIMIT 1",
            (user_id,),
        ).fetchone()
        return dict(row) if row else None


def cancel_booking(booking_id: int):
    update_booking(booking_id, status="cancelled")


def add_waitlist(user_id, user_name, guests, date, slot):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO waitlist (user_id, user_name, guests, date, slot) VALUES (?,?,?,?,?)",
            (user_id, user_name, guests, date, slot),
        )


def get_waitlist_for_slot(date: str, slot: str):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM waitlist WHERE date=? AND slot=? AND notified=0 ORDER BY id",
            (date, slot),
        ).fetchall()
        return [dict(r) for r in rows]


def mark_waitlist_notified(waitlist_id: int):
    with get_conn() as conn:
        conn.execute("UPDATE waitlist SET notified=1 WHERE id=?", (waitlist_id,))


def get_pending_reminders():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM bookings WHERE status='confirmed'"
        ).fetchall()
        return [dict(r) for r in rows]
