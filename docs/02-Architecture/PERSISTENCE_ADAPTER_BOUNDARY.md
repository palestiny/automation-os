# Phase 3 — Persistence Adapter Boundary

Status: Design baseline
Date: 2026-09-18
Issue: #38

## Purpose

Define the boundary between persistence contracts and concrete infrastructure after introducing repository contracts and in-memory reference adapters. The goal is to preserve aggregate boundaries while avoiding premature database, ORM, transaction, or worker decisions.

## Committed Decisions

### 1. Repositories persist aggregates, not individual fields

The repository boundary is aggregate-aligned:
- WorkflowRepository persists and retrieves Workflow aggregates.
- ExecutionRepository persists and retrieves Execution aggregates.

The repository API does not expose persistence-specific queries, ORM entities, tables, sessions, or database connections.

### 2. Infrastructure adapters own persistence mapping

A concrete adapter may use persistence models that differ from domain objects. Mapping between persistence representation and valid domain aggregates belongs in the infrastructure adapter.

Domain entities must not gain database IDs, ORM annotations, sessions, serialization code, or storage-specific behavior merely to support persistence.

### 3. The in-memory adapters are reference/test adapters

The current in-memory implementations establish the repository contract and provide a deterministic adapter for tests and early application wiring.

They are not the production persistence strategy and must not force an in-memory-specific domain behavior.

### 4. Save semantics are replacement-by-aggregate-ID

For the current repository contract, saving an aggregate with an existing ID replaces the stored representation for that aggregate.

Insert-vs-update distinction is intentionally hidden from callers. If optimistic concurrency or version checks become necessary, they require a separate design decision.

### 5. Transactions and Unit of Work are not introduced yet

Repository methods remain independently callable. No Unit of Work abstraction is added until a concrete application use case requires multiple aggregate changes to commit atomically.

This avoids introducing transaction semantics without a demonstrated consistency requirement.

### 6. Execution persistence is separate from Workflow persistence

Execution and Workflow retain separate repository boundaries because their lifecycles and consistency concerns differ. A future infrastructure transaction may coordinate both where a concrete use case requires it, without collapsing their repository responsibilities.

### 7. Persistence queries remain minimal

The current contract supports save/get by aggregate identity only. Query methods, filtering, pagination, deletion, and history are deferred until an application use case requires them.

## Deferred Scope

- database vendor and schema;
- ORM selection;
- Unit of Work / transaction abstraction;
- optimistic concurrency/versioning;
- query/read-model strategy;
- deletion semantics;
- execution context serialization;
- scheduling/background workers;
- production persistence implementation.

## Design Consequence

Phase 3 can now add application use cases against repository contracts without coupling those use cases to a database. A production persistence adapter can be selected later behind the same boundary, provided it preserves aggregate reconstruction and the committed repository semantics.

## Gate Result

The persistence adapter boundary is sufficiently defined for focused implementation work. The next implementation should be driven by a concrete runtime/application use case rather than by selecting infrastructure technology in isolation.
