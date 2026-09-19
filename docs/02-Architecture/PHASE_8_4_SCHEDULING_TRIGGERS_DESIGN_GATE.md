# Phase 8.4 Design Gate — Scheduling / Triggers

Status: **DESIGN PREPARATION — decision pending**

Capability: **Scheduling / Triggers**
Position: **4 of 13**

## Objective

Introduce deterministic workflow triggering without coupling execution to a specific scheduler, UI, external event provider, or durable scheduling implementation.

## Current repository evidence

The Workflow domain already contains a declarative Trigger with an event_type and Workflow exposes triggers. StartWorkflowExecution currently starts a workflow explicitly by workflow ID.

Phase 8.4 should therefore focus on the missing application boundary that matches a trigger to an eligible published workflow and requests execution, rather than redesigning Workflow or Execution.

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

## Alternatives

### Option A — Trigger Matching + Invocation Application Boundary

A small application service evaluates an incoming normalized trigger/event against workflow declarations and delegates eligible execution to the existing StartWorkflowExecution boundary.

Pros: separates detection from execution, testable, scheduler/provider independent, reuses existing execution semantics.

Trade-off: a later scheduling capability must supply time-based trigger detection; this phase does not provide a scheduler.

### Option B — Trigger Execution Embedded in Workflow

Workflow directly owns trigger evaluation and starts execution.

Pros: fewer application objects.

Trade-off: couples domain workflow definition to execution orchestration and makes external/time-based triggering harder to isolate and test.

## Decision required

Project Owner must select Option A or Option B before GREEN implementation.

## Dependency boundary

Phase 8.4 consumes workflow trigger declarations and existing execution-start semantics. It must not introduce cron infrastructure, external event transport, durable scheduling, or authorization without separate decisions.
