# Phase 8.6 — Durable Persistence Trade-offs

## Purpose

Provide the Project Owner with the concrete trade-offs required to choose the durable persistence direction before implementation begins.

This document does not make the architectural decision.

## Current Boundary

The application already depends on repository contracts for:

- Workflow persistence.
- Execution persistence.
- Workflow-start idempotency.
- Atomic idempotent execution creation.
- Append-only execution history.

The domain does not need to know which database or persistence library is selected.

## Decision Dimensions

| Dimension | SQLite + explicit SQL | PostgreSQL + explicit SQL | SQLAlchemy adapter |
|---|---|---|---|
| Local development | Very simple | Requires DB service/container | Depends on selected DB |
| Durable transactions | Yes | Yes | Yes, through selected DB |
| Cross-process concurrency | More constrained | Strong fit | Depends on selected DB |
| Explicit SQL/data model | High | High | Lower if ORM mapping is used |
| Repository boundary clarity | Strong | Strong | Strong if ORM stays behind adapter |
| Operational complexity | Low | Higher | Depends on DB + ORM |
| Production multi-instance path | More limited | Strong | Depends on DB |
| Schema migration strategy | Required | Required | Required |
| Extra abstraction | Low | Low | Higher |
| Fit with current architecture | Direct | Direct | Direct, but adds mapping/session concerns |

## Option A — SQLite + Explicit SQL Repositories

### Advantages

- Minimal infrastructure.
- Durable local state without a separate database service.
- Transaction semantics are available for the repository boundary.
- Keeps the persistence adapter explicit and easy to inspect.

### Trade-offs

- Multi-process deployment has more operational constraints than a server database.
- Concurrency characteristics are less aligned with a future horizontally scaled execution service.
- Moving from a local SQLite deployment to a server database later may require another persistence deployment decision.

### Best fit

A local-first or single-instance Automation OS where minimizing infrastructure is the primary constraint.

## Option B — PostgreSQL + Explicit SQL Repositories

### Advantages

- Strong transactional and concurrency primitives for atomic idempotent starts.
- Clear fit for multiple application processes/instances.
- Keeps domain and application layers independent from database-specific APIs.
- Explicit SQL keeps transaction boundaries and persistence behavior visible.

### Trade-offs

- Requires database provisioning/configuration.
- Adds connection management and migration concerns.
- Local development needs a PostgreSQL environment unless a separate local strategy is adopted.

### Best fit

A production-oriented Automation OS expected to evolve toward concurrent, multi-process execution.

## Option C — SQLAlchemy-Based Persistence Adapter

### Advantages

- Mature transaction/session management.
- Supports multiple database backends.
- Can reduce repetitive persistence plumbing.
- Can remain behind repository contracts.

### Trade-offs

- Adds ORM/session/mapping concepts to the infrastructure layer.
- Makes transaction ownership less explicit unless repository/application boundaries are deliberately designed.
- Does not remove the underlying database choice.
- Introduces another abstraction that must be maintained.

### Best fit

A project where ORM productivity and database portability justify the additional infrastructure abstraction.

## Critical Architectural Question

The most important decision is not the database name by itself.

It is:

> Which durable transaction boundary owns the invariant that one idempotency key can create at most one execution for a workflow start?

The implementation must make this invariant database-backed rather than relying on a process-local lock.

## Recommended Evaluation Order

1. Select the database durability model.
2. Decide whether SQL is explicit or mediated by an ORM.
3. Define transaction ownership for workflow-start idempotency.
4. Define schema constraints that enforce uniqueness.
5. Define the repository adapter composition.
6. Only then begin RED tests for the selected implementation.

## Proposed Engineering Default

**PostgreSQL + explicit repository adapters + explicit transaction boundaries** remains the proposed engineering default because it directly addresses the project's intended multi-process evolution while preserving the existing domain/application boundaries.

This is a proposal, not a committed project decision.

## Explicitly Deferred

This decision does not include:

- distributed workers;
- automatic recovery;
- workflow versioning;
- multi-tenancy;
- authorization;
- HA/replication operations;
- backup/restore runbooks;
- provider marketplace persistence beyond concrete Phase 8.6 needs.

## Decision Record

**Status:** Awaiting Project Owner decision.

**Chosen option:** Not decided.

**Implementation:** Blocked until the persistence direction is accepted.
