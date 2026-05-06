from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.engine import Connection


def apply(conn: Connection) -> None:
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS email_notification_settings (
                id INTEGER PRIMARY KEY,
                smtp_server VARCHAR(255) NOT NULL DEFAULT '',
                smtp_port INTEGER NOT NULL DEFAULT 465,
                smtp_sender_email VARCHAR(255) NOT NULL DEFAULT '',
                smtp_sender_password VARCHAR(500) NOT NULL DEFAULT '',
                smtp_use_ssl BOOLEAN NOT NULL DEFAULT 1,
                notify_token_expiring BOOLEAN NOT NULL DEFAULT 1,
                notify_check_in_success BOOLEAN NOT NULL DEFAULT 1,
                require_admin_approval_for_registration BOOLEAN NOT NULL DEFAULT 1,
                warn_unverified_email_before_approval BOOLEAN NOT NULL DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME
            )
            """
        )
    )
    conn.commit()
