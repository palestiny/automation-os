# Phase 7 Idempotency Concurrency Decision

## Status

**DECIDED — Option A selected by Project Owner; implementation verified**

Phase 7 functional implementation is complete. Deep hardening identified a real end-to-end concurrency gap in workflow-start idempotency, and the Project Owner selected Option A to resolve it.

The original RED proof is preserved by PR #228 and GitHub Actions run #941:

- 470 tests passed
- 1 test failed
- failing scenario: a duplicate request observes an idempotency reservation before the first request has persisted its execution
- original behavior raised `RuntimeError("Idempotency record references a missing execution")`

The selected Option A implementation was merged through PR #232. GitHub Actions run #969 completed successfully with **470 tests passed**, including the GREEN concurrent duplicate-start regression.

## Problem

The original start sequence was conceptually:

1. normalize the idempotency key;
2. check for an existing record;
3. load the published workflow;
4. create an execution;
5. reserve the idempotency key;
6. start the execution;
7. persist the execution;
8. return the execution.

The idempotency repository reservation was atomic, but the reservation and execution persistence were not one atomic operation.

A concurrent duplicate could therefore observe:

- an existing idempotency record;
- a referenced execution that was not yet persisted.

This violated the intended duplicate-request contract.

## Verified current architecture

The implementation now introduces an explicit `ExecutionStartRepository` boundary for idempotent workflow starts.

For the current in-memory adapter:

- `ExecutionRepository` persists the authoritative `Execution` aggregate.
- `ExecutionIdempotencyRepository` owns key reservation/release.
- `ExecutionStartRepository` coordinates idempotency registration and execution persistence under one lock.
- `ExecutionHistoryRepository` stores append-only lifecycle evidence through `EventRecordingExecutionRepository`.

Duplicate idempotency lookup also goes through the execution-start boundary, so a duplicate cannot pass through while the first coordinated persistence operation is in progress.

The existing history decorator continues to save the execution before appending history. Execution remains authoritative and evidence failure is surfaced.

## Required invariants

Any implementation of this contract must preserve:

1. one successfully registered key maps to one execution;
2. concurrent duplicates deterministically resolve to that execution;
3. the same key used for a different workflow remains a conflict;
4. a successful idempotency record cannot remain orphaned after pre-persistence failure;
5. execution remains the sole lifecycle authority;
6. persistence failures remain explicit;
7. no polling or retry loop merely hides the race;
8. the design remains compatible with the project's persistence boundaries;
9. later operational-evidence failure does not create a second lifecycle authority;
10. the in-memory adapter models the selected contract rather than introducing weaker test-only semantics.

## Options

### A — Atomic reservation + execution persistence

Coordinate idempotency registration and execution persistence inside one atomic persistence boundary.

**Advantages**

- strongest consistency model;
- duplicate requests cannot observe an intermediate reservation;
- semantics are straightforward once the persistence boundary supports the operation;
- directly matches the required invariant across the two previously separate repositories.

**Costs / implications**

- may require evolving repository interfaces;
- durable persistence adapters may need transaction or equivalent atomic support;
- the application use case may need a transaction/unit-of-work boundary;
- in-memory behavior should model the same contract rather than create a special case;
- interaction with history persistence must be explicitly defined because history follows execution persistence.

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

This comparison is architectural analysis only. The Project Owner has selected Option A.

## Decision

**Selected model: A — Atomic reservation + execution persistence.**

The Project Owner selected Option A because the required invariant is that a successfully registered idempotency key and its execution must become visible as one coordinated persistence operation. The implementation introduces an explicit execution-start persistence boundary rather than adding a pending idempotency state or a polling/retry protocol.

The in-memory adapter models the same boundary by serializing idempotency registration and execution persistence under one coordination lock. Durable adapters must provide an equivalent transaction or atomic persistence primitive before they are considered production-compatible with this contract.

The execution aggregate remains the sole lifecycle authority. Execution history remains downstream operational evidence and retains the established ordering: execution persistence occurs before history append.

### Implementation contract

The atomic boundary guarantees for the current in-memory implementation:

1. a duplicate cannot observe a registered key whose execution has not yet been persisted;
2. one key maps to one execution;
3. same-key/different-workflow remains a conflict;
4. if execution persistence fails before the execution exists, the idempotency reservation is released;
5. if execution persistence succeeds but later history evidence fails, the persisted execution and idempotency association remain available for deterministic replay;
6. no polling or second lifecycle state is introduced.

### Verification result

The implementation was verified through:

1. the existing RED concurrency proof converted to GREEN coverage;
2. concurrent duplicate-start regression;
3. reservation failure verification;
4. execution-save failure and orphan-reservation verification;
5. partial history failure/replay verification;
6. key conflict, normalization, no-key behavior, lifecycle evidence, API behavior, and regression coverage;
7. GitHub Actions run #969: **470 tests passed**.

## Current project state

No Phase 8 capability is selected or committed.

PR #228 remains unmerged as historical RED evidence. PR #232 contains the selected implementation and its equivalent GREEN regression coverage.

The Phase 7 concurrency decision is resolved. The project is now at the Post-Phase-7 Design Gate for explicit selection of the next major capability.

## Durable adapter boundary

This decision does not claim that the current in-memory lock is a durable transaction.

Before any durable persistence adapter is considered compatible with Option A, it must provide an equivalent atomic primitive that guarantees the same observable contract across idempotency registration and execution persistence.
