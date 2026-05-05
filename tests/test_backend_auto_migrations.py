from __future__ import annotations

from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine, text

from backend.migrations import (
    MIGRATIONS,
    Migration,
    MigrationExecutionError,
    get_applied_migration_ids,
    run_pending_migrations,
)
from backend.migration_steps.account_lockout import apply as apply_account_lockout
from backend.migration_steps.email_notification_settings import (
    apply as apply_email_notification_settings,
)
from backend.migration_steps.task_thread_id import apply as apply_task_thread_id


def test_pending_migration_is_recorded_and_skipped_on_next_run() -> None:
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    calls: list[str] = []

    def apply_test_migration(conn) -> None:
        calls.append("001_test")
        conn.execute(text("CREATE TABLE example (id INTEGER PRIMARY KEY)"))

    migrations = (
        Migration(
            id="001_test",
            description="create example table",
            apply=apply_test_migration,
        ),
    )

    first_result = run_pending_migrations(engine=engine, migrations=migrations)
    second_result = run_pending_migrations(engine=engine, migrations=migrations)

    with engine.connect() as conn:
        applied_ids = get_applied_migration_ids(conn)

    assert first_result.applied == ("001_test",)
    assert first_result.skipped == ()
    assert second_result.applied == ()
    assert second_result.skipped == ("001_test",)
    assert calls == ["001_test"]
    assert applied_ids == {"001_test"}


def test_failed_migration_is_not_recorded_as_applied() -> None:
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})

    def broken_migration(conn) -> None:
        conn.execute(text("CREATE TABLE before_failure (id INTEGER PRIMARY KEY)"))
        raise RuntimeError("boom")

    migrations = (
        Migration(
            id="001_broken",
            description="broken migration",
            apply=broken_migration,
        ),
    )

    with pytest.raises(MigrationExecutionError) as exc_info:
        run_pending_migrations(engine=engine, migrations=migrations)

    with engine.connect() as conn:
        applied_ids = get_applied_migration_ids(conn)

    assert exc_info.value.migration_id == "001_broken"
    assert applied_ids == set()


def test_existing_migrations_are_registered_in_order() -> None:
    assert [migration.id for migration in MIGRATIONS] == [
        "2026050401_add_account_lockout",
        "2026050402_add_task_thread_id",
        "2026050501_add_email_notification_settings",
    ]
    assert [migration.apply.__module__ for migration in MIGRATIONS] == [
        "backend.migration_steps.account_lockout",
        "backend.migration_steps.task_thread_id",
        "backend.migration_steps.email_notification_settings",
    ]


def test_email_notification_settings_migration_creates_settings_table() -> None:
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})

    with engine.connect() as conn:
        apply_email_notification_settings(conn)

        columns = {
            row[1] for row in conn.execute(text("PRAGMA table_info(email_notification_settings)"))
        }

    assert {
        "smtp_server",
        "smtp_port",
        "smtp_sender_email",
        "smtp_sender_password",
        "smtp_use_ssl",
        "notify_token_expiring",
        "notify_check_in_success",
    } <= columns


def test_account_lockout_migration_adds_missing_user_fields() -> None:
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})

    with engine.connect() as conn:
        conn.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY, alias VARCHAR(50))"))
        conn.commit()

        apply_account_lockout(conn)

        columns = {row[1] for row in conn.execute(text("PRAGMA table_info(users)"))}

    assert {"failed_login_attempts", "locked_until", "last_failed_login"} <= columns


def test_task_thread_id_migration_backfills_payload_thread_id() -> None:
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})

    with engine.connect() as conn:
        conn.execute(
            text(
                "CREATE TABLE check_in_tasks ("
                "id INTEGER PRIMARY KEY, "
                "user_id INTEGER NOT NULL, "
                "payload_config TEXT NOT NULL"
                ")"
            )
        )
        conn.execute(
            text(
                "INSERT INTO check_in_tasks (id, user_id, payload_config) "
                'VALUES (1, 10, \'{"ThreadId":"thread-1"}\')'
            )
        )
        conn.commit()

        apply_task_thread_id(conn)

        row = conn.execute(text("SELECT thread_id FROM check_in_tasks WHERE id = 1")).one()
        indexes = {row[1] for row in conn.execute(text("PRAGMA index_list(check_in_tasks)"))}

    assert row.thread_id == "thread-1"
    assert "ix_task_user_thread_id_unique" in indexes


