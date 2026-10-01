# Authentication Boundary

## Purpose

Authentication is an infrastructure concern. The application layer must consume a
normalized, trusted identity and must not parse provider-specific credentials or
client-controlled identity headers.

## Boundary

```
HTTP request
    |
    v
Authentication provider / adapter
    |
    v
AuthenticatedPrincipal
    |
    v
AuthorizationContext
    |
    v
AuthorizationPolicy
    |
    v
Application use case
```

### Application contract

`AuthenticationProvider` is an application-facing port. Its implementation is
owned by infrastructure.

`AuthenticatedPrincipal` contains only normalized identity facts required by
authorization:

- principal id
- tenant id for tenant identities
- explicit system identity flag

It contains no access token, password, provider-specific claims, or secret
material.

### API boundary

FastAPI dependencies read only
`request.state.authenticated_principal`, which must be populated by trusted
authentication infrastructure.

The API does not trust:

- `X-User-Id`
- `X-Tenant-Id`
- client-supplied role/system flags
- a legacy `authorization_context` request-state value

Missing trusted authentication fails closed with HTTP 503 until an authentication
provider is configured.

## Provider decision

No external identity provider is selected in this phase.

The first production adapter should implement the port using a standards-based
OIDC/JWT verification flow or an equivalent platform identity service. The choice
is deliberately deferred because it depends on deployment and product identity
requirements.

## Security invariants

1. Client-controlled identity is never converted directly into authorization.
2. Tenant identity is explicit and cannot be omitted for tenant principals.
3. System identity is explicit and cannot carry a tenant.
4. Provider-specific authentication details do not cross into application/domain
   code.
5. Authorization remains separate from authentication.

## Current status

**Phase C: boundary established; production authentication provider not yet
configured.**

This is intentionally not a production-readiness claim.
