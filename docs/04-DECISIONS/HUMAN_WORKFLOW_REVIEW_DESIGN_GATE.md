# Human Workflow Review Design Gate

Status: DESIGN GATE — not authorized for implementation
Date: 2026-09-28

## 1. Purpose

Define the first post-roadmap capability candidate for Automation OS:

**Human Workflow Review / Operations Surface**

This document is a design gate only. It does not authorize production implementation, UI selection, or runtime behavior changes.

## 2. Problem Statement

Automation OS can already generate a provider-neutral workflow candidate, validate it, materialize it as a persisted DRAFT workflow, explicitly publish it, and execute only published workflows.

The missing product boundary is a controlled human operation path for inspecting and deciding what happens to persisted DRAFT workflows.

The intended problem is:

> A human operator/reviewer needs a reliable way to discover reviewable workflow drafts, inspect their validated structure and context, approve or reject them, and retain evidence of that decision without implicitly starting execution.

## 3. Existing Foundation

The current architecture already provides:

- Workflow DRAFT/PUBLISHED lifecycle.
- Generated workflow persistence.
- Deterministic candidate validation.
- Explicit publication boundary.
- Authorization context and tenant identity.
- Workflow versioning and immutable published revisions.
- Execution discovery, progress, and history.
- Deterministic execution.
- Idempotent workflow starts.

Therefore the first review slice should be an application/domain capability, not a rewrite of the execution engine.

## 4. Proposed Boundary

Initial conceptual flow:

    ListReviewableDrafts
            |
            v
       GetDraft
            |
            v
    Validate / Present
            |
        +---+---+
        |       |
      Approve  Reject
        |       |
        +---+---+
            |
            v
    Persist Review Decision

Critical invariant:

> A review decision must never silently start workflow execution.

Approval may authorize or invoke the existing publication boundary, but the exact relationship between approval and publication must be decided explicitly in this gate. No implicit execution coupling is allowed.

## 5. Domain Questions

The gate must resolve the following before implementation.

### Review lifecycle

Minimum candidate states:

- REVIEWABLE
- APPROVED
- REJECTED

Possible additional state:

- CHANGES_REQUESTED

Decision required: whether rejection and requested changes are distinct business meanings.

### Review identity

A review decision needs:

- reviewed workflow identity
- reviewer identity
- tenant identity
- decision
- timestamp
- reason/comment where applicable
- reviewed revision/version context where applicable

Decision records should be immutable evidence rather than mutable status-only fields.

### Publication relationship

Options:

A. Review approval directly calls the existing publication application boundary.

B. Review records approval; a separate explicit publication action performs publication.

C. Review creates an approval authorization that publication consumes.

Trade-off:

- A is simplest but couples review and publication.
- B preserves the strongest existing boundary but adds an explicit operator step.
- C gives stronger governance semantics but introduces more lifecycle complexity.

Current recommendation for the gate:

**Prefer B unless a concrete product requirement requires approval to be the publication authorization.**

### Rejection semantics

Rejecting a draft must not mutate the workflow into a partially modified state.

The initial contract should preserve the reviewed draft and record the decision/reason.

If editing/resubmission is later required, define a separate revision/resubmission lifecycle instead of silently reopening published artifacts.

## 6. Authorization and Tenant Isolation

Review operations must execute inside the existing authorization model.

Required invariants:

- Reviewer can access only authorized tenant/workflow scope.
- A review decision cannot be attached to another tenant's workflow.
- Reviewer identity must be attributable.
- Publication must continue to enforce its existing authorization boundary.
- Review must not become a bypass around workflow publication or execution authorization.

Do not introduce a second authorization system.

## 7. Persistence

A review decision is operational evidence and should be durably persisted.

Candidate abstraction:

    WorkflowReviewDecisionRepository

The exact repository shape is not committed by this document.

Persistence must answer:

- Who decided?
- What workflow was reviewed?
- What revision/state was reviewed?
- What was decided?
- When?
- Why, when a reason is required?

The design must prevent a later workflow mutation from making historical review evidence ambiguous.

## 8. Idempotency

Review commands need explicit replay semantics.

At minimum:

- Repeating the same decision for the same review target must have deterministic behavior.
- Conflicting repeated decisions must not silently overwrite historical evidence.
- Approval must not accidentally publish twice.
- Review retries must not create duplicate authoritative decisions.

The exact idempotency key and uniqueness boundary are part of the implementation design gate.

## 9. Runtime Boundary

No changes to the execution engine are required for the first slice.

The review capability must not:

- create an Execution merely because a draft was reviewed
- bypass StartWorkflowExecution
- execute unpublished workflows
- invoke providers
- modify provider configuration
- expose credentials
- allow AI output to become executable authority

## 10. API/Application-First Scope

The first implementation should be application/API-first.

Minimum useful operations:

- list reviewable drafts
- retrieve a reviewable draft
- approve
- reject
- retrieve review decision/history

A frontend is explicitly out of scope for the first slice unless a concrete product requirement makes it necessary.

## 11. Observability

Review operations should produce sufficient evidence to answer:

- what entered review
- who reviewed it
- what decision was made
- when it happened
- which workflow/revision was affected
- whether publication subsequently occurred

Do not introduce a generic audit/event platform solely for this capability.

## 12. Failure Semantics

Expected failures must be explicit:

- workflow not found
- workflow not reviewable
- unauthorized reviewer
- tenant mismatch
- stale review target
- duplicate/conflicting decision
- publication failure after approval, if approval is coupled to publication

No failure should leave an ambiguous state such as "approved and maybe published".

## 13. Trade-offs

### Option A — Approval directly publishes

Pros:
- simplest operator flow
- fewer explicit steps
- easy to reason about for a small system

Cons:
- couples governance decision with lifecycle mutation
- harder to distinguish "approved" from "published"
- publication failures complicate review state

### Option B — Approval and publication remain separate

Pros:
- strongest separation of concerns
- preserves existing publication boundary
- clearer failure semantics
- review remains a governance capability

Cons:
- one additional operator action
- requires a clear UI/API workflow later

**Recommendation: Option B for the initial architecture.**

### Option C — Approval authorization token/state

Pros:
- stronger governance model
- useful if multiple approval levels are eventually required

Cons:
- introduces another lifecycle and authorization concept
- unnecessary complexity for the first slice

**Recommendation: defer unless a concrete requirement appears.**

## 14. Explicit Non-Goals

This gate does not authorize:

- a frontend framework
- a full admin dashboard
- multi-level approval chains
- generic audit infrastructure
- generic event bus
- credential management
- marketplace expansion
- autonomous AI approval
- automatic execution after approval
- deployment/release management

## 15. Verification Gate

Before implementation can be authorized, the design must prove:

1. Review target identity is unambiguous.
2. Tenant/authorization boundaries are enforced.
3. Review decisions are durable and attributable.
4. Replay/conflict behavior is deterministic.
5. Approval cannot bypass publication.
6. Review cannot create execution implicitly.
7. Published workflow/version immutability remains intact.
8. Rejection cannot corrupt the draft lifecycle.
9. Failure states remain observable and recoverable.
10. Existing execution and generation invariants remain unchanged.

## 16. Decision Required

The remaining product decision is:

**Should Automation OS first optimize for controlled human operation of generated workflows?**

If yes, this gate becomes the active implementation gate.

If no, return to the post-roadmap capability matrix and select a different concrete product problem.

## 17. Current Recommendation

Proceed with the Human Workflow Review Design Gate, but do not implement until the lifecycle, approval/publication relationship, persistence model, authorization behavior, and idempotency semantics are explicitly decided.