def test_task_thread_id_migration_rejects_invalid_payloads() -> None:
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})

    with engine.connect() as conn:
        conn.execute(
            text(
                "CREATE TABLE check_in_tasks ("
                "id INTEGER PRIMARY KEY, "
                "user_id INTEGER NOT NULL, "
                "payload_config TEXT NOT NULL"
                ")"
            )
        )
        conn.execute(
            text("INSERT INTO check_in_tasks (id, user_id, payload_config) VALUES (1, 10, '{}')")
        )
        conn.commit()

        with pytest.raises(RuntimeError, match="ThreadId"):
            apply_task_thread_id(conn)


def test_task_thread_id_migration_does_not_recreate_existing_unique_index() -> None:
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})

    with engine.connect() as conn:
        conn.execute(
            text(
                "CREATE TABLE check_in_tasks ("
                "id INTEGER PRIMARY KEY, "
                "user_id INTEGER NOT NULL, "
                "payload_config TEXT NOT NULL, "
                "thread_id VARCHAR(100)"
                ")"
            )
        )
        conn.execute(
            text(
                "INSERT INTO check_in_tasks (id, user_id, payload_config, thread_id) "
                "VALUES (1, 10, '{\"ThreadId\":\"thread-1\"}', 'thread-1')"
            )
        )
        conn.execute(
            text(
                "CREATE UNIQUE INDEX uq_task_user_thread_id ON check_in_tasks (user_id, thread_id)"
            )
        )
        conn.commit()

        apply_task_thread_id(conn)

        indexes = {row[1] for row in conn.execute(text("PRAGMA index_list(check_in_tasks)"))}

    assert "uq_task_user_thread_id" in indexes
    assert "ix_task_user_thread_id_unique" not in indexes


@pytest.mark.asyncio
async def test_lifespan_runs_migrations_before_scheduler(monkeypatch) -> None:
    from backend import main as backend_main
    from backend.services import scheduler_service

    order: list[str] = []

    def fake_init_db() -> None:
        order.append("init_db")

    def fake_run_pending_migrations() -> SimpleNamespace:
        order.append("migrations")
        return SimpleNamespace(applied=("001_test",), skipped=())

    def fake_start_scheduler() -> None:
        order.append("scheduler")

    monkeypatch.setattr(backend_main, "init_db", fake_init_db)
    monkeypatch.setattr(backend_main, "run_pending_migrations", fake_run_pending_migrations)
    monkeypatch.setattr(scheduler_service, "start_scheduler", fake_start_scheduler)

    async with backend_main.lifespan(object()):
        pass

    assert order == ["init_db", "migrations", "scheduler"]


@pytest.mark.asyncio
async def test_lifespan_does_not_start_scheduler_when_migration_fails(monkeypatch) -> None:
    from backend import main as backend_main
    from backend.services import scheduler_service

    order: list[str] = []

    def fake_init_db() -> None:
        order.append("init_db")

    def fake_run_pending_migrations() -> None:
        order.append("migrations")
        raise RuntimeError("migration failed")

    def fake_start_scheduler() -> None:
        order.append("scheduler")

    monkeypatch.setattr(backend_main, "init_db", fake_init_db)
    monkeypatch.setattr(backend_main, "run_pending_migrations", fake_run_pending_migrations)
    monkeypatch.setattr(scheduler_service, "start_scheduler", fake_start_scheduler)

    with pytest.raises(RuntimeError, match="migration failed"):
        async with backend_main.lifespan(object()):
            pass

    assert order == ["init_db", "migrations"]
