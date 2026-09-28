from __future__ import annotations

from fastapi import HTTPException, Request, status

from app.application.authorization import AuthorizationContext


def get_authorization_context(request: Request) -> AuthorizationContext:
    """Read a trusted context established by authentication infrastructure.

    This dependency intentionally does not parse client-controlled identity headers.
    """
    context = getattr(request.state, "authorization_context", None)

    if not isinstance(context, AuthorizationContext):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authorization context provider is not configured",
        )

    return context
