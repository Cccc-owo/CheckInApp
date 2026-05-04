from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

SCRIPT_PATH = (
    Path(__file__).resolve().parents[1] / "apps" / "backend" / "scripts" / "run_migrations.py"
)
SCRIPT_SPEC = importlib.util.spec_from_file_location("backend.scripts.run_migrations", SCRIPT_PATH)
assert SCRIPT_SPEC is not None and SCRIPT_SPEC.loader is not None
run_migrations = importlib.util.module_from_spec(SCRIPT_SPEC)
SCRIPT_SPEC.loader.exec_module(run_migrations)


def test_run_migrations_initializes_database_before_running_pending_migrations() -> None:
    calls: list[str] = []

    def fake_init_db() -> None:
        calls.append("init_db")

    def fake_run_pending_migrations():
        calls.append("run_pending_migrations")
        return SimpleNamespace(applied=("001",), skipped=())

    with (
        patch.object(run_migrations, "init_db", side_effect=fake_init_db),
        patch.object(
            run_migrations, "run_pending_migrations", side_effect=fake_run_pending_migrations
        ),
    ):
        exit_code = run_migrations.main()

    assert exit_code == 0
    assert calls == ["init_db", "run_pending_migrations"]
