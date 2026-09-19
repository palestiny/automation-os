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

## Current Milestone — Phase 6 Platform Generalization

Phase 6 committed scope has been completed and reviewed. The platform now supports intent-driven execution across multiple domains and a marketplace boundary for workflow discovery, publication, deterministic search and installation. Provider boundaries remain local to capabilities and analyzers; no universal provider abstraction was introduced.

The latest verified GitHub Actions run for commit `1b8b287c97a2b575a93bedd16d85cb11d8d90550` completed successfully.

The older Phase 1 milestone below is retained as historical context and is not the current project state.

## Recent Runtime Increments

Execution cancellation, execution resume, and resumed-execution orchestration are now implemented as explicit application boundaries. These increments reuse the existing Execution lifecycle and workflow orchestrator without introducing workers, queues, durable context, or universal provider infrastructure.

Execution retry is now exposed as an explicit application boundary for FAILED → RETRYING. The domain remains authoritative for the attempt increment and lifecycle transition; automatic retry policy and infrastructure remain deferred.

A caller-requested retry can now be composed through RETRYING → RUNNING and then the existing workflow orchestrator. The retry composition creates a fresh in-memory ExecutionContext and deliberately does not introduce automatic retry policy or background infrastructure.

## Next Engineering Focus

The runtime lifecycle now has explicit boundaries for start, execute, wait/resume, cancel, fail/retry and retry-and-execute. The execution-control API now exposes those existing boundaries through a thin HTTP adapter. The next increment should target a concrete product/runtime integration gap rather than adding another lifecycle state or generic abstraction.

## Journal Rule

Record what changed and why. Do not turn this document into a duplicate of the roadmap or ADRs.
