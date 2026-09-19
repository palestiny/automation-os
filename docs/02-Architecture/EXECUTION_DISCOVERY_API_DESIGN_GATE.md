# Execution Discovery API Design Gate

## Status

Accepted and ready for implementation.

## Purpose

Expose a read-only execution collection for dashboards and operational clients that need to monitor multiple workflow executions.

## Boundary

HTTP request -> execution discovery application use case -> execution progress projection

## Decisions

1. Execution discovery is read-only.
2. The existing ExecutionRepository remains the source of execution identities.
3. The existing ExecutionProgress projection remains the API-facing execution view.
4. No second execution state model is introduced.
5. Initial discovery supports optional deterministic filters:
   - workflow_id
   - state
6. Results are returned as a stable collection in repository order for the in-memory adapter; ordering guarantees are not part of the business contract.
7. No pagination, sorting, ownership, authentication, or persistence changes are introduced.
8. Discovery never starts, retries, resumes, cancels, or mutates an execution.
9. Individual GET /executions/{execution_id} remains authoritative for one execution.
10. Transport maps invalid state/filter input to HTTP validation errors.

## Application Boundary

DiscoverExecutions accepts optional filters and returns ExecutionProgress projections.

It must not depend on FastAPI or HTTP schemas.

## API

GET /executions

Optional:
- workflow_id
- state

Response:
- array of existing ExecutionResponse representations.

## Deferred

- pagination/cursors;
- sorting;
- authentication/authorization;
- ownership/multi-tenancy;
- historical persistence;
- event streaming;
- dashboard-specific aggregation;
- analytics.

## Exit Criteria

- repository supports read collection without changing lifecycle semantics;
- application discovery is independently testable;
- API contract covers filtering and empty results;
- discovery is strictly read-only;
- full CI passes.
