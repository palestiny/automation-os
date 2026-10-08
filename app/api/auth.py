from __future__ import annotations

from fastapi import Depends, HTTPException, Request, status

from app.application.authentication import AuthenticatedPrincipal
from app.application.authorization import AuthorizationContext


def get_authenticated_principal(request: Request) -> AuthenticatedPrincipal:
    """Read identity established by trusted authentication infrastructure."""
    principal = getattr(request.state, "authenticated_principal", None)
    if isinstance(principal, AuthenticatedPrincipal):
        return principal

    authentication_error = getattr(request.state, "authentication_error", None)
    if authentication_error == "invalid":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="A valid bearer token is required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Authentication provider is not configured",
    )


def get_authorization_context(
    principal: AuthenticatedPrincipal = Depends(get_authenticated_principal),
) -> AuthorizationContext:
    """Translate trusted authentication output into application authorization."""
    return principal.to_authorization_context()
