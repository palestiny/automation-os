# Phase 7 Idempotency Concurrency Decision

## Status

**OPEN — Project Owner decision required**

Phase 7 functional implementation is complete, but deep hardening identified a real end-to-end concurrency gap in workflow-start idempotency.

The gap is covered by PR #228 and reproduced by GitHub Actions run #941:

- 470 tests passed
- 1 test failed
- failing scenario: a duplicate request observes an idempotency reservation before the first request has persisted its execution
- current behavior raises `RuntimeError("Idempotency record references a missing execution")`

Production behavior is intentionally not changed until the coordination design is selected.

## Problem

The current start sequence is conceptually:

1. normalize the idempotency key;
2. check for an existing record;
3. load the published workflow;
4. create an execution;
5. reserve the idempotency key;
6. start the execution;
7. persist the execution;
8. return the execution.

The idempotency repository reservation is atomic, but the reservation and execution persistence are not one atomic operation.

A concurrent duplicate can therefore observe:

- an existing idempotency record;
- a referenced execution that is not yet persisted.

This violates the intended duplicate-request contract.

## Verified current architecture

The current implementation has three separate persistence boundaries:

- `ExecutionRepository` persists the authoritative `Execution` aggregate.
- `ExecutionIdempotencyRepository` owns key reservation/release and currently uses a lock in the in-memory adapter.
- `ExecutionHistoryRepository` stores append-only lifecycle evidence through `EventRecordingExecutionRepository`.

The application use case coordinates these repositories sequentially. There is currently no transaction/session/unit-of-work abstraction spanning idempotency and execution persistence.

The current in-memory execution store itself does not provide a cross-repository atomic boundary. Therefore, adding another lock around only the idempotency repository would not establish the required end-to-end invariant.

The existing history decorator intentionally saves the execution before appending history. This ordering must remain compatible with Phase 7's established failure semantics: execution remains authoritative and evidence failure is surfaced.

## Required invariants

Any selected design must preserve:

1. one successfully registered key maps to one execution;
2. concurrent duplicates deterministically resolve to that execution;
3. the same key used for a different workflow remains a conflict;
4. a successful idempotency record cannot remain orphaned;
5. execution remains the sole lifecycle authority;
6. persistence failures remain explicit;
7. no polling or retry loop merely hides the race;
8. the design remains compatible with the project's persistence boundaries;
9. the solution must define what happens when coordination succeeds but a later operational-evidence write fails;
10. the in-memory adapter must model the selected contract rather than introduce weaker test-only semantics.

## Options

### A — Atomic reservation + execution persistence

Coordinate idempotency registration and execution persistence inside one atomic persistence boundary.

**Advantages**

- strongest consistency model;
- duplicate requests cannot observe an intermediate reservation;
- semantics are straightforward once the persistence boundary supports the operation;
- directly matches the required invariant across the two currently separate repositories.

**Costs / implications**

- may require evolving repository interfaces;
- durable persistence adapters may need transaction or equivalent atomic support;
- the application use case may need a transaction/unit-of-work boundary;
- in-memory behavior should model the same contract rather than create a special case;
- interaction with history persistence must be explicitly defined because history currently follows execution persistence.

### B — Pending / Resolved idempotency state

Make idempotency records explicitly represent an in-progress reservation and a resolved execution.

A duplicate encountering a pending record follows a defined resolution protocol rather than treating the record as immediately replayable.

**Advantages**

- explicit representation of the intermediate state;
- can work where transactionally atomic persistence is unavailable;
- keeps the current basic separation between idempotency and execution repositories.

**Costs / implications**

- introduces additional state and coordination semantics;
- requires defined timeout/stuck-reservation behavior;
- duplicate request behavior becomes more complex;
- the pending record becomes another coordination state that must not become a second execution lifecycle authority;
- failure recovery semantics become a first-class part of the idempotency contract.

### C — Persistence-level compare/claim coordination

Keep the conceptual idempotency model but introduce a persistence operation that atomically claims/resolves the key together with the persisted execution.

**Advantages**

- can keep the domain contract focused while placing coordination in the persistence adapter;
- can be adapted to different storage capabilities;
- may avoid exposing transaction details to the application/domain layer.

**Costs / implications**

- exact guarantees depend on the adapter;
- repository contracts become more specialized;
- durable implementations must provide equivalent atomic semantics;
- the application contract must still define what a duplicate observes during and after the atomic operation;
- adapter-specific capabilities must not leak into the domain model.

## Decision comparison against current architecture

| Concern | A — Atomic boundary | B — Pending/Resolved | C — Adapter claim |
|---|---|---|---|
| Eliminates observed reservation-before-save race | Directly | Through resolution protocol | Directly if atomic claim is real |
| Requires new coordination semantics | Moderate | High | Moderate |
| Requires explicit stuck-operation policy | No separate pending state | Yes | Depends on adapter |
| Fits current separate repositories | Requires coordination boundary | More naturally | Requires specialized adapter operation |
| Risk of second coordination state | Low | Highest | Low–moderate |
| Durable persistence implications | Transaction/equivalent boundary | Pending-state durability/recovery | Adapter-specific atomic primitive |
| Test adapter must model | Atomic boundary | Pending lifecycle | Atomic claim |
| Main unresolved design question | Where transaction boundary lives | How pending resolves safely | What atomic primitive every adapter guarantees |

This comparison is architectural analysis only. It does **not** select an option.

## Decision boundary

Do not implement A, B, or C implicitly.

The Project Owner must select the coordination model before production behavior is changed.

After selection:

1. record the rationale and trade-offs;
2. update the Phase 7 Design Gate / hardening review as appropriate;
3. implement RED → GREEN;
4. verify concurrent duplicates, partial failures, key conflicts, and persistence failures;
5. run the full regression suite;
6. update `PROJECT_STATUS.md` and the Phase 7 exit/hardening documentation;
7. only then consider the Post-Phase-7 Design Gate for the next capability.

## Current project state

No Phase 8 capability is selected or committed.

PR #228 remains intentionally unmerged because it is RED evidence for this decision boundary.
