# Phase 8.3 Design Gate — Human-in-the-Loop

Status: **DESIGN PREPARATION — decision pending**

Capability: **Human-in-the-Loop**
Position: **3 of 13**

## Objective

Introduce explicit human control points into workflow execution without making human interaction a hidden side effect of capabilities.

## In scope

- explicit human approval/rejection control point;
- deterministic pause/resume semantics;
- structured decision request/context;
- explicit decision result;
- focused tests, full regression, documentation, exit review.

## Out of scope

Scheduling/triggers, external events, UI/mobile implementation, authorization, durable persistence redesign, AI autonomous approval, marketplace changes, general workflow graph redesign.

## Alternatives

### Option A — Application-level Human Decision Port

A narrow application boundary represents a pending human decision. Execution pauses at the boundary and resumes only after an explicit decision.

Pros: small, testable, UI-independent, compatible with later clients.

Trade-off: durable pending decisions remain dependent on the later persistence capability.

### Option B — Human Approval as a Capability

Represent approval as an ordinary executable capability.

Pros: reuses capability execution mechanics.

Trade-off: mixes human control with provider execution and makes authority/pause semantics less explicit.

## Decision required

Project Owner must select Option A or Option B before GREEN implementation.

## Dependency boundary

Human-in-the-Loop consumes workflow/condition control points and execution lifecycle boundaries. It must not pull scheduling, durable persistence, UI, authorization, or AI autonomy into this capability without a separate decision.
