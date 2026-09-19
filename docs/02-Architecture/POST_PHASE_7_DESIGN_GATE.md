# Post-Phase-7 Design Gate

Status: **OPEN — capability not selected**  
Phase 7 status: **COMPLETED**  
Decision owner: **Project Owner**

## Purpose

This document is the required decision boundary between completed Phase 7 work and any future major capability.

It does **not** select or approve a Phase 8 capability.

No future major capability may enter implementation until this gate is completed and the Project Owner explicitly selects the capability and approves its Design Gate.

## Current State

Phase 7 — Execution Reliability and Operational Visibility is complete.

Current project position:

`Phase 7 completed → Design Gate required → next capability pending`

Safe autonomous work may continue while this gate is open:

- verification and regression testing;
- bug fixes;
- documentation and consistency maintenance;
- refactoring that preserves behavior;
- CI/tooling maintenance;
- evidence gathering for capability evaluation.

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
| Next major capability | **OPEN** |
| Capability scope | **OPEN** |
| Architecture | **OPEN** |
| Persistence changes | **OPEN** |
| External integrations | **OPEN** |
| Security/authorization impact | **OPEN** |
| Operational requirements | **OPEN** |
| Exit criteria | **OPEN** |

These are not implementation tasks until a capability is selected.

## Activation Rule

When the Project Owner selects a capability:

1. Record the selection and rationale.
2. Define or update the capability-specific Design Gate.
3. Resolve architecture and scope trade-offs.
4. Establish explicit non-goals and exit criteria.
5. Only then enter TDD RED → GREEN → REFACTOR.
6. Verify implementation and documentation.
7. Complete an exit review before declaring the capability complete.

## Prohibited While Gate Is Open

Do not:

- infer a Phase 8 capability from historical proposals;
- start implementation of a future major capability;
- create production architecture for an unselected capability;
- silently convert a candidate into a commitment;
- update `PROJECT_STATUS.md` to imply a future capability is committed.

## Authoritative References

- `PROJECT_STATUS.md`
- `AUTONOMOUS_PROJECT_DEVELOPMENT_MODE.md`
- `AGENTS.md`
- `docs/01-Roadmap/`
- `docs/02-Architecture/`
- `docs/04-DECISIONS/`

## Gate Outcome

**OPEN / WAITING FOR PROJECT OWNER CAPABILITY SELECTION**

This is an intentional project state, not an incomplete implementation.
