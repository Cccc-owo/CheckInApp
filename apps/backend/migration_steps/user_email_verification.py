from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.engine import Connection


def _table_columns(conn: Connection, table_name: str) -> set[str]:
    rows = conn.execute(text(f"PRAGMA table_info({table_name})")).fetchall()
    return {str(row[1]) for row in rows}


def _add_column_if_missing(
    conn: Connection, table_name: str, columns: set[str], column_name: str, ddl: str
) -> set[str]:
    if column_name not in columns:
        conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {ddl}"))
        conn.commit()
        return _table_columns(conn, table_name)
    return columns


def _drop_column_if_present(
    conn: Connection, table_name: str, columns: set[str], column_name: str
) -> set[str]:
    if column_name in columns:
        conn.execute(text(f"ALTER TABLE {table_name} DROP COLUMN {column_name}"))
        conn.commit()
        return _table_columns(conn, table_name)
    return columns


def apply(conn: Connection) -> None:
    user_columns = _table_columns(conn, "users")
    user_columns = _add_column_if_missing(
        conn,
        "users",
        user_columns,
        "email_verified_at",
        "email_verified_at DATETIME",
    )
    user_columns = _add_column_if_missing(
        conn,
        "users",
        user_columns,
        "email_verification_code_hash",
        "email_verification_code_hash VARCHAR(200)",
    )
    _add_column_if_missing(
        conn,
        "users",
        user_columns,
        "email_verification_expires_at",
        "email_verification_expires_at DATETIME",
    )

    settings_columns = _table_columns(conn, "email_notification_settings")
    settings_columns = _add_column_if_missing(
        conn,
        "email_notification_settings",
        settings_columns,
        "require_admin_approval_for_registration",
        "require_admin_approval_for_registration BOOLEAN NOT NULL DEFAULT 1",
    )
    settings_columns = _add_column_if_missing(
        conn,
        "email_notification_settings",
        settings_columns,
        "require_verified_email_for_approval",
        "require_verified_email_for_approval BOOLEAN NOT NULL DEFAULT 1",
    )
    _drop_column_if_present(
        conn,
        "email_notification_settings",
        settings_columns,
        "warn_unverified_email_before_approval",
    )
