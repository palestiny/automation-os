# Development History

Status: Living document

This journal records meaningful project milestones, architectural progress and changes in direction. It is intentionally concise; detailed rationale belongs in ADRs and learning documents.

## Foundation

- Initial FastAPI foundation established.
- Execution introduced as the central runtime concept.
- Execution lifecycle and state transitions were implemented and tested.
- Retry lifecycle was introduced.
- Initial workflow and capability abstractions were established.
- Automated tests became part of the development loop.

## Architecture Direction

The project evolved from an initial content-automation concept into **Automation OS**: a general automation platform whose core concern is turning intent into executable workflows and business outcomes.

The current architectural direction is a modular monolith with explicit separation between domain concepts, application orchestration, capabilities and infrastructure.

## Current Milestone — Phase 7 Execution Reliability

Phase 7 — **Execution Reliability and Operational Visibility** — is completed and merged.

The milestone established:

- workflow-start idempotency;
- deterministic duplicate behavior;
- append-only execution lifecycle evidence;
- minimal structured execution events;
- execution/workflow correlation through execution evidence;
- explicit operational evidence failure semantics.

The existing `Execution` aggregate remains the sole lifecycle authority. History and events are evidence only and do not introduce a second state model.

The implementation was merged through PR **#207** with merge commit:

`e4635f3ecfd9e4aba37ea92daf051c3c0df9d516`

The Phase 7 exit review confirms that ownership/authorization, autonomous planning, generic product/API foundation, cross-command idempotency, durable production persistence architecture, and generic event/tracing infrastructure remain deferred.

## Phase 6 — Historical Milestone

Phase 6 committed scope was completed and reviewed. The platform now supports intent-driven execution across multiple domains and a marketplace boundary for workflow discovery, publication, deterministic search and installation. Provider boundaries remain local to capabilities and analyzers; no universal provider abstraction was introduced.

The latest verified GitHub Actions run for commit `1b8b287c97a2b575a93bedd16d85cb11d8d90550` completed successfully.

The older Phase 1 milestone below is retained as historical context and is not the current project state.

## Recent Runtime Increments

Execution cancellation, execution resume, and resumed-execution orchestration are now implemented as explicit application boundaries. These increments reuse the existing Execution lifecycle and workflow orchestrator without introducing workers, queues, durable context, or universal provider infrastructure.

Execution retry is now exposed as an explicit application boundary for FAILED → RETRYING. The domain remains authoritative for the attempt increment and lifecycle transition; automatic retry policy and infrastructure remain deferred.

A caller-requested retry can now be composed through RETRYING → RUNNING and then the existing workflow orchestrator. The retry composition creates a fresh in-memory ExecutionContext and deliberately does not introduce automatic retry policy or background infrastructure.

## Next Engineering Focus

Phase 9 Observability / Metrics is complete for its committed operational-metrics scope. The next planned capability is the AI Planning Layer. No implementation has been started; an explicit Design Gate and Project Owner decision are required before that capability is activated.

Safe autonomous engineering may continue for repository inspection, architecture mapping, documentation, test planning, consistency fixes, verification, and other work that does not silently commit a new architecture.

## Journal Rule

Record what changed and why. Do not turn this document into a duplicate of the roadmap or ADRs.

## Execution Control API Composition

Added a thin HTTP composition layer over the verified Execution application boundaries. The API exposes progress, cancel, resume, retry, and retry-and-execute without duplicating lifecycle logic. Contract tests cover success, missing execution, and invalid transitions; the final GitHub Actions run passed the full suite.

## Phase 9 — Observability / Metrics

Phase 9 Design Gate is accepted with **Option A**: derive operational metrics from existing Execution and ExecutionHistory evidence. The implementation is intentionally read-only and keeps Execution as the lifecycle authority. Persisted metric counters and a generic telemetry/event pipeline remain deferred.

The first increment defines an application query boundary for execution totals, state counts, completed duration statistics, retry/recovery event counts, workflow/version breakdowns, and attempt distribution. In-memory and PostgreSQL verification passed, the full GitHub Actions test workflow passed, and the Phase 9 exit review is complete. Persisted metric counters and a generic telemetry/event pipeline remain deferred.
