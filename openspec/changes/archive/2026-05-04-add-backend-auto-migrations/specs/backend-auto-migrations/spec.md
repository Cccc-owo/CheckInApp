## ADDED Requirements

### Requirement: Ordered backend migration registry
The backend SHALL define a deterministic registry of database migrations with stable identifiers and execution order.

#### Scenario: Registry order is stable
- **WHEN** the migration runner loads available migrations
- **THEN** it SHALL evaluate them in the registered order using stable migration identifiers.

#### Scenario: Existing migrations are registered
- **WHEN** the backend migration registry is built
- **THEN** it SHALL include migrations for the existing account-lockout fields and task thread ID schema changes.

### Requirement: Applied migration tracking
The backend SHALL store applied migration records in the application database and use those records to skip completed migrations.

#### Scenario: Migration metadata is initialized
- **WHEN** the migration runner starts against a database without migration metadata
- **THEN** it SHALL create the migration metadata table before checking pending migrations.

#### Scenario: Pending migration is marked after success
- **WHEN** a pending migration completes successfully
- **THEN** the backend SHALL record that migration as applied with its stable identifier and applied timestamp.

#### Scenario: Completed migration is skipped
- **WHEN** a migration identifier is already present in the applied migration metadata
- **THEN** the backend SHALL skip that migration instead of executing it again.

#### Scenario: Failed migration is not marked
- **WHEN** a migration fails during execution
- **THEN** the backend SHALL NOT record that migration as applied.

### Requirement: Automatic startup migration execution
The backend SHALL run pending database migrations automatically during API startup before runtime background work begins.

#### Scenario: Startup applies migrations before scheduler
- **WHEN** the FastAPI lifespan startup runs
- **THEN** it SHALL initialize base database tables, run pending migrations, and only then start the scheduler.

#### Scenario: Startup stops on migration failure
- **WHEN** any pending migration fails during startup
- **THEN** the backend SHALL fail startup and SHALL NOT start the scheduler.

#### Scenario: Startup logs migration activity
- **WHEN** startup migration execution runs
- **THEN** the backend SHALL log whether migrations were applied, skipped, or failed with the relevant migration identifier.

### Requirement: Manual migration execution
The backend SHALL provide a manual command path that runs the same registered migrations used by automatic startup.

#### Scenario: Operator runs migrations manually
- **WHEN** an operator executes the documented backend migration command
- **THEN** the command SHALL apply pending registered migrations and skip already-applied migrations.

#### Scenario: Manual failure exits unsuccessfully
- **WHEN** a migration fails during manual execution
- **THEN** the command SHALL exit unsuccessfully after reporting the failing migration.

### Requirement: Existing migration behavior is preserved
The backend SHALL preserve the behavior of existing schema changes when they move into the automatic migration path.

#### Scenario: Account lockout fields are added
- **WHEN** the account-lockout migration runs against a database missing its fields
- **THEN** it SHALL add `failed_login_attempts`, `locked_until`, and `last_failed_login` to the users table.

#### Scenario: Task thread identity is backfilled
- **WHEN** the task thread ID migration runs against valid existing task payloads
- **THEN** it SHALL add or maintain `check_in_tasks.thread_id`, backfill it from `payload_config.ThreadId`, and ensure the per-user thread ID uniqueness index exists.

#### Scenario: Invalid legacy task payload blocks migration
- **WHEN** the task thread ID migration finds missing or duplicate `ThreadId` values that would make the schema invalid
- **THEN** it SHALL fail with a clear validation error instead of silently creating inconsistent task identity data.
