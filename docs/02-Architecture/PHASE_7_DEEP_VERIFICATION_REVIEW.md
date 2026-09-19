# Phase 7 — Deep Verification and Hardening Review

## Status

**HARDENING VERIFIED**

Phase 7 remains the completed selected capability. This review verifies the implemented Phase 7 contract against its Design Gate and Exit Review, including the previously identified end-to-end concurrent duplicate-start gap.

## Verification matrix

| Area | Result | Evidence / finding |
|---|---|---|
| Workflow-start idempotency | PASS | Same key + same workflow replays the same execution; duplicate does not increase execution count. |
| Key normalization | PASS | Whitespace is stripped before lookup/reservation; equivalent normalized keys replay the same execution. |
| Key conflict | PASS | Same key for a different workflow returns a conflict and does not create a second execution. |
| No-key behavior | PASS | Requests without a key remain non-idempotent. |
| Idempotency lookup failure | PASS | Failure is surfaced before execution creation. |
| Idempotency reserve failure | PASS | Failure is surfaced and no execution is persisted. |
| Execution-save failure | PASS | Reservation is released when the execution was not persisted. |
| Partial persistence / history failure | PASS | Execution remains authoritative, failure is surfaced, and a later duplicate replays the persisted execution rather than creating another one. |
| Atomic reservation claims | PASS | Concurrent repository-level claims for one key produce exactly one reservation owner. |
| End-to-end concurrent duplicate start | PASS | The selected Option A atomic execution-start boundary prevents a duplicate from observing an idempotency registration before its execution is persisted. The GREEN regression verifies the duplicate waits for the first coordinated save and then resolves to the same execution. |
| Execution lifecycle evidence | PASS | Start, step completion, wait, resume, completion, failure, retry, retry-start, and cancellation are represented by domain events. |
| Retry evidence | PASS | Cross-attempt event ordering and attempt numbers are covered by regression tests. |
| Resume/cancel evidence | PASS | Lifecycle evidence is covered by regression tests. |
| History ordering | PASS | A real adapter bug allowing non-contiguous sequence insertion was found and fixed; repeated identical saves remain idempotent. |
| Conflicting history sequence | PASS | Conflicting events at an existing sequence are rejected. |
| History persistence failure | PASS | Evidence failure is surfaced and does not create a second lifecycle authority. |
| Second state authority | PASS | Execution remains the lifecycle authority; history is append-only observational evidence. |
| API success/duplicate replay | PASS | Workflow start returns 200 and duplicate replay returns 200 with the same execution representation. |
| API key conflict | PASS | Reuse of a key for another workflow returns 409. |
| API unknown workflow | PASS | Unknown workflow returns 404. |
| API draft workflow | PASS | Non-published workflow start returns 409. |
| API without key | PASS | Existing non-idempotent behavior remains covered. |
| API persistence failure | PASS | Operational idempotency persistence failure is surfaced as HTTP 500 rather than swallowed. |
| Design Gate boundary | PASS | No ownership, autonomous planning, product/API foundation, cross-command idempotency, durable DB, generic event bus, or tracing capability was activated. |
| Exit Review consistency | PASS | The original Exit Review remains historically valid for the merged Phase 7 implementation; the later concurrency gap was resolved through the selected hardening decision and equivalent GREEN regression. |
| GitHub Actions verification | PASS | PR #232 run #969 completed successfully with **470 tests passed**. |

## Real fixes completed during hardening

1. Fixed `InMemoryExecutionHistoryRepository.append()` so a new event must use the next contiguous sequence number. The previous implementation returned before enforcing this rule.
2. Corrected the orphan-idempotency regression fixture to use the repository's actual reservation contract.
3. Added idempotency regression coverage for normalization, lookup failure, reserve failure, partial history failure, duplicate replay after lifecycle changes, and concurrent reservation claims.
4. Corrected an existing retry-and-execute API regression test that used an unregistered capability and expected running even though successful execution completes the workflow.
5. Selected and implemented Option A for end-to-end concurrent duplicate-start coordination.
6. Added an explicit `ExecutionStartRepository` boundary so idempotency registration and execution persistence are coordinated as one operation for the current in-memory adapter.
7. Added a GREEN concurrent duplicate-start regression proving that a duplicate cannot observe a registered key before the first execution is persisted.

## Resolved concurrency gap

The previously observed sequence was:

1. Request A creates execution A.
2. Request A reserves the idempotency key for execution A.
3. Before A persists execution A, request B sees the existing reservation.
4. B looks up execution A.
5. If A has not persisted it yet, B receives the missing-execution error.

This gap is resolved in the selected in-memory implementation by coordinating reservation and execution persistence under the same atomic execution-start boundary. A duplicate lookup also uses that boundary, so it cannot pass through while the first coordinated save is in progress.

The implementation does **not** claim a generic durable database transaction. Durable adapters must provide an equivalent transaction or atomic persistence primitive before they are considered production-compatible with this contract.

## Decision

The Project Owner selected **Option A — Atomic reservation + execution persistence**.

The selected implementation preserves:

- one execution per successfully registered key;
- deterministic duplicate behavior;
- same-key/different-workflow conflict;
- no orphan idempotency success after pre-persistence failure;
- current Execution lifecycle authority;
- append-only history as downstream evidence;
- persistence abstraction without vendor-specific leakage;
- no polling or second lifecycle state.

## Verification conclusion

Phase 7 functional scope: **verified**.

Phase 7 hardening status: **verified for the current in-memory persistence model**.

Therefore:

- do not activate a new major capability automatically;
- do not infer or select Phase 8;
- proceed to the Post-Phase-7 Design Gate;
- require explicit Project Owner selection and an approved Design Gate before any future major capability enters implementation.
