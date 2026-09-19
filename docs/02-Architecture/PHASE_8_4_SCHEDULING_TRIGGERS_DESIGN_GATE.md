# Phase 8.4 Design Gate — Scheduling / Triggers

Status: **APPROVED FOR IMPLEMENTATION — Application-level Trigger Invocation Boundary selected by Project Owner**

Capability: **Scheduling / Triggers**
Position: **4 of 13**

## Objective

Introduce deterministic workflow triggering without coupling execution to a specific scheduler, UI, external event provider, or durable scheduling implementation.

## Current repository evidence

The Workflow domain already contains a declarative Trigger with an event_type, and Workflow exposes triggers. WorkflowRepository exposes all(), while StartWorkflowExecution starts a workflow explicitly by workflow ID and already owns published-state validation and existing start/idempotency semantics.

Phase 8.4 should therefore focus on the missing application boundary that matches an incoming normalized trigger/event to eligible published workflow declarations and requests execution, rather than redesigning Workflow or Execution.

## In scope

- declarative trigger matching contract;
- explicit trigger invocation boundary;
- deterministic handling of matching/non-matching workflows;
- separation between trigger detection and execution;
- focused tests and exit review.

## Out of scope

- cron/time scheduling implementation;
- external event transport;
- durable scheduler storage;
- UI/mobile scheduling;
- retries/recovery;
- authorization;
- AI planning;
- marketplace changes;
- general workflow graph redesign.

## Architecture Decision

**Option A — Application-level Trigger Invocation Boundary is selected.**

A small application service evaluates an incoming normalized trigger/event against workflow declarations and delegates eligible execution to the existing StartWorkflowExecution boundary.

This keeps Workflow definition-oriented and prevents trigger reception/matching from becoming execution orchestration inside the domain.

Option B is **not** implemented as a competing mechanism. Existing TriggerMatcher is reconciled into this application boundary rather than replaced by a second trigger path.

The later scheduler/event-source capabilities will detect or produce events; this phase consumes normalized events and requests execution.

## Decision status

**Project Owner approval received; GREEN implementation is authorized.**

## Design questions that must be resolved during the selected option's RED phase

These are implementation-contract questions, not permission to silently expand scope:

1. **Eligibility:** only PUBLISHED workflows are trigger-eligible; draft workflows must not start.
2. **Multiple matches:** all matching published workflows are eligible. Invocation orders them by stable workflow UUID before delegating each start, so behavior does not depend on repository iteration order.
3. **No match:** return an explicit no-match result without invoking execution.
4. **Match-to-execution boundary:** a trigger match must delegate to StartWorkflowExecution; it must not construct or persist Execution directly.
5. **Idempotency:** trigger invocation must preserve the existing explicit-start idempotency semantics rather than introduce a second idempotency mechanism.
6. **Event contract:** the phase needs the smallest normalized input required to match the existing Trigger.event_type; payload semantics should not be invented unless required by the selected design.
7. **Detection vs scheduling:** this phase defines invocation/matching, not the mechanism that discovers that an event/time condition has occurred.

## Dependency boundary

Phase 8.4 consumes workflow trigger declarations and existing execution-start semantics. It must not introduce cron infrastructure, external event transport, durable scheduling, or authorization without separate decisions.

## Repository Reconciliation — Existing Scheduling/Trigger Code

Repository inspection found an earlier scheduling/trigger implementation that predates this Design Gate, including:

- `app/domain/event.py` with a normalized `Event(event_type)` value object;
- `app/application/trigger_matcher.py` that matches an Event against one Workflow without starting execution;
- `app/application/scheduling.py` with a concrete `ScheduledExecutionRequest` and `FixedClock`;
- `app/application/scheduled_workflow_execution.py` with `StartDueWorkflowExecution` and `ExecuteDueWorkflow`;
- existing tests covering trigger matching and due scheduled execution.

This code is useful repository evidence, but it is **not treated as the Phase 8.4 completion contract yet**. In particular, the current Design Gate is broader than a single scheduled-workflow request: it must define the application boundary for normalized trigger invocation, eligibility, deterministic multiple-match behavior, explicit no-match behavior, and delegation to `StartWorkflowExecution` while preserving its idempotency semantics.

The existing `ExecuteDueWorkflow` path also performs synchronous workflow execution after starting. That behavior is outside the current Phase 8.4 scope, because this phase must keep trigger detection/invocation separate from execution orchestration.

### Consequence for implementation planning

The GREEN implementation reconciles the legacy TriggerMatcher by composing it into the new TriggerInvocation boundary. The existing scheduled-workflow execution path remains available as legacy scheduling behavior; this phase does not create another scheduler or move synchronous execution into trigger invocation.
