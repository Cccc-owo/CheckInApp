from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.engine import Connection


def apply(conn: Connection) -> None:
    verified_at = datetime.now(timezone.utc).isoformat()
    conn.execute(
        text(
            """
            UPDATE users
            SET email_verified_at = :verified_at
            WHERE email_verified_at IS NULL
              AND email IS NOT NULL
              AND email != ''
              AND is_approved = 1
            """
        ),
        {"verified_at": verified_at},
    )
    conn.commit()
