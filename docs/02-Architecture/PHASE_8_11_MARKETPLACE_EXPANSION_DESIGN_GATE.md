# Phase 8.11 — Marketplace Expansion Design Gate

## Status

**APPROVED FOR IMPLEMENTATION — Option A selected by Project Owner**

## Purpose

Expand the existing marketplace foundation into a stable artifact-oriented marketplace boundary without making the marketplace an execution authority.

## Repository Baseline

The repository already has:
- `MarketplaceListing` domain entity;
- deterministic marketplace discovery;
- installation validation;
- published-workflow checks;
- immutable `WorkflowVersion` artifacts;
- provider-independent capability contracts;
- durable PostgreSQL persistence.

The current listing references a mutable `Workflow` identity directly. That is insufficient for a marketplace artifact that must remain reproducible after later workflow evolution.

## Approved Option A — Version-pinned Marketplace Artifact

A marketplace listing publishes an immutable, explicit `WorkflowVersion` artifact.

The listing remains metadata/discovery information and points to one immutable workflow version. Installation resolves and validates that exact version; it does not silently upgrade to a newer version.

### Contract

```
Marketplace Listing
       ↓
immutable WorkflowVersion
       ↓
validated installation
       ↓
local workflow/version identity
```

- Listing identity is separate from workflow identity.
- Published listings must reference an existing published WorkflowVersion.
- Discovery returns only publicly visible, published listings whose referenced version is available.
- Installation is deterministic and version-pinned.
- Marketplace does not execute workflows.
- Marketplace does not select providers.
- Marketplace does not bypass workflow validation.
- Withdrawn listings cannot be newly installed.
- Existing installed artifacts are not mutated by later listing changes.

## Alternatives Considered

### Option A — Version-pinned artifact
Keeps marketplace reproducibility aligned with WorkflowVersion immutability.

Trade-off: listings carry explicit version identity and require version-aware persistence.

### Option B — Mutable workflow reference
Keeps the current model simple.

Trade-off: installing the same listing later could resolve a different workflow definition after updates, weakening reproducibility and auditability.

### Option C — Packaged workflow/capability bundle
Creates a richer portable package containing workflow, versions, capabilities, and metadata.

Trade-off: larger artifact and dependency-resolution surface than the current platform needs.

## Scope

- version-pinned marketplace listing contract;
- publication validation;
- deterministic discovery;
- deterministic installation;
- persistence required for listings;
- focused tests and PostgreSQL parity;
- documentation and exit review.

## Deferred

- ratings/reviews/reputation;
- payments/billing;
- private/tenant marketplaces;
- remote capability installation;
- automatic dependency/provider installation;
- marketplace recommendation/ranking;
- marketplace UI;
- signing/cryptographic supply-chain verification;
- external marketplace federation.

## Exit Criteria

- RED tests define version-pinned behavior.
- GREEN implementation passes focused tests.
- Existing marketplace behavior remains valid where compatible.
- PostgreSQL persistence parity is verified.
- Full regression passes.
- Exit review documents limitations and deferred scope.
