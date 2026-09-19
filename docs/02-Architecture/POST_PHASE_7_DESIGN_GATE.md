# Post-Phase-7 Design Gate

Status: **OPEN — capability not selected**  
Phase 7 functional status: **COMPLETED — hardening verified**  
Decision owner: **Project Owner**

## Purpose

This document is the required decision boundary between completed Phase 7 work and any future major capability.

It does **not** select or approve a Phase 8 capability.

No future major capability may enter implementation until:

1. this gate is completed;
2. the Project Owner explicitly selects the next capability;
3. the selected capability has an approved Design Gate.

## Current State

Phase 7 — Execution Reliability and Operational Visibility is functionally complete and hardening-verified.

Deep hardening identified an end-to-end concurrent idempotency gap. The Project Owner selected **Option A — Atomic reservation + execution persistence**, and PR **#232** implemented the selected coordination model.

The implementation introduced an explicit ExecutionStartRepository boundary. The current in-memory adapter coordinates idempotency registration and execution persistence under one lock, and duplicate lookup uses the same boundary.

GitHub Actions run **#969** for PR #232 completed successfully with **470 tests passed**.

The authoritative hardening review is:

- docs/02-Architecture/PHASE_7_DEEP_VERIFICATION_REVIEW.md
- docs/04-DECISIONS/PHASE_7_IDEMPOTENCY_CONCURRENCY_DECISION.md

Current project position:

Phase 7 functional complete → hardening verified → this gate → next capability pending

### Durable persistence limitation

The selected Option A contract is verified for the current in-memory persistence model.

A future durable adapter must provide an equivalent transaction or atomic persistence primitive before it is considered production-compatible with this contract. This gate does not silently assume that an in-memory lock provides durable cross-process/database atomicity.

## Safe Autonomous Work

While the next capability remains unselected, safe autonomous work may continue for:

- verification and regression testing;
- bug fixes;
- documentation and consistency maintenance;
- refactoring that preserves behavior;
- CI/tooling maintenance;
- evidence gathering for capability evaluation;
- architectural analysis that does not select or implement the next major capability.

## Candidate Capability

**Selected capability:** None

**Decision:** Pending Project Owner selection.

Candidate proposals may be documented here, but documenting a candidate does not commit it.

## Candidate Evaluation Contract

Any proposed major capability should be evaluated against:

1. **Business value** — what concrete problem does it solve?
2. **Domain impact** — which existing domain concepts change or are introduced?
3. **Architectural impact** — which boundaries, contracts, persistence, or runtime responsibilities change?
4. **Dependencies** — what must exist before implementation?
5. **Risk** — correctness, reliability, security, operational, and migration risks.
6. **Testability** — how the behavior can be verified before implementation is considered complete.
7. **Scope** — what is explicitly in and out.
8. **Alternatives** — viable alternatives and their trade-offs.
9. **Exit criteria** — objective conditions for completion.
10. **Deferred consequences** — what remains intentionally outside the capability.

## Decision Record

| Decision | Status |
|---|---|
| Phase 7 hardening completion | **VERIFIED** |
| Idempotency coordination model | **DECIDED — Option A** |
| Next major capability | **OPEN** |
| Capability scope | **OPEN** |
| Architecture | **OPEN** |
| Persistence changes | **OPEN** |
| External integrations | **OPEN** |
| Security/authorization impact | **OPEN** |
| Operational requirements | **OPEN** |
| Exit criteria | **OPEN** |

These are not implementation tasks until the relevant decision is selected and approved.

## Activation Rule

Before any future major capability enters implementation:

1. the Project Owner explicitly selects the capability;
2. its business/domain/architecture trade-offs are recorded;
3. its Design Gate is written and approved;
4. objective RED tests are defined where applicable;
5. implementation proceeds through RED → GREEN → REFACTOR;
6. verification and regression are completed;
7. the relevant project status and decision documents are updated.

## Prohibited While Gate Is Open

Do not:

- infer a Phase 8 capability from historical proposals;
- start implementation of a future major capability;
- create production architecture for an unselected capability;
- silently convert a candidate into a commitment;
- update PROJECT_STATUS.md to imply a future capability is committed;
- replace the selected idempotency coordination model with another model without a new Project Owner decision.

## Authoritative References

- PROJECT_STATUS.md
- AUTONOMOUS_PROJECT_DEVELOPMENT_MODE.md
- AGENTS.md
- docs/02-Architecture/PHASE_7_DEEP_VERIFICATION_REVIEW.md
- docs/04-DECISIONS/PHASE_7_IDEMPOTENCY_CONCURRENCY_DECISION.md
- docs/01-Roadmap/
- docs/02-Architecture/

## Gate Outcome

**OPEN / WAITING FOR EXPLICIT PROJECT OWNER SELECTION OF THE NEXT MAJOR CAPABILITY**
