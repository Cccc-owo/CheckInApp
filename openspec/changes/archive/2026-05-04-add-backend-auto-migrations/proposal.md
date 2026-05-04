## Why

The backend currently relies on `Base.metadata.create_all()` plus manually executed SQL scripts, so existing databases do not reliably receive schema changes during deployment or restart. This is risky now because recent backend changes already added schema evolution scripts that are easy to forget before the scheduler starts using the database.

## What Changes

- Add a lightweight backend migration capability that tracks applied migrations in the database and runs pending migrations in deterministic order.
- Run backend migrations automatically during FastAPI startup after base table creation and before the scheduler starts.
- Preserve a manual migration entrypoint for operators and developers who want to apply or inspect migrations outside normal service startup.
- Adapt the existing account-lockout and task-thread-id migration scripts into the registered migration path while keeping them safe to skip after they have already run.
- Fail startup clearly when a migration fails, and never mark a failed migration as applied.
- Do not add Alembic or a broad migration framework in this change.

## Capabilities

### New Capabilities

- `backend-auto-migrations`: automatic and manual execution contract for ordered backend database migrations.

### Modified Capabilities

None.

## Impact

- Affected backend startup path: `apps/backend/main.py`.
- Affected database code: `apps/backend/models/database.py` and a new backend migration module or service.
- Affected scripts: existing migration scripts under `apps/backend/scripts/` plus a consolidated manual runner.
- Affected tests: backend migration runner tests and startup-order coverage.
- Affected documentation: developer/deployment guidance for automatic migrations and the manual migration command.
