# ADR — Post-Roadmap Reliability Ownership and Retry Semantics

## Status

**ACCEPTED — Project Owner approval recorded 2026-09-22.**

## Decision

The Project Owner approved the reliability-hardening proposal combination:

- **A1 — WorkflowVersion explicit tenant ownership**
  - WorkflowVersion carries tenant_id.
  - Repository reads/writes are tenant-scoped.
  - tenant_id = NULL represents the explicit system/global ownership boundary for legacy/system artifacts.
  - Workflow/version ownership consistency is enforced at persistence boundaries.
- **B1 — MarketplaceListing tenant ownership with separate visibility**
  - MarketplaceListing carries tenant_id.
  - Repository reads/writes are tenant-scoped.
  - PUBLIC/HIDDEN controls discoverability; publication does not transfer ownership.
- **C2 — RetryPolicy governs automatic retries; authorized manual retry can override**
  - Automatic retry must remain constrained by RetryPolicy.
  - Manual intervention is a separate recovery authority and may exceed the automatic limit only with explicit authorization and auditable actor/reason context.
  - No automatic retry worker or new retry authority is activated by this decision.

## Migration Boundary

Existing nullable tenant columns/rows are preserved as the system/global compatibility boundary. No automatic reassignment of legacy rows to a tenant is performed without an explicit migration policy.

## Implementation Order

1. WorkflowVersion tenant ownership.
2. MarketplaceListing tenant ownership and visibility separation.
3. Manual/automatic retry authority contract.
4. Legacy compatibility and migration review.
5. Full regression and CI.
6. Exit review.

## Evidence

The approved source proposal is docs/02-Architecture/POST_ROADMAP_RELIABILITY_HARDENING_DESIGN_GATE.md.

Focused tests must cover cross-tenant isolation and legacy/null-tenant compatibility before the gate is considered complete.
