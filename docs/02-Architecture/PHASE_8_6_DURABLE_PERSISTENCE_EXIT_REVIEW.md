# Phase 8.6 Exit Review — Durable Persistence

Status: **COMPLETED — PostgreSQL implementation merged and CI verified**

## Decision

The Project Owner selected **Option B — PostgreSQL + explicit SQL repository adapters**.

The durable transaction boundary for workflow-start idempotency is the PostgreSQL-backed ExecutionStartRepository. A database uniqueness constraint on the idempotency key protects the invariant, while idempotency registration, execution persistence, and lifecycle history are committed atomically.

## Delivered

- PostgreSQL workflow persistence.
- PostgreSQL execution persistence.
- PostgreSQL workflow-start idempotency persistence.
- PostgreSQL atomic execution-start repository.
- PostgreSQL append-only execution history.
- Restart-survival coverage.
- Concurrent same-key workflow-start coverage.
- Different-workflow reuse rejection for the same idempotency key.
- Rollback coverage proving a failed atomic start does not leave an orphaned idempotency record.
- Timestamp normalization at the infrastructure/domain boundary.
- PostgreSQL schema bootstrap for the Phase 8.6 persistence contract.
- Application composition that selects PostgreSQL when AUTOMATION_OS_DATABASE_URL is configured while retaining in-memory adapters for tests and environments without durable configuration.
- GitHub Actions PostgreSQL service for the persistence test suite.

## Verification

Pull request **#240** was merged after the final CI run passed.

Final branch CI:
- Run #1071 — success.
- **494 tests passed**.

The implementation required three corrective iterations identified by CI:
1. PostgreSQL timezone-aware timestamps were normalized to the domain's naive UTC datetime contract.
2. Execution history persistence was tightened to preserve append-only/idempotent behavior.
3. PostgreSQL row-factory handling was corrected for aggregate/history queries.

## Architectural Boundary

The domain and application layers remain database-vendor independent.

The PostgreSQL adapter owns:
- SQL schema interaction;
- database transactions;
- uniqueness enforcement;
- connection creation;
- persistence serialization/deserialization.

The execution lifecycle remains owned by Execution; history remains evidence and does not become a second lifecycle authority.

## Deferred

- Execution recovery engine.
- Workflow versioning.
- Multi-tenancy and authorization.
- Distributed workers and queues.
- HA/replication operations.
- Backup/restore runbooks.
- Provider marketplace persistence beyond concrete Phase 8.6 needs.
- Generic migration tooling beyond the current Phase 8.6 schema bootstrap.

## Next Capability

**Phase 8.7 — Execution Recovery**, subject to its own Design Gate.
