# Workflow Discovery API Design Gate

## Status

Accepted and implemented.

## Purpose

Expose the platform's existing deterministic workflow discovery capability to external clients such as dashboards and future mobile applications.

## Boundary

HTTP request → workflow discovery application use case → read-only workflow metadata

The API is a transport adapter. It does not execute workflows.

## Decisions

1. The existing `DiscoverWorkflows` application use case remains authoritative for discovery.
2. API discovery is read-only.
3. Only published workflows are returned.
4. Filtering remains deterministic and provider-neutral.
5. The initial query supports the existing canonical `goal` filter.
6. API responses expose workflow identity and selection metadata, not internal mutable state.
7. Workflow execution continues through the existing execution API/use case.
8. No database, authentication, ownership, marketplace ranking, semantic search, or AI ranking is introduced.
9. The API must not mutate workflow definitions.
10. The transport layer maps application/domain errors to HTTP responses.

## Initial Contract

GET /workflows

Optional query parameter: `goal` — canonical goal identifier.

Response items contain:
- workflow_id
- name
- supported_goals
- required_parameters
- parameter_types

## Deferred

- pagination;
- authentication/authorization;
- ownership;
- workflow creation/editing API;
- semantic search;
- marketplace search/ranking;
- execution through discovery endpoints.

## Exit Criteria

- published workflows can be discovered through HTTP;
- goal filtering matches `DiscoverWorkflows` semantics;
- draft workflows never appear;
- response contract is tested;
- discovery never starts execution.
