# Human Workflow Review — API Integration Gate

Status: IMPLEMENTATION GATE — approved for API/application integration
Date: 2026-09-28

## 1. Scope

Expose the already-implemented Human Workflow Review application capability through the existing FastAPI application.

The API layer must remain a transport adapter. It must not reimplement authorization, workflow lifecycle, revision calculation, idempotency, publication, or execution semantics.

Core invariant:

> Review approval != publication != execution.

## 2. Routes

The review surface is grouped under `/review/workflows` to keep review operations distinct from the existing workflow lifecycle API.

### Read operations

- `GET /review/workflows`
  - Lists visible persisted DRAFT workflows only.
- `GET /review/workflows/{workflow_id}`
  - Retrieves one visible DRAFT workflow.
- `GET /review/workflows/{workflow_id}/decisions`
  - Retrieves immutable review evidence for the workflow.

### Decision commands

- `POST /review/workflows/{workflow_id}/approve`
- `POST /review/workflows/{workflow_id}/reject`

Decision requests contain the exact `expected_revision` inspected by the reviewer.

The `Idempotency-Key` HTTP header is required for approve/reject commands.

## 3. Authorization transport boundary

The repository currently has an application-level `AuthorizationContext`, but it does not yet contain an HTTP authentication/identity provider.

Therefore the API must NOT accept tenant, principal, or system identity from ordinary client-controlled headers.

Instead:

1. An authentication/authorization adapter will establish `AuthorizationContext`.
2. The review router receives that context through a FastAPI dependency.
3. If no trusted context provider is configured, the endpoint fails closed with HTTP 503.
4. Tests may override the dependency using FastAPI's supported dependency-override mechanism.

This is deliberate. A fake `X-Tenant-Id` or `X-System` header would create an authorization bypass disguised as an API contract.

The HTTP authentication provider is a separate integration concern and is not invented by this slice.

## 4. Persistence composition

- System context uses the system-scoped workflow/review repositories.
- Tenant context uses tenant-scoped PostgreSQL repositories.
- Tenant review without durable PostgreSQL persistence is rejected rather than silently falling back to process-local storage.
- No second authorization system is introduced.

## 5. Serialization

The API exposes:

- workflow identity
- current DRAFT state
- stable review revision
- tenant ownership metadata
- validated workflow steps and conditions
- triggers
- supported goals
- required parameters and types
- automation domain
- discovery tags

Review decisions expose:

- decision id
- workflow id
- workflow revision
- tenant id
- reviewer principal
- decision
- reason
- idempotency key
- created timestamp

Responses are deterministically ordered.

## 6. Error mapping

- Missing workflow: HTTP 404.
- Workflow is not reviewable/DRAFT: HTTP 409.
- Authorization denied: HTTP 403.
- Stale review revision: HTTP 409.
- Idempotency conflict: HTTP 409.
- Invalid command data: HTTP 422 through Pydantic validation.
- Missing trusted authorization context: HTTP 503.

No API handler catches broad exceptions and converts them into client-success responses.

## 7. Explicit non-goals

This slice does not add:

- frontend/UI
- client-controlled identity headers
- authentication provider implementation
- automatic publication after approval
- automatic execution after approval
- generic audit/event infrastructure
- pagination without a concrete scale requirement
- new workflow lifecycle states

## 8. Verification gate

API tests must prove:

1. DRAFT-only listing.
2. Tenant isolation.
3. System-context isolation.
4. Single-workflow authorization.
5. Deterministic review revision exposure.
6. Decision history ordering.
7. Approve records evidence without publishing.
8. Reject records evidence without mutating workflow content.
9. Exact idempotent replay.
10. Conflicting idempotency is rejected.
11. Stale revision is rejected.
12. No execution is created by review.
13. Missing trusted authorization context fails closed.
14. Existing workflow and execution APIs remain mounted.

## 9. Exit condition

The gate is complete when:

- API contracts are covered by RED/GREEN tests.
- CI is green.
- No existing review/application invariant regresses.
- The PR is merged only after successful CI.
- Post-merge state is reconciled without claiming unverified merge-commit CI.
