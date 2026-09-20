# Phase 8.11 — Marketplace Expansion Design Gate

## Status

**APPROVED FOR IMPLEMENTATION — Option A selected**

## Context

Automation OS already has marketplace foundations for deterministic discovery, publication, installation, and search. WorkflowVersion is now an immutable executable artifact, while current MarketplaceListing still references the logical Workflow.

The next expansion must prevent marketplace installations from silently moving to a different executable version while preserving the rule that marketplace metadata is not an execution engine.

## Objective

Define the next marketplace artifact boundary so marketplace distribution remains deterministic, version-aware, provider-neutral, and compatible with the existing WorkflowVersion execution model.

## Repository Evidence

Current marketplace path:

Workflow → Listing → Discovery → Installation → existing Workflow

Current versioned execution path:

Workflow → immutable WorkflowVersion → Execution

The key architectural gap is that a marketplace listing currently identifies Workflow rather than an immutable executable WorkflowVersion.

## Core Invariants

1. Marketplace must not become a second execution engine.
2. A marketplace artifact must resolve to an immutable executable definition.
3. Publishing a newer WorkflowVersion must not silently change an already published marketplace artifact.
4. Marketplace discovery remains deterministic.
5. Installation does not execute anything.
6. Workflow and WorkflowVersion lifecycle remain authoritative.
7. Provider-specific implementation details remain outside marketplace artifacts.
8. Existing published marketplace artifacts must have explicit compatibility behavior.
9. No payments, ratings, trust scoring, moderation, tenancy, or remote code execution is introduced by this capability unless separately approved.
10. Marketplace data must not bypass workflow/capability validation.

## Options

### Option A — Version-pinned Marketplace Listing

MarketplaceListing references a specific immutable WorkflowVersion.

**Pros**
- deterministic installation;
- exact executable artifact is known;
- aligns directly with Phase 8.8;
- reproducible marketplace behavior;
- simple security/compatibility reasoning.

**Trade-offs**
- a new workflow version requires a new listing or explicit listing update;
- existing listing does not automatically receive improvements;
- migration is required for current Workflow-based listings.

### Option B — Workflow-level Listing with Latest Published Version Resolution

MarketplaceListing continues referencing Workflow; installation resolves the latest published WorkflowVersion.

**Pros**
- simpler publisher experience;
- listing automatically receives new versions;
- preserves current listing identity.

**Trade-offs**
- installation is not reproducible;
- same listing can resolve to different executable artifacts over time;
- marketplace behavior becomes coupled to Workflow version publication timing;
- rollback/pinning becomes harder.

### Option C — Separate MarketplaceArtifact

Introduce a new immutable MarketplaceArtifact that references a WorkflowVersion, while MarketplaceListing remains mutable presentation metadata.

**Pros**
- clean separation between catalog metadata and immutable distributed artifact;
- supports future marketplace versioning, deprecation, compatibility, and provenance.

**Trade-offs**
- more domain vocabulary and persistence;
- more lifecycle complexity than the immediate problem requires;
- likely becomes a foundation for future marketplace ownership/trust features.

## Approved Decision

**Option A — Version-pinned Marketplace Listing** is approved.

A published marketplace listing must identify one immutable published `WorkflowVersion`. Existing Workflow-only listing records remain readable as legacy metadata but cannot be newly published or installed until explicitly migrated to a version. A new WorkflowVersion never silently changes an existing published listing.

It makes marketplace installation deterministic without introducing a second artifact lifecycle prematurely.

A future MarketplaceArtifact can still be introduced through a separate Design Gate if marketplace provenance, publisher ownership, compatibility, ratings, or distribution history require it.

## Decision Questions

1. Should marketplace listings pin an immutable WorkflowVersion?
2. Should existing Workflow-based listings be migrated to the latest published version, rejected until migrated, or preserved as legacy metadata?
3. When a new WorkflowVersion is published, should marketplace publication require an explicit listing update?
4. Should marketplace discovery expose the WorkflowVersion identity to consumers?
5. Should installation return the exact WorkflowVersion artifact rather than only the logical Workflow?

## TDD RED Plan

If Option A is approved:

1. listing requires a valid WorkflowVersion reference;
2. unpublished WorkflowVersion cannot be listed;
3. listing cannot silently change version;
4. publishing a new WorkflowVersion does not mutate existing listing;
5. discovery returns version-pinned listings;
6. installation resolves the exact WorkflowVersion;
7. old listing cannot install a withdrawn/unavailable version;
8. existing Workflow execution path remains unchanged.

## Explicitly Deferred

- marketplace accounts/ownership;
- ratings/reviews;
- trust/reputation;
- payments;
- semantic marketplace search;
- remote executable plugins;
- automatic provider installation;
- marketplace-specific AI ranking;
- multi-tenancy;
- marketplace analytics.

## Exit Criteria

- marketplace distribution is version-deterministic;
- no marketplace path executes directly;
- listing/version lifecycle is explicit;
- existing execution authority remains unchanged;
- focused and full regression tests pass;
- migration behavior is documented;
- exit review records deferred scope and limitations.
