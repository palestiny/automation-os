from __future__ import annotations

from fastapi import Depends, HTTPException, Request, status

from app.application.authentication import AuthenticatedPrincipal
from app.application.authorization import AuthorizationContext


def get_authenticated_principal(request: Request) -> AuthenticatedPrincipal:
    """Read identity established by trusted authentication infrastructure.

    Provider-specific credentials and client-controlled identity headers are not
    interpreted at the API boundary.
    """
    principal = getattr(request.state, "authenticated_principal", None)

    if not isinstance(principal, AuthenticatedPrincipal):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication provider is not configured",
        )

    return principal


def get_authorization_context(
    principal: AuthenticatedPrincipal = __import__("fastapi").Depends(
        get_authenticated_principal
    ),
) -> AuthorizationContext:
    """Translate trusted authentication output into application authorization."""
    return principal.to_authorization_context()
