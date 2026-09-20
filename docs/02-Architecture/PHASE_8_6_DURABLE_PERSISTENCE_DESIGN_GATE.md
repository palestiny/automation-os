# Phase 8.6 — Durable Persistence Design Gate

## Status

**Decision Accepted — PostgreSQL + explicit SQL repository adapters**

## Purpose

Replace the current in-memory persistence limitation with a durable persistence boundary while preserving the existing domain and application contracts.

## Repository Evidence

The repository already defines explicit persistence-facing contracts for Workflow, Execution, workflow-start idempotency, atomic execution start, and append-only execution history. Current adapters are in-memory. The atomic start adapter uses a process-local lock, which cannot provide the same guarantee across application processes or instances.

## Goal

Provide a durable adapter that preserves:
- workflow persistence;
- execution persistence;
- workflow-start idempotency;
- atomic idempotent execution creation;
- append-only execution history;
- restart survival;
- concurrent requests across application processes.

## Committed Constraints

1. Domain entities remain database-vendor independent.
2. Application use cases depend on repository contracts, not concrete persistence technology.
3. Execution remains the lifecycle authority.
4. Durable persistence must not introduce a second lifecycle/state model.
5. Idempotency must use a durable transaction/constraint or equivalent atomic primitive, not an application-process lock.
6. History remains append-only evidence, not lifecycle authority.
7. Existing in-memory adapters remain valid test adapters.
8. No workflow recovery engine, versioning, authorization, or multi-tenancy is added here.

## Options

### Option A — SQLite + explicit SQL repositories
Minimal infrastructure, local durability, and transactions; weaker multi-process deployment/scaling characteristics.

### Option B — PostgreSQL + explicit SQL repositories
Strong transactional/concurrency primitives and a clear production path; requires database deployment, driver, configuration, and migration strategy.

### Option C — SQLAlchemy-based persistence adapter
Mature transaction/session tooling and database abstraction; adds mapping/ORM complexity and still requires an actual production database decision.

## Decision Required

The Project Owner selected **Option B — PostgreSQL + explicit SQL repository adapters**. GREEN implementation may proceed within the committed constraints below.

The key architectural decision is:

**Which durable transaction boundary will own atomic workflow-start idempotency?**

### Accepted Decision

The Project Owner accepted PostgreSQL with explicit repository adapters and explicit transaction boundaries. The durable transaction boundary for workflow-start idempotency is owned by the PostgreSQL-backed `ExecutionStartRepository` adapter; uniqueness is enforced by a database constraint and execution/idempotency writes occur in one database transaction.

## TDD RED Plan

1. Data survives repository recreation.
2. Workflow save/get works durably.
3. Execution save/get works durably.
4. Idempotency records survive recreation.
5. Concurrent same-key starts produce one execution.
6. Same key for a different workflow is rejected.
7. Execution history is append-only and ordered.
8. Failed durable writes do not leave an invalid idempotency record.
9. Existing application behavior remains unchanged when the durable adapter is substituted.

## GREEN Scope

Implement only the selected durable adapter and the minimum schema/transaction infrastructure required by the repository contracts.

## Exit Criteria

- Design Gate decision accepted.
- RED tests exist.
- Durable repositories reach GREEN.
- Atomic idempotent start is verified under concurrency.
- History survives restart.
- Focused persistence tests pass.
- Full regression passes.
- Documentation and exit review are updated.

## Deferred

Execution recovery, workflow versioning, provider marketplace persistence beyond concrete needs, multi-tenancy, authorization, distributed worker infrastructure, HA/replication operations, and backup/restore runbooks.
