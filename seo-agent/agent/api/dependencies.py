"""Authentication and approval dependencies for product API routes."""

import logging
from dataclasses import dataclass
from typing import Optional

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from core.db import (
    ProjectStoreError,
    ProjectStoreUnavailable,
    get_db_client,
    is_access_request_approved,
)

logger = logging.getLogger("api.auth")
bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class ApprovedUser:
    """Identity fields trusted only after Supabase validates the bearer token."""

    id: str
    email: str


def get_approved_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> ApprovedUser:
    """Validate the Supabase access token and require an approved email request."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="A valid Supabase bearer token is required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    client = get_db_client()
    if client is None:
        raise HTTPException(status_code=503, detail="Authentication service is unavailable.")

    try:
        response = client.auth.get_user(credentials.credentials)
    except Exception as exc:
        status = getattr(exc, "status", None) or getattr(exc, "status_code", None)
        if status in (400, 401, 403):
            raise HTTPException(
                status_code=401,
                detail="The Supabase access token is invalid or expired.",
                headers={"WWW-Authenticate": "Bearer"},
            ) from exc
        logger.exception("Could not validate Supabase access token")
        raise HTTPException(status_code=503, detail="Authentication service is unavailable.") from exc

    user = getattr(response, "user", None)
    user_id = getattr(user, "id", None)
    email = getattr(user, "email", None)
    if not user_id or not email:
        raise HTTPException(
            status_code=401,
            detail="The Supabase access token has no authenticated user.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        approved = is_access_request_approved(email)
    except (ProjectStoreUnavailable, ProjectStoreError) as exc:
        logger.exception("Could not check access approval")
        raise HTTPException(status_code=503, detail="Access approval service is unavailable.") from exc

    if not approved:
        raise HTTPException(status_code=403, detail="This account does not have an approved access request.")

    return ApprovedUser(id=str(user_id), email=email.strip().lower())
