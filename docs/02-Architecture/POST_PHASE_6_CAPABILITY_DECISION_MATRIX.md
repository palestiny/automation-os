# Post-Phase 6 Capability Decision Matrix

## Status

Neutral decision-support artifact. This document does not rank, score, or select a capability.

## Comparison dimensions

| Dimension | A — Reliability / Visibility | B — Ownership / Authorization | C — Planning / Generation | D — Product / API |
|---|---|---|---|---|
| Primary boundary | Execution | Resource/application access | Intent → planning → workflow | HTTP/product contract |
| Existing foundation | Execution lifecycle, repository, controls, progress | Workflow/execution/marketplace boundaries | Intent, discovery, deterministic selection | Existing FastAPI/application boundaries |
| Main new contract | Idempotency/history/events | Identity/ownership/policy | Bounded planner output | Consumer-facing API contract |
| Main domain impact | Execution-centric | Cross-domain | Cross intent/discovery/execution | Primarily transport/application, potentially identity |
| Determinism concern | Duplicate-command semantics | Policy consistency | AI output must remain non-authoritative | Contract/compatibility stability |
| Main persistence question | Idempotency/history/event storage | Ownership/isolation | Planner artifacts, if persisted | Resource/API state only where required |
| TDD starting point | Duplicate command behavior | Unauthorized resource operation | Invalid planner output blocked | First stable consumer contract |
| Explicit safety boundary | One lifecycle authority | Application authorization | Deterministic validation before execution | Stable contract before publication |

## Dependency questions

### A — Reliability / Visibility

Depends on a precise command boundary before implementation. It can be designed around the existing Execution aggregate without changing the existing lifecycle authority.

### B — Ownership / Authorization

Requires a product-level identity/ownership decision before entity changes are safe. It potentially affects several existing resource types.

### C — Planning / Generation

Requires a precise definition of what AI is allowed to produce. It must preserve deterministic validation and execution authority.

### D — Product / API

Requires a concrete consumer and stable capability boundary. Authentication and authorization cannot be designed independently of the ownership decision.

## Existing deferred boundaries that must remain visible

The current repository already records several intentionally deferred concerns, including ownership/authentication, pagination/sorting, historical persistence, event streaming, analytics, and autonomous replanning in earlier Design Gates.

Any new milestone must explicitly distinguish:

- previously deferred scope being activated;
- genuinely new scope;
- scope that remains deferred.

## Decision inputs required from the Project Owner

The next Design Gate can be finalized once the Project Owner determines:

1. The capability area to activate.
2. The concrete outcome expected from that capability.
3. Any product constraint that changes its scope.
4. Whether previously deferred related concerns should remain deferred.

No implementation should begin from this matrix alone.

## Engineering sequence after selection

**Selected capability → finalized Design Gate → RED test → GREEN implementation → refactor → full verification → exit review**

