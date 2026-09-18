# ADR-012 — Workflow Start Trigger Boundary

- Status: Accepted
- Phase: Phase 3 — Workflow Engine
- Date: 2026-09-16

## Context

The current runtime can start a published Workflow through Orchestrator.start(workflow), but there is no explicit boundary for schedules, webhooks, file arrivals, user actions, or external events to request Workflow execution.

Embedding those mechanisms inside Workflow would couple the reusable Workflow definition to external infrastructure. Giving a Trigger ownership of Execution would create a second lifecycle owner.

## Decision

Triggers are external/application mechanisms that produce a WorkflowStartRequest.

A WorkflowStartRequest identifies the Workflow to start by workflow_id.

Triggers do not execute Workflow steps and do not own Execution lifecycle. The Orchestrator remains responsible for runtime coordination and Execution startup.

Conceptually:

Trigger -> WorkflowStartRequest -> application start boundary -> Orchestrator -> Execution

The first implementation keeps the request intentionally minimal and does not introduce trigger-specific payloads or context propagation.

## Consequences

### Positive

- External trigger infrastructure remains outside the Workflow domain definition.
- Execution retains a single authoritative lifecycle owner.
- A Workflow can later be started by multiple mechanisms without changing Execution semantics.
- Trigger adapters remain replaceable.
- The boundary is testable without requiring Scheduler/Webhook infrastructure.

### Negative

- Adds an explicit application request/boundary concept.
- A concrete start path still needs a Workflow resolution strategy.
- Trigger-specific payload propagation will require a later contract decision if needed.

## Scope Constraints

This ADR does not introduce scheduler implementation, webhook implementation, event bus, trigger persistence, Workflow persistence, trigger configuration lifecycle, idempotency/deduplication, correlation/causation identifiers, or trigger-specific payload contracts.

## Deferred Decisions

- How the application layer resolves WorkflowStartRequest.workflow_id to a published Workflow.
- Whether trigger payload becomes part of the start request and how it maps into ExecutionContext.
- Whether Trigger becomes a persisted domain concept associated with Workflow.
- Duplicate-event/idempotency semantics.
- Concrete Scheduler/Webhook/Event adapters.
