# Trigger / Workflow Start — Design Gate

- Status: Boundary committed; concrete trigger adapters and Workflow resolution deferred
- Phase: Phase 3 — Workflow Engine
- Scope: External/application mechanisms that request Workflow execution
- Owner: Khaled (Project Owner / Decision Maker / Tech Lead)

## Purpose

Define how an external event or application mechanism requests execution of a Workflow without making the Workflow or Execution responsible for external trigger infrastructure.

## 1. Concept

A Trigger is an external or application mechanism that detects or receives something that should cause a Workflow to start.

Examples include a scheduled time, webhook request, file arrival, user action, or external event.

A Trigger does not execute Workflow steps and does not own Execution lifecycle. Its first responsibility is to produce a WorkflowStartRequest containing the identity of the Workflow that should be started.

## 2. Committed Boundary

External Trigger -> WorkflowStartRequest -> application start boundary -> Orchestrator -> Execution

The ownership rule is: Triggers request Workflow execution; they do not own Workflow execution.

## 3. Ownership

| Component | Owns |
|---|---|
| Trigger adapter | Receiving/detecting the external/application event and producing a start request |
| WorkflowStartRequest | Transporting the intent to start a specific Workflow |
| Workflow | Workflow definition and structural validity |
| Orchestrator | Runtime coordination and Execution startup |
| Execution | Runtime lifecycle and progression |
| Infrastructure | Scheduler/webhook/file/event integration |

A Trigger must not create, retry, complete, fail, cancel, or otherwise manage an Execution lifecycle.

## 4. Alternatives and Trade-offs

### A — Trigger inside Workflow

Pros: fewer concepts initially; Workflow appears to contain the full automation definition.

Trade-offs: couples Workflow definition to external infrastructure, makes scheduler/webhook/event concerns part of the Workflow model, and makes the definition harder to test independently.

Decision: Rejected for the current architecture.

### B — Trigger as a domain object attached to Workflow

Pros: explicit domain representation and support for multiple triggers per Workflow.

Trade-offs: introduces trigger lifecycle and ownership decisions before concrete requirements exist and adds domain surface area early.

Decision: Deferred.

### C — Trigger adapter produces WorkflowStartRequest

Pros: keeps external mechanisms outside Workflow and Execution, allows multiple mechanisms to start the same Workflow, is easy to test, and preserves the Orchestrator as runtime coordination boundary.

Trade-offs: adds an application boundary and a request type; concrete adapters still need later decisions about Workflow resolution and trigger-specific payloads.

Decision: Accepted for the current slice.

## 5. Current Implementation Scope

The current slice introduces only WorkflowStartRequest with workflow_id and a Trigger application boundary that produces the request, with tests for both contracts.

It does not introduce Scheduler, Webhook server, Event Bus, File Watcher, trigger persistence, Workflow persistence, trigger registration/configuration, duplicate-event handling, idempotency, correlation IDs, or trigger-specific payload schemas.

## 6. Workflow Resolution

WorkflowStartRequest identifies the target Workflow by ID, but the project does not yet have a committed Workflow persistence/resolution strategy. This slice therefore does not invent a repository or persistence implementation merely to complete the trigger boundary.

When an actual trigger-to-start path is introduced, the application layer must decide how workflow_id is resolved to a published Workflow before invoking the Orchestrator.

## 7. Deferred Decisions

- Workflow resolution/repository boundary for start requests.
- Trigger-specific payload/context propagation.
- Trigger persistence and configuration.
- Multiple triggers per Workflow as a domain concept.
- Duplicate-event/idempotency policy.
- Correlation and causation identifiers.
- Scheduler/webhook/event infrastructure.
- Trigger enable/disable lifecycle.

## 8. Related Documentation

- docs/02-Architecture/WORKFLOW_DESIGN_GATE.md
- docs/04-DECISIONS/ADR-011-Workflow-Transition-Routing.md
- docs/04-DECISIONS/ADR-012-Workflow-Start-Trigger-Boundary.md
- docs/01-Roadmap/ROADMAP.md
