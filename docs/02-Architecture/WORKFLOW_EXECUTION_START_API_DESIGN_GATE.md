# Workflow Execution Start API Design Gate

## Status

Accepted / Implemented

## Purpose

Expose the existing StartWorkflowExecution application boundary through HTTP so a published workflow can be turned into a persisted RUNNING Execution.

## Committed Decisions

1. The API accepts a workflow UUID in the route.
2. StartWorkflowExecution remains the authority for published-workflow validation and Execution creation/start.
3. The API returns the existing Execution projection used by execution-control endpoints.
4. Missing workflows map to HTTP 404.
5. Invalid workflow lifecycle state maps to HTTP 409.
6. No workflow creation, editing, publication, or parameter mutation is introduced here.
7. No background worker or immediate workflow execution is introduced; this endpoint only starts the Execution.
8. The existing in-memory repositories remain the composition dependency.

## TDD Order

### RED

Prove published workflows create persisted RUNNING executions, draft workflows are rejected, and missing workflows map to 404.

### GREEN

Add one thin API route and compose StartWorkflowExecution from the existing repositories.

### REFACTOR

Keep HTTP mapping in app/api and workflow/execution lifecycle in existing domain/application boundaries.

## Explicitly Deferred

- workflow authoring API;
- workflow publication API;
- request parameter transport/validation for workflow execution;
- authentication/authorization;
- durable persistence;
- background execution.
