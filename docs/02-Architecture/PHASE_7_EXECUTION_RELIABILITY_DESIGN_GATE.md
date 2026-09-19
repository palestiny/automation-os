# Phase 7 — Execution Reliability and Operational Visibility Design Gate

## Status

**Selected capability:** A — Execution Reliability and Operational Visibility

**Project Owner selection:** Approved

**Implementation status:** Design Gate finalized; implementation follows TDD RED → GREEN → Refactor → Verification.

## Problem

The execution engine currently owns lifecycle state and attempt count, but a caller cannot safely distinguish a repeated start command from a request to create a new execution. The platform also has no committed execution history contract and no minimal structured execution-event contract.

This milestone strengthens the existing execution boundary without introducing a second execution lifecycle authority.

## Goal

Make workflow execution start safely repeatable for an explicit idempotency boundary and make execution transitions diagnosable through bounded, append-only operational evidence.

## Committed scope

1. **Idempotency for workflow execution start**
   - The first idempotent command is `StartWorkflowExecution`, exposed through the workflow-start HTTP endpoint.
   - A caller may provide an idempotency key.
   - The key is scoped to the start operation and the target workflow.
   - A successful first request associates the key with the created execution.
   - A repeated request with the same key and equivalent workflow target returns the same execution rather than creating another execution.
   - Reuse of the same key for a different workflow is rejected as a conflict.
   - A request without an idempotency key retains current non-idempotent behavior.
   - The duplicate response replays the current execution representation; it does not create a second lifecycle.
   - Idempotency records are retained for the lifetime of the configured persistence store in this phase. No TTL/expiry policy is introduced until durable persistence requirements justify one.

2. **Execution history**
   - History is append-only.
   - Each entry records execution id, sequence number, operation/event name, resulting execution state, attempt, and timestamp.
   - History describes authoritative execution facts; it is not a second state model.
   - The current `Execution` aggregate remains the only lifecycle authority.
   - History is observational evidence of committed lifecycle changes, not an alternative source from which lifecycle state is reconstructed in this phase.

3. **Minimal structured execution events**
   - Events are limited to execution lifecycle facts needed by the history contract.
   - Initial event vocabulary is bounded to start, wait, resume, step completion, retry, failure, completion, and cancellation where those transitions already exist.
   - Events carry execution identity, workflow identity, sequence/order information, resulting state, attempt, and timestamp.
   - No generic event bus, external telemetry vendor, or analytics pipeline is introduced.

4. **Correlation**
   - Execution-related records use execution id and workflow id as the stable domain correlation identifiers.
   - A separate distributed trace/correlation infrastructure is explicitly out of scope.

5. **Failure semantics**
   - Execution lifecycle state is committed before operational evidence is considered successful.
   - Failure to persist history/event evidence must not create a second execution lifecycle or roll back a domain transition in this phase.
   - Such evidence failure must be surfaced to the application boundary as an operational persistence failure; silent swallowing is not permitted.
   - Idempotency registration must be durable enough for the active persistence boundary before a start result is exposed as successfully idempotent.
   - If the idempotency record cannot be persisted, the start command must fail rather than claim idempotency that cannot be honored.

## Non-goals

- A second execution state machine or lifecycle authority.
- Generic event bus infrastructure.
- Full distributed tracing.
- Vendor-specific observability integrations.
- Analytics dashboards or metrics products.
- Unbounded event storage.
- Idempotency for every API command.
- Idempotency TTL/expiry policy.
- Multi-user ownership or authorization.
- Autonomous planning, workflow generation, or AI ranking.
- Public API versioning unrelated to this command contract.
- Durable database implementation solely for this milestone.

## Design constraints

### Execution remains authoritative

All legal lifecycle transitions continue to be enforced by `Execution`. History and events cannot mutate execution state.

### Deterministic duplicate behavior

For the same idempotency key and workflow target, a duplicate start request resolves to the originally associated execution. The system must never create two executions for one successfully registered key.

### Key conflict behavior

A key already associated with workflow A cannot be reused for workflow B. This is a client contract error and must not mutate either execution.

### Ordering

History/event sequence ordering is local to an execution. The contract does not promise global ordering across executions.

### Persistence abstraction

Idempotency, history, and event storage are application/domain-facing contracts with in-memory adapters for the current repository. The design must not leak a storage vendor into the domain.

## TDD entry point

The first RED tests must prove:

1. First workflow-start request with an idempotency key creates one running execution and records the key.
2. Repeating the same request with the same key returns the original execution.
3. Repeating the same key for a different workflow is rejected.
4. A start request without a key preserves existing behavior.
5. Duplicate requests do not increment execution count.
6. The first successful start produces the expected execution history/event evidence.
7. Existing execution lifecycle behavior remains unchanged.

## Verification

Focused tests must run first, followed by the complete test suite.

The milestone cannot exit until:

- idempotency behavior is deterministic;
- duplicate start never creates a second execution;
- key conflicts are rejected;
- history is append-only and ordered per execution;
- event/history evidence cannot become a second lifecycle authority;
- existing lifecycle, retry, resume, cancel, scheduling, and API tests remain valid;
- failure behavior is covered;
- full CI/test verification passes.

## Exit review

The exit review must explicitly confirm:

- selected scope was implemented and no unrelated post-Phase-6 capability was activated;
- Execution remains the sole lifecycle authority;
- idempotency is bounded to workflow start;
- history/events are bounded and operationally useful;
- no generic infrastructure was introduced without a concrete need;
- documentation and tests match the implemented contract.

## Deferred after this gate

The following remain deferred:

- ownership and authorization;
- autonomous planning/workflow generation;
- generic product/API foundation;
- cross-command idempotency;
- durable production persistence decisions;
- full observability/tracing platform.

