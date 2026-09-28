# Trusted Authorization Context — Integration Gate

Status: DESIGN / IMPLEMENTATION GATE
Date: 2026-09-28

## Decision

HTTP transport must never derive tenant, principal, or system authority from client-controlled headers.

The application already owns the authorization model through AuthorizationContext and AuthorizationPolicy. The transport layer therefore needs only an adapter seam that obtains a trusted AuthorizationContext.

The adapter contract is:

- authentication/identity infrastructure establishes the principal and scope;
- the transport dependency reads the already-established context;
- missing context fails closed;
- application commands remain responsible for authorization policy;
- tests may override the FastAPI dependency.

## Transport boundary

The initial adapter reads request.state.authorization_context.

This is intentionally not an authentication implementation. A future authentication middleware or gateway integration may populate this state after validating a real credential/token/session.

No credential parsing, JWT verification, session lookup, tenant selection, or identity header support is introduced here.

## Failure semantics

- valid trusted context -> request proceeds to application layer;
- missing context -> HTTP 503 because the service is not correctly configured with its required trust boundary;
- malformed context -> HTTP 503 rather than attempting to repair or infer identity.

## Security invariants

1. Client cannot select tenant through a normal request field.
2. Client cannot select system mode.
3. Client cannot select reviewer principal.
4. Application-level authorization remains authoritative.
5. Review approval cannot publish or execute a workflow.

## Verification

Tests must prove:

- request state context is accepted;
- absent context fails closed;
- malformed context fails closed;
- existing review API dependency override behavior remains possible;
- no client identity headers are introduced.
