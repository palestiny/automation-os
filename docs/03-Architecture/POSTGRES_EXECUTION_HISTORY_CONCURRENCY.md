# PostgreSQL Execution-History Concurrency Verification

## Scope

Phase E verifies the concurrency behavior of PostgreSQL execution-history append operations.

The relevant persistence contract is append-only execution evidence with a primary key on:

`(execution_id, sequence)`

The implementation currently determines the expected next sequence by reading `MAX(sequence)`, validates the caller-provided sequence, and inserts the event.

## Verification Method

The acceptance test uses:

- PostgreSQL 17 in CI;
- two independent database connections;
- the same `execution_id`;
- two different events with the same next sequence;
- a database trigger that deliberately overlaps the two inserts;
- independent repository transactions.

The overlap removes normal scheduling luck from the test and exercises the actual PostgreSQL uniqueness boundary.

## Observed Result

The concurrent append produced:

1. one committed event;
2. one PostgreSQL `UniqueViolation` against `execution_history_pkey`;
3. no duplicate `(execution_id, sequence)` row;
4. ordered persisted history.

CI run #2066 passed with **761 tests**.

## Interpretation

This verifies that the current schema prevents history corruption under the tested concurrent-write race.

It does **not** prove that the current repository behavior is an ideal application-level concurrency API. The losing writer receives a database exception rather than a typed domain/application concurrency result.

The distinction matters:

- **Data integrity:** protected by the database primary key.
- **Concurrent writer outcome:** optimistic conflict; one writer loses.
- **Automatic retry:** not currently defined by the history repository contract.
- **Universal serialization:** not required by the current evidence.

## Decision

**Phase E verification: PASS.**

No database sequence-allocation rewrite is justified solely by the observed race.

The current behavior remains acceptable as an optimistic-concurrency boundary because the database rejects the conflicting duplicate and preserves unique ordered history.

If execution orchestration later introduces multiple concurrent writers for the same execution history, a separate design gate should define:

- typed history-concurrency error;
- retry/backoff policy;
- whether the stale aggregate must be reloaded before retry;
- whether event sequence allocation should move into a database-side serialization mechanism.

That decision should be driven by an actual concurrent runtime path, not by the existence of the theoretical race alone.

## Alternatives Considered

### Database-side serialization

Lock an execution row or use another PostgreSQL serialization primitive before allocating the next sequence.

**Benefit:** fewer loser-side conflicts.

**Cost:** stronger database coupling, more locking, and potential contention.

### Database-generated sequence identity

Replace the domain sequence contract with a database-generated identifier.

**Benefit:** simple concurrent allocation.

**Cost:** changes the existing event-ordering contract and domain semantics.

### Keep optimistic concurrency

Retain `MAX(sequence)` plus the primary-key constraint and treat duplicate sequence as a conflict.

**Benefit:** smallest change, preserves current domain contract, and the database remains the final integrity boundary.

**Cost:** concurrent stale writers can receive a database-level conflict.

**Decision:** selected for Phase E based on current evidence.

## Follow-up

If the raw `UniqueViolation` becomes reachable from a real runtime concurrency path, introduce a typed application-level conflict rather than leaking the database exception through application boundaries.
