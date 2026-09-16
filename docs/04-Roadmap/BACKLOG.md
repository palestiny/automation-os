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
- [ ] Define and implement JobManager application-boundary synchronization, if retained in Phase 2 scope.

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

The active focus is closing the Execution Engine phase without expanding scope prematurely. The local full test suite has been reported at **79 passed** and the registry → dispatcher → orchestrator path has integration-level coverage.

The remaining execution-phase Design Gate is whether JobManager needs live synchronization with Orchestrator at an application boundary. If implemented, Execution must remain the authoritative lifecycle owner and JobManager must remain an operational adapter rather than becoming a second lifecycle aggregate.
