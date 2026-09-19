# Marketplace Next Capability Design Gate

## Status

Accepted / Implemented.

## Context

The workflow marketplace foundation is complete for deterministic discovery and installation.

The platform now has:

**Workflow → Listing → Discovery → Installation → existing Workflow**

The next capability must add user value without creating a second execution engine or weakening the existing intent/workflow boundaries.

## Candidate Scope

The next marketplace capability is **listing publication management**.

This means the platform can create, validate, publish, hide, and withdraw marketplace listings around existing workflows.

It does **not** mean marketplace users can upload executable code or modify the referenced workflow through the listing.

## Decisions

1. Marketplace listings remain metadata around an existing Workflow.
2. A listing has an explicit lifecycle independent from Workflow execution.
3. Listing lifecycle is not allowed to execute, mutate, or bypass the referenced Workflow.
4. Publication requires a valid published Workflow.
5. Hidden/withdrawn listings are not discoverable.
6. Installation remains valid only for an active public listing backed by a published Workflow.
7. Listing publication does not register new intent goals; canonical goal vocabulary remains authoritative.
8. Listing metadata remains separate from the Workflow aggregate.
9. No remote executable plugins are introduced.
10. No payments, ratings, trust scores, or moderation system are introduced in this slice.

## Proposed Vocabulary

`ListingStatus`:

- DRAFT
- PUBLISHED
- WITHDRAWN

A listing may move:

**DRAFT → PUBLISHED → WITHDRAWN**

A withdrawn listing may not return to published state in the initial slice. Re-publication can be a later explicit design decision.

## Publication Invariants

A listing may be published only when:

- its referenced Workflow exists;
- the Workflow is PUBLISHED;
- its supported goals are supported by the Workflow;
- its required metadata is valid.

Publication must not execute the Workflow.

## Discovery Impact

Discovery should expose only listings with:

- `ListingStatus.PUBLISHED`;
- valid published Workflow backing;
- existing deterministic goal/domain filtering.

The current visibility concept should not be allowed to create a second, contradictory publication lifecycle.

## TDD Order

1. Define listing lifecycle vocabulary and transitions.
2. Add publication use case with Workflow validation.
3. Update discovery to use listing publication status.
4. Update installation to require published listing status.
5. Add end-to-end lifecycle → discovery → installation tests.
6. Record exit review.

## Explicitly Deferred

- listing ownership/accounts;
- marketplace permissions;
- reviews/ratings;
- payments;
- semantic search;
- remote code;
- automatic credentials;
- marketplace-specific AI generation;
- multi-tenancy.

## Exit Criteria

- listing lifecycle is explicit and deterministic;
- invalid listings cannot be published;
- withdrawn listings cannot be discovered or installed;
- existing Workflow execution remains the only execution path;
- canonical intent goals remain authoritative;
- all behavior is covered by tests and documented.