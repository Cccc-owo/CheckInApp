## 1. Migration Runner Foundation

- [x] 1.1 Add a backend migration metadata table and helper utilities for reading and writing applied migration records.
- [x] 1.2 Implement a deterministic migration registry with stable identifiers and ordered execution.
- [x] 1.3 Extract the existing account-lockout and task-thread-id migration logic into shared callable migration units.
- [x] 1.4 Add a manual migration entrypoint that invokes the shared registry.

## 2. Startup Integration

- [x] 2.1 Wire the migration runner into backend FastAPI startup after base table creation and before scheduler startup.
- [x] 2.2 Make startup fail fast when a migration fails and ensure the scheduler does not start afterward.
- [x] 2.3 Add clear logs for applied, skipped, and failed migrations.

## 3. Verification and Documentation

- [x] 3.1 Add backend tests for first-run execution, repeat-run skipping, and failure-not-marked behavior.
- [x] 3.2 Add startup-order coverage to prove migrations run before the scheduler.
- [x] 3.3 Update developer/deployment documentation with automatic startup migration behavior and the manual migration command.
- [x] 3.4 Run the repository checks for backend code and OpenSpec validation before archiving or implementation handoff.
