# Workflow Start Architecture Consistency Review

## Scope

This review covers the four architecture review items recorded in `PROJECT_STATUS.md` after workflow generation, workflow versioning, and workflow-start idempotency hardening.

Review principle:

`UNDERSTAND → MAP → DESIGN → TRADE-OFFS → DECIDE → VERIFY → DOCUMENT`

No production behavior is changed by this review.

## 1. Idempotency Repository vs Execution Start Repository

### Observed design

`StartWorkflowExecution` receives both boundaries when idempotency is requested:

- `ExecutionIdempotencyRepository`: generic key/record persistence API.
- `ExecutionStartRepository`: atomic workflow-start boundary that coordinates idempotency registration with execution persistence.

The current start use case uses `ExecutionIdempotencyRepository` as a required configuration guard, while actual replay lookup and atomic creation use `ExecutionStartRepository`.

The in-memory implementation composes the two repositories. The PostgreSQL implementation also exposes both, while `PostgresExecutionStartRepository` owns the transactional start operation.

### Trade-offs

**Keep both boundaries**
- Preserves compatibility with existing repository contracts and adapters.
- Makes the generic idempotency record concept independently reusable.
- Keeps the atomic start boundary explicit.

**Remove the idempotency dependency**
- Reduces constructor coupling.
- Better expresses that atomic start is the real runtime requirement.
- Would require contract, adapter, composition, and test migration.

### Decision

**KEEP for now; DOCUMENT the relationship.**

The two interfaces are not treated as equivalent responsibilities. `ExecutionIdempotencyRepository` remains the persistence contract for idempotency records, while `ExecutionStartRepository` is the runtime atomicity boundary. No refactor is justified until actual production composition demonstrates that the generic repository contract is no longer needed.

## 2. Replay With a Different Explicit Workflow Version

### Observed behavior

For an idempotent start, the existing idempotency association is checked before workflow/version resolution.

Therefore, if key `K` originally created an execution using version 1, replaying `K` while explicitly supplying version 2 returns the original execution and version 1. No second execution is created.

This behavior is now regression-tested in `tests/test_workflow_start_idempotency.py`.

### Decision

**KEEP and DOCUMENT current replay semantics.**

An idempotency key represents the original start request's identity. Reuse of the key is a replay, not a new version-selection request. The first persisted execution remains authoritative.

A future API may choose to reject mismatched replay parameters, but that would be a new contract and requires a separate design decision.

## 3. Legacy First-Start Version Materialization

### Observed behavior

When workflow-version persistence is configured but a workflow has no published version, the start use case creates workflow version 1, publishes it, and persists it with `save_if_absent`.

### Trade-off

Removing this fallback would make publication/version creation fully explicit but could break compatibility with legacy persisted workflows that predate workflow versioning.

### Decision

**KEEP as a backward-compatibility path.**

It must remain clearly distinguished from the normal explicit publication boundary. It is not an AI-generation shortcut and does not permit starting a DRAFT workflow.

Removal or redesign requires a dedicated migration/compatibility decision.

## 4. Durable Atomic Idempotency + Execution Persistence

### Verified PostgreSQL behavior

`PostgresExecutionStartRepository.save_idempotent()` performs idempotency registration and execution persistence inside one PostgreSQL transaction.

If the idempotency key is newly registered, the execution and its lifecycle events are persisted in the same transaction. If the key already exists, the existing association is returned without creating another execution.

The in-memory implementation uses a lock to provide atomicity for the test/runtime adapter; this must not be interpreted as durable transaction semantics.

### Decision

**KEEP the Phase 7 atomic-start contract.**

Every future durable adapter must provide an equivalent transactional or otherwise durable atomic guarantee. Adapter-specific verification remains required.

## Review Outcome

| Item | Outcome | Production change |
|---|---|---|
| Idempotency vs execution-start repositories | KEEP + DOCUMENT | None |
| Version-mismatched idempotent replay | KEEP + DOCUMENT | None |
| Legacy first-start version materialization | KEEP for compatibility | None |
| Durable atomic start | KEEP contract + VERIFY PostgreSQL | None |

## Exit Criteria

- Current master behavior is characterized by regression tests.
- PostgreSQL atomic-start implementation is inspected and verified at source level.
- No production architecture change is introduced without a separate Design Gate.
- Project status records the review outcome and current verification checkpoint.
