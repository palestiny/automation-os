# Automation OS — Project Status

> **Single entry point for current project state.**
>
> GitHub `master` is the source of truth. Commit/CI evidence must be verified from GitHub rather than inferred from this document.

## Current State

| Item | Status |
|---|---|
| Current phase | **Phase D — External Side-Effect Semantics Design Gate** |
| Phase D status | **Design Gate prepared; implementation not started** |
| Phase A — Repository Reconciliation | **DONE — PR #368 merged** |
| Phase B — Database Migration Boundary | **DONE — PR #369 merged** |
| Phase C — Authentication Boundary | **DONE structurally — PR #370 merged; production provider not configured** |
| Current master after Phase C | `07e08cdc63b8ef3e34da83923050ec2a3e4af621` |
| Phase C CI | **PASS — Tests run #2017 on PR #370 head** |
| Post-merge master CI for Phase C | **Not returned by workflow lookup** |
| Production authentication | **NOT COMPLETE — provider/adapter unselected and unconfigured** |
| Production secret provider | **NOT COMPLETE — fail-closed adapter remains** |
| Production readiness | **NO-GO** pending remaining hardening gates |

## Active Hardening Roadmap

1. **Phase A — Repository Reconciliation** — complete.
2. **Phase B — Database Migration Boundary** — complete.
3. **Phase C — Authentication Boundary** — structurally complete; concrete provider remains a deployment/product decision.
4. **Phase D — External Side-Effect Semantics** — current.
5. **Phase E — PostgreSQL Execution-History Concurrency Verification**.
6. **Phase F — Production Secret Provider**.
7. **Phase G — Observability + CI Hardening**.
8. **Phase H — Scalability / Performance Verification**.
9. **Production Readiness Gate**.

## Phase A — Repository Reconciliation

PR #368 is merged.

- Project status was reconciled with GitHub branch/PR state.
- Historical non-master branches were classified for explicit cleanup.
- No destructive branch deletion was performed implicitly.

## Phase B — Database Migration Boundary

PR #369 is merged.

- PostgreSQL schema ownership moved to explicit migrations.
- `schema_migrations` tracks applied versions.
- Runtime dependency composition no longer initializes or mutates schema.
- CI applies migrations before tests.
- `scripts/migrate_postgres.py` provides an explicit migration entry point.
- `PostgresSchema` remains only as a temporary compatibility facade.

A Phase-B reliability issue was also fixed: PostgreSQL repositories return detached domain objects, so `ExecuteWorkflow` now reloads the persisted execution after each step instead of continuing with stale state.

## Phase C — Authentication Boundary

PR #370 is merged.

Boundary:

`HTTP request → Authentication provider/adapter → AuthenticatedPrincipal → AuthorizationContext → AuthorizationPolicy → use case`

Implemented:
- `AuthenticatedPrincipal` as normalized trusted identity.
- `AuthenticationProvider` application port.
- API authorization consumes `request.state.authenticated_principal`.
- Client-controlled identity headers are not trusted.
- Legacy `authorization_context` request state is not accepted.
- Missing/malformed trusted authentication fails closed.

Not complete:
- No concrete OIDC/JWT/platform identity adapter has been selected or configured.
- Authentication is therefore architecturally bounded but not production-deployed.

## Phase D — External Side-Effect Semantics

Design Gate:

`docs/03-Architecture/EXTERNAL_SIDE_EFFECT_SEMANTICS_DESIGN_GATE.md`

The current capability result model is boolean-oriented and cannot safely distinguish:
- failure before an external side effect;
- confirmed external success;
- confirmed external failure;
- ambiguous outcome after a provider/network/local persistence failure.

Proposed direction:
- explicit capability outcome classification;
- explicit retryability;
- optional stable external operation/idempotency identity;
- durable ambiguity evidence;
- automatic retry blocked for UNKNOWN unless provider-supported idempotency makes repetition safe.

Explicit non-goals:
- distributed transactions;
- Kafka/event-bus introduction;
- microservices;
- two-phase commit;
- universal exactly-once semantics.

Implementation follows:

`UNDERSTAND → MAP → DESIGN → TRADE-OFFS → DECIDE → RED → GREEN → VERIFY → DOCUMENT → EXIT REVIEW`

## Verified Architectural Contracts

### Workflow / Versioning
- `Workflow` remains the logical workflow container.
- `WorkflowVersion` is the immutable executable artifact.
- Published versions are immutable.
- Executions retain their selected workflow version.
- Runtime start requires persisted PUBLISHED workflow state.
- AI-generated workflows are persisted as DRAFT before review/publication.
- AI cannot publish, execute, or mutate production workflows.

### Execution Authorization
- Tenant execution routes use trusted authorization context.
- Tenant persistence is scoped from authenticated authorization context.
- System context uses system/global persistence boundaries.
- Client identity/tenant headers are not authoritative.

### Runtime Connections
- WorkflowVersion declares provider-neutral, secret-free connection requirements.
- Tenant runtime preparation resolves persisted requirements inside the tenant boundary.
- Domain Connection persists only `secret_reference`, never secret material.
- Runtime connection write access is protected behind the internal preparation boundary.
- The current secret provider fails closed until a production secret manager is configured.

### Human Review
- Approval and publication remain separate boundaries.
- Review evidence is durable and revision-aware.
- Stale review decisions cannot publish a changed revision.

## Known Remaining Production Gaps

### P1
- Concrete authentication provider/adapter is not configured.
- Production secret provider is not implemented/configured.
- External side-effect ambiguity/idempotency semantics are not yet modeled.
- PostgreSQL execution-history append concurrency is not yet verified with a real concurrent test.
- Independent post-merge master CI verification is not consistently visible after merges.

### P2
- `app/core/execution_dependencies.py` is approaching composition/God-module complexity.
- `app/infrastructure/persistence/postgres.py` remains a large persistence module.
- API error mapping partly relies on exception/message patterns; typed application errors are a future hardening target.
- Metrics and stale-execution recovery contain full-scan/N+1 patterns that need query-oriented scaling work.
- Observability needs structured logs, correlation IDs, tracing, provider latency/error metrics, and SLO/alerting.
- CI should eventually add linting, type checking, dependency/security/secret scanning, coverage, migration verification, and smoke tests.
- No dedicated load/performance/chaos testing has established production capacity.

## Production Readiness Position

**Controlled hardening: GO**

**Production deployment: NO-GO**

The core architecture does not require a rewrite. Remaining work is boundary hardening, explicit failure semantics, operational readiness, and production infrastructure verification.

## Working Rules

Every major capability follows:

`UNDERSTAND → MAP → DESIGN → TRADE-OFFS → DECIDE → RED → GREEN → VERIFY → DOCUMENT → EXIT REVIEW`

Safe autonomous work includes repository inspection, dependency mapping, test planning, verification, documentation, and non-direction-changing cleanup.

A significant product or architecture decision remains a Project Owner decision.
