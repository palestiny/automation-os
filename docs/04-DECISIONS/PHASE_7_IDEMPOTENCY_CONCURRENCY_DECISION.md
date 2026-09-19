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

## Required invariants

Any selected design must preserve:

1. one successfully registered key maps to one execution;
2. concurrent duplicates deterministically resolve to that execution;
3. the same key used for a different workflow remains a conflict;
4. a successful idempotency record cannot remain orphaned;
5. execution remains the sole lifecycle authority;
6. persistence failures remain explicit;
7. no polling or retry loop merely hides the race;
8. the design remains compatible with the project's persistence boundaries.

## Options

### A — Atomic reservation + execution persistence

Coordinate idempotency registration and execution persistence inside one atomic persistence boundary.

**Advantages**
- strongest consistency model;
- duplicate requests cannot observe an intermediate reservation;
- semantics are straightforward once the persistence boundary supports the operation.

**Costs / implications**
- may require evolving repository interfaces;
- durable persistence adapters may need transaction or equivalent atomic support;
- in-memory behavior should model the same contract rather than create a special case.

### B — Pending / Resolved idempotency state

Make idempotency records explicitly represent an in-progress reservation and a resolved execution.

A duplicate encountering a pending record follows a defined resolution protocol rather than treating the record as immediately replayable.

**Advantages**
- explicit representation of the intermediate state;
- can work where transactionally atomic persistence is unavailable.

**Costs / implications**
- introduces additional state and coordination semantics;
- requires defined timeout/stuck-reservation behavior;
- duplicate request behavior becomes more complex;
- must avoid creating a second lifecycle/state authority.

### C — Persistence-level compare/claim coordination

Keep the conceptual idempotency model but introduce a persistence operation that atomically claims/resolves the key together with the persisted execution.

**Advantages**
- can keep the domain contract focused while placing coordination in the persistence adapter;
- can be adapted to different storage capabilities.

**Costs / implications**
- exact guarantees depend on the adapter;
- repository contracts become more specialized;
- durable implementations must provide equivalent atomic semantics.

## Decision boundary

Do not implement A, B, or C implicitly.

The Project Owner must select the coordination model before production behavior is changed.

After selection:

1. record the rationale and trade-offs;
2. update the Phase 7 Design Gate / hardening review as appropriate;
3. implement RED → GREEN;
4. verify concurrent duplicates, partial failures, key conflicts, and persistence failures;
5. run the full regression suite;
6. update PROJECT_STATUS.md and the Phase 7 exit/hardening documentation;
7. only then consider the Post-Phase-7 Design Gate for the next capability.

## Current project state

No Phase 8 capability is selected or committed.

PR #228 remains intentionally unmerged because it is RED evidence for this decision boundary.
