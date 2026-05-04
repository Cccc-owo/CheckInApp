## Context

The backend boot path currently creates tables with `Base.metadata.create_all(bind=engine)` and then starts runtime services. Two schema evolution scripts already live under `apps/backend/scripts/`, but they must be run manually and are not coordinated with service startup. That means a fresh or upgraded database can drift out of sync until an operator remembers to run the right script.

This change is scoped to the current backend stack and its SQLite-first runtime behavior. It should improve deployment safety without introducing a full migration framework or changing the database access layer.

## Goals / Non-Goals

**Goals:**

- Apply pending backend schema migrations automatically before the service becomes ready.
- Keep an explicit record of applied migrations in the database.
- Preserve a manual command for running migrations outside normal startup.
- Reuse the existing migration logic for account lockout and task thread ID rather than duplicating it.
- Fail fast if migration execution fails.

**Non-Goals:**

- Introducing Alembic or database-version autogeneration.
- Designing a generic cross-project migration framework.
- Changing business API behavior beyond startup readiness and migration execution.
- Reworking unrelated schema definitions that are not part of the existing manual migrations.

## Decisions

### 1. Add a small migration runner with a metadata table

Create a backend migration module that owns a fixed ordered registry of migration entries. Each entry should have a stable identifier, a short description, and a callable that receives a database connection or session-bound connection. The runner should create and consult a `schema_migrations` table before executing anything.

Why this over relying on ad hoc script execution: the database itself becomes the source of truth for what has already been applied, so startup and manual execution use the same contract. This is lighter than Alembic and better aligned with the current hand-written SQL style.

Alternatives considered:

- Keep only standalone scripts. Rejected because there is no durable applied-state record and startup cannot know whether a migration still needs to run.
- Adopt Alembic now. Rejected because it is larger than the current need and would require a broader migration model than the repo currently uses.

### 2. Run migrations during startup before the scheduler starts

Move the migration runner into the FastAPI lifespan startup path after the database base tables are ensured and before `start_scheduler()` is called.

Why this order: the app should not begin processing scheduled work against a partially migrated database. Running before the scheduler also keeps the failure surface small and makes startup failures explicit.

Alternatives considered:

- Run migrations lazily on first request. Rejected because it defers failure until user traffic arrives and allows the scheduler to start against the wrong schema.
- Run migrations after the scheduler starts. Rejected because scheduler jobs may read or write schema fields that are not yet present.

### 3. Keep the existing scripts as thin wrappers or registered migration implementations

The existing `migrate_add_account_lockout.py` and `migrate_add_task_thread_id.py` logic should be reused through the registry rather than remaining as separate one-off flows. A manual runner entrypoint can call the same registry used at startup.

Why this choice: it avoids duplicate migration behavior and keeps the manual/operator path and the automatic path consistent.

Alternatives considered:

- Rewrite the scripts into a new CLI-only tool and leave startup separate. Rejected because the automatic path would still need a second implementation.
- Delete the scripts entirely. Rejected because operators still need a manual escape hatch and the scripts already document the schema history.

### 4. Treat migration failure as a startup blocker

If any migration raises, the runner should stop immediately and surface the failing migration ID and error. A migration should only be marked applied after its work succeeds.

Why this choice: schema drift is a correctness problem, not a recoverable warning. Marking failure as applied would hide a broken database state and make recovery harder.

### 5. Keep migrations idempotent and validation-first where needed

The runner should skip already-applied migrations based on metadata. Individual migration functions should still check the current schema when they need to perform safe DDL or data backfills, because SQLite DDL and older databases can require defensive inspection.

Why this choice: metadata protects the common case, but some migrations already need schema checks and data validation before altering tables or creating indexes.

## Risks / Trade-offs

- [Risk] Manual SQL migrations can still be database-specific and brittle. → Mitigation: keep the registry small, ordered, and explicit; avoid pretending this is a generic migration framework.
- [Risk] Startup failures may block the entire service when a migration encounters bad legacy data. → Mitigation: fail fast by design, surface the failing migration clearly, and keep validation in the migration itself so operators can fix the data before retrying.
- [Risk] SQLite DDL behavior can make transactional guarantees uneven. → Mitigation: use metadata updates only after successful execution and keep migration steps idempotent so reruns are safe.
- [Risk] The manual scripts and the registry could drift apart. → Mitigation: make the scripts call the shared migration functions or runner so there is one source of truth.

## Migration Plan

1. Add the migration metadata table and runner module.
2. Register the two existing migrations in execution order.
3. Wire the runner into backend startup before the scheduler begins.
4. Add a manual CLI entrypoint that invokes the same runner.
5. Add tests for first-run execution, repeat-run skipping, failure handling, and startup ordering.
6. Update the developer/deployment notes to mention automatic startup migrations and the manual command.

Rollback strategy:

- If a migration blocks startup, fix the underlying migration or data issue and rerun startup or the manual command.
- Because applied migrations are tracked explicitly, repeated runs should remain safe once the issue is resolved.

## Open Questions

- Should the manual runner live as a dedicated `backend.scripts.run_migrations` module, or should the startup helper be the only public entrypoint and scripts import it directly?
- Should migration IDs be semantic strings based on the change name, or timestamp-prefixed identifiers to make ordering obvious?
