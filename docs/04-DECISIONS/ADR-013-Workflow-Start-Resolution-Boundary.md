# ADR-013 — Workflow Start Resolution Boundary

- Status: Accepted
- Phase: Phase 3 — Workflow Engine
- Date: 2026-09-16

## Context

WorkflowStartRequest identifies a Workflow by workflow_id, but the current runtime entry point Orchestrator.start() accepts a concrete Workflow.

The project does not yet have a committed persistence implementation or repository infrastructure. We therefore need an application boundary that can resolve the requested Workflow without inventing storage details.

## Decision

The application layer will define a WorkflowResolver protocol as a port:

get_by_id(workflow_id) -> Workflow | None

A WorkflowStartService will:
1. receive WorkflowStartRequest;
2. resolve the Workflow through WorkflowResolver;
3. reject an unknown Workflow;
4. delegate the resolved Workflow to Orchestrator.start().

WorkflowStartService does not own Execution lifecycle.

Orchestrator remains responsible for the runtime invariant that only a published Workflow can start.

Conceptually:

Trigger
   ↓
WorkflowStartRequest
   ↓
WorkflowStartService
   ↓
WorkflowResolver (port)
   ↓
Workflow
   ↓
Orchestrator
   ↓
Execution

## Why

This keeps the application flow explicit while avoiding a premature persistence decision.

The resolver is an application dependency boundary. A future in-memory store, database repository, API-backed source, or other implementation can satisfy the port without changing the start orchestration contract.

## Alternatives and Trade-offs

### A — Let Trigger resolve Workflow directly

Pros:
- Fewer application objects.

Trade-offs:
- Couples every trigger mechanism to Workflow storage/resolution.
- Duplicates resolution behavior across future triggers.
- Makes triggers responsible for more than detecting/requesting an event.

Decision: Rejected.

### B — Make Orchestrator accept WorkflowStartRequest

Pros:
- Fewer application layers.
- Centralizes startup behind Orchestrator.

Trade-offs:
- Forces Orchestrator to know Workflow resolution concerns.
- Mixes runtime coordination with obtaining the definition.
- Requires persistence/repository knowledge inside the runtime coordinator.

Decision: Rejected.

### C — WorkflowStartService + WorkflowResolver port

Pros:
- Separates request handling, Workflow resolution, and runtime orchestration.
- Keeps Orchestrator focused on Execution coordination.
- Allows persistence to be introduced later without redesigning the trigger boundary.
- Easy to unit test without infrastructure.

Trade-offs:
- Adds one application service and one port.
- The actual resolver implementation remains a future infrastructure decision.

Decision: Accepted.

## Scope Constraints

This ADR does not introduce:
- database persistence;
- repository implementation;
- Workflow versioning;
- caching;
- distributed locks;
- idempotency;
- trigger payload propagation;
- scheduler/webhook/event infrastructure.

## Deferred Decisions

- Concrete Workflow repository/storage implementation.
- Published Workflow version/revision resolution.
- Whether missing Workflow should use a dedicated application exception.
- Trigger payload propagation into ExecutionContext.
- Idempotency and duplicate-trigger handling.
