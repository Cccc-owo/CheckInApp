from __future__ import annotations

import logging
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import Engine, text
from sqlalchemy.engine import Connection

from backend.migration_steps.account_lockout import apply as apply_account_lockout
from backend.migration_steps.email_notification_settings import (
    apply as apply_email_notification_settings,
)
from backend.migration_steps.task_thread_id import apply as apply_task_thread_id
from backend.models.database import engine as default_engine

logger = logging.getLogger(__name__)

MIGRATION_TABLE_NAME = "schema_migrations"


@dataclass(frozen=True)
class Migration:
    id: str
    description: str
    apply: Callable[[Connection], None]


@dataclass(frozen=True)
class MigrationRunResult:
    applied: tuple[str, ...]
    skipped: tuple[str, ...]


class MigrationExecutionError(RuntimeError):
    def __init__(self, migration_id: str, original: Exception) -> None:
        self.migration_id = migration_id
        self.original = original
        super().__init__(f"Migration {migration_id} failed: {original}")


def ensure_migration_table(conn: Connection) -> None:
    conn.execute(
        text(
            f"""
            CREATE TABLE IF NOT EXISTS {MIGRATION_TABLE_NAME} (
                id VARCHAR(200) PRIMARY KEY,
                description VARCHAR(500) NOT NULL,
                applied_at DATETIME NOT NULL
            )
            """
        )
    )
    conn.commit()


def get_applied_migration_ids(conn: Connection) -> set[str]:
    ensure_migration_table(conn)
    rows = conn.execute(text(f"SELECT id FROM {MIGRATION_TABLE_NAME}")).fetchall()
    return {str(row.id) for row in rows}


def mark_migration_applied(conn: Connection, migration: Migration) -> None:
    conn.execute(
        text(
            f"""
            INSERT INTO {MIGRATION_TABLE_NAME} (id, description, applied_at)
            VALUES (:id, :description, :applied_at)
            """
        ),
        {
            "id": migration.id,
            "description": migration.description,
            "applied_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    conn.commit()


MIGRATIONS: tuple[Migration, ...] = (
    Migration(
        id="2026050401_add_account_lockout",
        description="Add account lockout columns to users.",
        apply=apply_account_lockout,
    ),
    Migration(
        id="2026050402_add_task_thread_id",
        description="Add and backfill check-in task thread identity.",
        apply=apply_task_thread_id,
    ),
    Migration(
        id="2026050501_add_email_notification_settings",
        description="Add admin-managed email notification settings.",
        apply=apply_email_notification_settings,
    ),
)


def run_pending_migrations(
    *,
    engine: Engine = default_engine,
    migrations: Sequence[Migration] = MIGRATIONS,
) -> MigrationRunResult:
    applied: list[str] = []
    skipped: list[str] = []

    with engine.connect() as conn:
        applied_ids = get_applied_migration_ids(conn)

        for migration in migrations:
            if migration.id in applied_ids:
                logger.info("Skipping applied migration %s", migration.id)
                skipped.append(migration.id)
                continue

            logger.info("Applying migration %s: %s", migration.id, migration.description)
            try:
                migration.apply(conn)
                mark_migration_applied(conn, migration)
            except Exception as exc:
                conn.rollback()
                logger.exception("Migration %s failed", migration.id)
                raise MigrationExecutionError(migration.id, exc) from exc

            logger.info("Applied migration %s", migration.id)
            applied.append(migration.id)
            applied_ids.add(migration.id)

    return MigrationRunResult(applied=tuple(applied), skipped=tuple(skipped))
