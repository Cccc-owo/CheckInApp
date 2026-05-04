from __future__ import annotations

from sqlalchemy.engine import Connection
from sqlalchemy import text


def _table_columns(conn: Connection, table_name: str) -> set[str]:
    rows = conn.execute(text(f"PRAGMA table_info({table_name})")).fetchall()
    return {str(row[1]) for row in rows}


def apply(conn: Connection) -> None:
    columns = _table_columns(conn, "users")

    if "failed_login_attempts" not in columns:
        conn.execute(
            text("ALTER TABLE users ADD COLUMN failed_login_attempts INTEGER DEFAULT 0 NOT NULL")
        )
        conn.commit()

    columns = _table_columns(conn, "users")
    if "locked_until" not in columns:
        conn.execute(text("ALTER TABLE users ADD COLUMN locked_until DATETIME"))
        conn.commit()

    columns = _table_columns(conn, "users")
    if "last_failed_login" not in columns:
        conn.execute(text("ALTER TABLE users ADD COLUMN last_failed_login DATETIME"))
        conn.commit()
