# Marketplace / Ecosystem Foundations Design Gate

## Status

Accepted / Implemented.

## Purpose

Define the smallest safe foundation for a future workflow/capability ecosystem without introducing a marketplace runtime, remote plugins, or untrusted code execution.

## Problem

Automation OS now has reusable workflows, capabilities, provider-neutral contracts, and multiple automation domains. An ecosystem requires discoverable definitions and stable identity, but a marketplace must not become a second execution engine or bypass existing validation and execution boundaries.

## Decisions

1. Marketplace foundations are metadata/discovery concerns, not a new execution engine.
2. A marketplace item references an existing platform artifact; it does not contain an alternate executable model.
3. Initial ecosystem scope is workflow discovery.
4. Workflow identity is the existing Workflow identity; marketplace metadata cannot replace it.
5. Published workflow rules remain authoritative.
6. Marketplace discovery may expose only workflows that satisfy explicit publication/visibility rules.
7. Marketplace metadata is separate from the Workflow aggregate to avoid turning the domain aggregate into catalog/search infrastructure.
8. Installation means making an already-defined workflow available to a platform/user; it does not execute it.
9. No remote code execution is introduced.
10. No arbitrary third-party Python plugins are loaded from the marketplace.
11. Capability implementations remain governed by the existing Capability contract and provider boundaries.
12. No payments, ratings, reviews, billing, tenancy, trust scoring, or moderation system is introduced in the foundation slice.
13. Search/filtering is deterministic metadata matching initially; semantic/vector marketplace search is deferred.
14. Marketplace discovery cannot bypass canonical intent goals or workflow parameter validation.
15. Execution continues exclusively through StartWorkflowExecution and the existing runtime.

## Initial Vocabulary

- MarketplaceListing: discoverable catalog entry.
- Workflow reference: identity of an existing Workflow.
- Listing metadata: title, description, domain, supported goals, tags.
- Visibility: whether a listing is discoverable.
- Installation: local availability of a referenced workflow.

## Boundary

**Workflow → Listing → Discovery → Installation → existing Workflow**

Not:

**Marketplace → custom execution runtime**

## Deferred

- remote executable plugins;
- arbitrary code sandboxing;
- marketplace payments;
- ratings/reviews;
- user-generated trust scores;
- multi-tenant marketplace infrastructure;
- semantic search;
- automatic installation of external credentials;
- automatic provider selection;
- workflow execution from marketplace data without installation/validation.

## TDD Order

1. MarketplaceListing vocabulary and invariants.
2. Deterministic discovery contract.
3. Published/visibility filtering.
4. Workflow reference validation.
5. Installation boundary.
6. End-to-end discovery-to-existing-workflow composition.

## Exit Criteria

- marketplace cannot execute anything directly;
- listings cannot reference unpublished/invalid workflows;
- discovery is deterministic and provider-neutral;
- installation does not bypass existing workflow validation;
- discovery → installation composition returns the existing workflow;
- existing execution engine remains the sole execution path.

## Implementation Status

Completed for the workflow discovery and installation foundation slice.

The foundation is now implemented through:

**Workflow → Listing → Discovery → Installation → existing Workflow**

The marketplace still has no execution runtime and does not introduce remote code execution.
