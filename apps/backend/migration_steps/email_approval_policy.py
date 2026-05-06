from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.engine import Connection


def _table_columns(conn: Connection, table_name: str) -> set[str]:
    rows = conn.execute(text(f"PRAGMA table_info({table_name})")).fetchall()
    return {str(row[1]) for row in rows}


def apply(conn: Connection) -> None:
    columns = _table_columns(conn, "email_notification_settings")
    if "require_verified_email_for_approval" not in columns:
        conn.execute(
            text(
                "ALTER TABLE email_notification_settings "
                "ADD COLUMN require_verified_email_for_approval BOOLEAN NOT NULL DEFAULT 1"
            )
        )
        conn.commit()
        columns = _table_columns(conn, "email_notification_settings")

    if "warn_unverified_email_before_approval" in columns:
        conn.execute(
            text(
                "ALTER TABLE email_notification_settings "
                "DROP COLUMN warn_unverified_email_before_approval"
            )
        )
        conn.commit()
