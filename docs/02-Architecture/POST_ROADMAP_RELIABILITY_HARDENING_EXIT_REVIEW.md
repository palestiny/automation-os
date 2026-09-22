# Post-Roadmap Reliability Hardening — Exit Review

## Status

**COMPLETED — 2026-09-22.**

## Approved Decisions

- A1: WorkflowVersion has explicit tenant ownership and tenant-scoped persistence.
- B1: MarketplaceListing has explicit tenant ownership; PUBLIC/HIDDEN remains separate from ownership.
- C2: RetryPolicy is the authority for policy-constrained retries; manual retry can override the automatic policy only through explicit authorization with actor/reason context.

## Implemented

- Added tenant_id to WorkflowVersion and MarketplaceListing domains.
- Propagated tenant ownership through workflow-version creation and legacy auto-materialization.
- Scoped in-memory and PostgreSQL version/listing repositories by tenant.
- Added PostgreSQL tenant-aware workflow-version uniqueness and preserved nullable legacy/system ownership.
- Enforced listing/version tenant consistency during marketplace publication and discovery.
- Added ManualRetryContext and authorization hook for policy overrides.
- Added focused in-memory and PostgreSQL isolation tests, cross-tenant write rejection tests, retry-policy tests, manual override tests, and null-tenant compatibility coverage.

## Verification

GitHub Actions Tests run #1720 completed successfully with **604 passed**.

GitHub Actions Tests run #1721 reached a completed-success test job with **605 passed in 3.46s**, including the final legacy/null-tenant compatibility coverage.

The final verified test job for commit cfedbb76e4a7027e0c05308e9d553bbc1ded5c12 is green. The workflow run metadata may remain briefly in progress while GitHub finalizes the run record.

## Retry Audit Boundary

The current retry boundary records manual actor/reason context at the application authorization hook. The execution event schema was not expanded because there is no committed automatic retry worker or dedicated retry-audit repository in the current architecture. Adding durable manual-retry audit events remains a future architecture decision if operational requirements require platform-owned audit storage.

## Migration Boundary

Legacy rows with NULL tenant_id remain system/global artifacts. No automatic tenant reassignment was introduced.

## Result

The approved reliability hardening gate is complete. The repository returns to the safe post-roadmap maintenance/verification boundary. Any further major retry-audit storage, worker, or tenancy expansion requires a new Design Gate.
