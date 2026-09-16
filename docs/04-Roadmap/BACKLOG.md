# Backlog

## Architecture

- [ ] Consolidate duplicate ADR/documentation locations.
- [ ] Define dependency direction rules explicitly.
- [ ] Add architecture validation where useful.
- [x] Define Definition of Done.

## Domain

- [x] Establish Execution state machine baseline.
- [x] Establish Workflow aggregate baseline.
- [ ] Formalize Asset model.
- [ ] Define Outcome model.
- [ ] Define Intent model.

## Application

- [x] Implement Orchestrator baseline.
- [x] Implement ExecutionContext baseline.
- [x] Implement CapabilityDispatcher.
- [x] Implement CapabilityRegistry.
- [x] Implement RetryPolicy baseline.
- [ ] Define error taxonomy comprehensively.
- [ ] Implement JobManager live synchronization — deferred by ADR-008 until a concrete live-tracking requirement exists.

## Infrastructure

- [ ] Provider adapters.
- [ ] Persistence strategy.
- [ ] Job persistence.
- [ ] Logging.
- [ ] Observability.

## Quality

- [x] Integration tests.
- [ ] CI pipeline.
- [ ] Code quality checks.
- [ ] Test coverage policy.

## Current Focus

Phase 2 execution-engine scope has reached its Exit Gate based on the current committed scope, the 79-pass local verification, integration-level execution coverage, and the documented JobManager ownership boundary.

JobManager live synchronization is explicitly deferred. If a real requirement for live tracking appears later, it must be implemented at the application boundary while keeping Execution as the authoritative lifecycle owner.

The next project focus moves to the next roadmap phase after the Phase 2 completion state is recorded in project context.
