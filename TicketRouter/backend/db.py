import sqlite3
from pathlib import Path
import datetime

DB_PATH = Path(__file__).resolve().parent / "tickets.db"


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL,
            category TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT '待处理',
            created_at TEXT NOT NULL
        )
        """
    )
    columns = [row[1] for row in conn.execute("PRAGMA table_info(tickets)").fetchall()]
    if "status" not in columns:
        conn.execute("ALTER TABLE tickets ADD COLUMN status TEXT NOT NULL DEFAULT '待处理'")
    conn.commit()
    conn.close()


def add_ticket(description: str, category: str) -> int:
    created_at = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db_connection()
    cursor = conn.execute(
        "INSERT INTO tickets (description, category, status, created_at) VALUES (?, ?, ?, ?)",
        (description, category, "待处理", created_at),
    )
    ticket_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return ticket_id


def get_all_tickets():
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM tickets ORDER BY id DESC").fetchall()
    conn.close()
    return rows


def get_ticket(ticket_id: int):
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    conn.close()
    return row


def update_ticket_status(ticket_id: int, status: str) -> None:
    conn = get_db_connection()
    conn.execute("UPDATE tickets SET status = ? WHERE id = ?", (status, ticket_id))
    conn.commit()
    conn.close()


def get_ticket_stats():
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT category, status, COUNT(*) AS count FROM tickets GROUP BY category, status"
    ).fetchall()
    conn.close()
    return rows
