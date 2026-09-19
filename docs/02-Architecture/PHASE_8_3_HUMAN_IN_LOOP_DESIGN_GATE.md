# Phase 8.3 Design Gate — Human-in-the-Loop

Status: **APPROVED FOR IMPLEMENTATION — Option A selected by Project Owner**

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

## Decision

**Option A — Application-level Human Decision Port** is selected by the Project Owner.

The human decision boundary is an application-level control point associated with a waiting Execution. Human interaction is not modeled as an ordinary provider capability. General expression of human decisions, UI/mobile concerns, authorization, durable pending-decision persistence, scheduling, and AI autonomy remain outside this capability.

## Dependency boundary

Human-in-the-Loop consumes workflow/condition control points and execution lifecycle boundaries. It must not pull scheduling, durable persistence, UI, authorization, or AI autonomy into this capability without a separate decision.


## Implementation insertion-point analysis

Repository inspection confirms that no separate workflow-step execution orchestrator currently owns a human decision boundary. The existing application boundaries operate directly on persisted Execution aggregates, while the domain already owns the WAITING lifecycle.

If Option A is selected, the smallest implementation boundary should therefore be an application-level decision request/result model associated with an Execution, with the following invariants:

1. A decision request is associated with exactly one Execution.
2. A decision request is actionable only while its Execution is WAITING.
3. Approval and rejection are explicit, mutually exclusive terminal decisions for that request.
4. A decision cannot resume an Execution that is no longer WAITING.
5. Repeating the same already-recorded decision must be deterministic; conflicting repeated decisions must be rejected.
6. The decision boundary must not introduce UI, authentication, durable storage, provider execution, or scheduling semantics.
7. Existing Execution.wait()/resume()/cancel() lifecycle rules remain the source of execution-state authority.

This is a contract proposal for the pending architecture decision, not a selected implementation. GREEN implementation remains blocked until the Project Owner selects Option A or B.
