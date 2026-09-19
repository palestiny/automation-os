# Post-Phase 6 Next Milestone Proposal

Status: Proposal only — not an architectural decision

## Purpose

Phase 6 is closed for its committed scope. The repository currently has no approved Phase 7 or next capability.

This document records the concrete capability areas that should be considered before implementation resumes. It does not select one of them.

## Current baseline

The committed platform currently provides:

- canonical intent analysis and validation
- deterministic workflow selection
- explicit selected / no-match / clarification-required outcomes
- provider-neutral workflow discovery metadata and HTTP discovery
- marketplace listing publication, discovery, installation, and deterministic search
- workflow execution orchestration
- scheduled execution
- execution cancellation, resume, retry, and control APIs

The Phase 6 exit rule remains authoritative: a later phase must not begin merely because code can be written.

## Candidate next capability areas

### A. Execution reliability and operational visibility

Possible scope:

- idempotency semantics for execution start and retried operations
- execution history/audit semantics
- structured execution events
- operational observability and failure diagnosis
- correlation between workflow, execution, step, capability, and outcome

Trade-offs:

- strengthens the existing execution engine without changing the business model
- requires careful decisions about event/history ownership and persistence
- can become infrastructure-heavy if scope is not constrained
- should not silently introduce a second execution state model

Open questions:

- What constitutes an idempotency boundary?
- Is history append-only, mutable projection, or both?
- Which events are domain events versus operational telemetry?
- What must be persisted versus derived?

### B. Platform ownership and authorization boundary

Possible scope:

- users/owners
- ownership of workflows, executions, and marketplace listings
- authorization policies
- isolation between owners/tenants

Trade-offs:

- required if the platform becomes a multi-user product
- affects repository contracts, API boundaries, and persistence
- introduces security and data-isolation requirements
- should not be added as a superficial API-layer check

Open questions:

- single-user ownership first, or multi-tenant model?
- resource ownership versus role-based permissions?
- where authorization belongs relative to application use cases?
- what persistence guarantees are required?

### C. Autonomous workflow planning / generation

Possible scope:

- generate workflow candidates from intent
- semantic discovery/ranking
- parameter inference beyond deterministic validation
- planner-driven workflow composition

Trade-offs:

- advances the autonomous vision directly
- introduces nondeterminism and validation complexity
- requires clear safety boundaries before generated workflows can execute
- must preserve deterministic execution authority

Explicitly deferred today:

- autonomous workflow generation
- semantic/vector discovery
- AI workflow ranking
- autonomous planning

Any promotion of these items requires a new Design Gate.

### D. Product/API foundation

Possible scope:

- stable public API contract
- authentication
- versioning
- richer pagination/filtering
- client-facing dashboard boundary

Trade-offs:

- moves the system toward product consumption
- can lock API contracts before the domain is mature
- should follow a concrete product/user boundary rather than become generic infrastructure

## Required Design Gate before implementation

The next milestone should explicitly define:

1. Problem and user/business outcome.
2. Exact committed scope.
3. Non-goals.
4. Domain model impact.
5. Application/API boundary impact.
6. Persistence impact.
7. Determinism and failure semantics.
8. Alternatives and trade-offs.
9. TDD entry point.
10. Exit criteria and verification plan.

## Decision rule

No candidate in this document is committed.

The Project Owner must select the next capability and approve its Design Gate before implementation begins.

Once approved, the selected milestone should be added to the roadmap and implemented through the existing:

Understand → Map → Design Gate → TDD RED → GREEN → Refactor → Exit Review

workflow.
