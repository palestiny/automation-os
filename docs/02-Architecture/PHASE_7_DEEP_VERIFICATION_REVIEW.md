# Phase 7 — Deep Verification and Hardening Review

## Status

**Hardening verification: IN PROGRESS**

Phase 7 remains the completed selected capability. This review verifies the implemented Phase 7 contract against its Design Gate and Exit Review without activating a new capability.

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
| End-to-end concurrent duplicate start | GAP | There is a race window after reservation and before execution persistence: a concurrent duplicate can observe the idempotency record while its execution is not yet persisted and receive the missing-execution error. This requires an explicit concurrency/transaction design decision before claiming the full duplicate contract is hardened. |
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
| Exit Review consistency | PASS with GAP | The original Exit Review remains historically valid for the merged Phase 7 implementation, but this hardening review found an additional concurrency gap that was not proven by the original exit evidence. |
| Full GitHub Actions verification | PASS | Master run #938 for merge commit b23ee7eddcb8172791ee555638d510a219fb9523 completed successfully: 469 tests passed. |

## Real fixes completed during hardening

1. Fixed InMemoryExecutionHistoryRepository.append() so a new event must use the next contiguous sequence number. The previous implementation returned before enforcing this rule.
2. Corrected the orphan-idempotency regression fixture to use the repository's actual reservation contract.
3. Added idempotency regression coverage for normalization, lookup failure, reserve failure, partial history failure, duplicate replay after lifecycle changes, and concurrent reservation claims.
4. Corrected an existing retry-and-execute API regression test that used an unregistered capability and expected running even though successful execution completes the workflow. The corrected test registers the capability and expects completed.

## Remaining GAP

The remaining issue is specifically end-to-end concurrent duplicate-start coordination.

Current sequence:

1. Request A creates execution A.
2. Request A reserves the idempotency key for execution A.
3. Before A persists execution A, request B sees the existing reservation.
4. B looks up execution A.
5. If A has not persisted it yet, B receives the missing-execution error.

The repository-level reservation is atomic, but the application-level duplicate contract is not fully atomic across reservation + execution persistence.

## Decision boundary

Closing this GAP requires choosing a coordination model for the idempotency boundary. It should not be silently solved with arbitrary polling or a second lifecycle authority.

Possible designs to evaluate in a dedicated decision:

- transactional reservation + execution persistence;
- explicit pending/resolved idempotency reservation state with wait/claim semantics;
- another persistence-level atomic coordination mechanism.

The choice must preserve:
- one execution per successfully registered key;
- deterministic duplicate behavior;
- no orphan success;
- no second execution lifecycle;
- current Execution authority;
- persistence abstraction without vendor leakage.

Until this decision is made and implemented, Phase 7 should be described as completed but not fully hardened/verified for concurrent end-to-end duplicate starts.

## Verification conclusion

Phase 7 functional scope: verified.

Phase 7 hardening status: blocked by one real concurrency GAP.

Therefore:
- do not activate a new major capability yet;
- do not declare Phase 7 fully hardened;
- do not select or infer Phase 8;
- resolve the concurrency design boundary first.
