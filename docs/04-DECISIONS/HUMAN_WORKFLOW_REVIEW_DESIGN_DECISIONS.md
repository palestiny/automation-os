# Human Workflow Review — Design Decisions

Status: DECIDED — implementation gate preparation
Date: 2026-09-28

This document resolves the minimum architectural decisions required before implementing the Human Workflow Review capability.

## 1. Review and publication remain separate

**Decision:** A review approval records an approval decision. It does not implicitly publish the workflow.

The existing `PublishWorkflow` boundary remains the only publication mutation boundary.

Flow:

    DRAFT
      |
      v
    REVIEW
      |
      +---- REJECT ----> DRAFT + immutable rejection evidence
      |
      +---- APPROVE ---> DRAFT + immutable approval evidence
                              |
                              v
                         explicit Publish
                              |
                              v
                          PUBLISHED

Rationale:
- keeps governance separate from lifecycle mutation
- avoids ambiguous "approved but publication failed" state
- preserves the existing publication boundary
- allows future publication policies without redefining review semantics

## 2. Review decisions are immutable evidence

**Decision:** A review decision is append-only evidence, not a mutable status field.

A decision records at minimum:

- decision id
- workflow id
- reviewed workflow revision/context
- tenant/ownership context
- reviewer principal id
- decision
- reason/comment when applicable
- created timestamp

A later decision, if the product eventually permits re-review, creates another evidence record rather than rewriting history.

## 3. Review target must be stable

**Decision:** A review decision is bound to the exact workflow state/revision that was reviewed.

A stale reviewer must not be able to approve a materially changed draft accidentally.

The implementation must therefore establish a concurrency/revision identity before approval/rejection is persisted.

The exact optimistic-concurrency representation is an implementation decision, but "workflow UUID only" is insufficient for approval authority.

## 4. Tenant ownership is a precondition

**Finding:** Current `WorkflowVersion` carries optional `tenant_id`, while `Workflow` itself does not. The existing `WorkflowRepository.get(workflow_id)` is also not tenant-scoped.

**Decision:** Tenant-aware review cannot safely rely on the current workflow lookup contract alone.

Before enabling tenant-scoped review, ownership must be established at the review target boundary.

Preferred direction:

    Workflow
      + tenant_id
            |
            v
    AuthorizationPolicy
            |
            v
    Review operation

The exact migration strategy must preserve existing system-owned/legacy workflows without allowing a tenant principal to claim them.

Alternative repository-scoping can be considered, but it must provide an equivalent security guarantee. A UUID-only lookup followed by an application-level assumption is not sufficient.

## 5. System context remains explicit

System workflows may exist.

**Decision:** System authorization may operate on explicitly system-owned workflows, while tenant review requires an explicit tenant ownership match.

No implicit fallback from tenant context to system context.

## 6. Review commands are idempotent

**Decision:** Review commands must have deterministic replay semantics.

For a review target and decision command:

- exact replay must not create duplicate authoritative state
- conflicting decisions must not overwrite an existing decision silently
- retries must return the already-recorded authoritative result where appropriate

The exact idempotency key may be derived from the review target plus command identity, but the uniqueness boundary must be persisted durably.

## 7. Approval does not create Execution

**Decision:** Review has zero direct execution side effects.

An approval may make the workflow eligible for the explicit publication operation, but:

    review approval != publication != execution

Execution continues to require the existing published-workflow/version boundary and `StartWorkflowExecution`.

## 8. Rejection does not mutate workflow content

**Decision:** Rejecting a draft records the decision and reason but does not partially edit the workflow.

If later product requirements need "changes requested", that becomes a separate lifecycle decision.

## 9. First implementation surface is application/API-first

**Decision:** No mandatory frontend.

Initial contracts should be application-level and testable without a UI:

- list reviewable drafts
- get review target
- approve
- reject
- list/get review decisions

A UI can consume these contracts later.

## 10. No generic audit/event platform

**Decision:** Do not introduce a generic audit service or event bus for this capability.

Review evidence gets its own narrow persistence boundary. Existing execution history remains responsible for execution lifecycle evidence.

## 11. Minimum implementation gate

Implementation is authorized only after these invariants have executable tests:

1. Tenant reviewer cannot read another tenant's review target.
2. Tenant reviewer cannot approve/reject another tenant's workflow.
3. System context is explicit.
4. Review decision identifies the exact reviewed revision/state.
5. Stale review cannot approve a changed target.
6. Duplicate command replay is deterministic.
7. Conflicting decisions do not silently overwrite evidence.
8. Approval does not publish implicitly.
9. Approval does not create Execution.
10. Publication still requires the existing publication boundary.
11. Rejection preserves workflow content.
12. Review history remains attributable and durable.

## 12. Remaining implementation design question

The only major domain decision intentionally left open is the exact ownership migration for existing workflows:

A. Add `tenant_id` to Workflow and migrate legacy workflows explicitly.

B. Keep Workflow ownership external and introduce tenant-scoped repository methods.

C. Temporary system-only review until tenant ownership is established.

Recommended direction: **A**, because ownership is a property of the workflow aggregate and should remain explicit as the platform becomes tenant-aware.

No production implementation is included in this document.
