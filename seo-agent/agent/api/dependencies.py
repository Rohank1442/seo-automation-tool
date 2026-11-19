"""Authentication and approval dependencies for product API routes."""

import logging
from dataclasses import dataclass
from typing import Optional
import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from core.config import AUTH_COOKIE_NAME
from core.db import (
    ProjectStoreError,
    ProjectStoreUnavailable,
    get_db_client,
    get_user_by_id,
    is_access_request_approved,
)
from core.security import decode_access_token

logger = logging.getLogger("api.auth")
bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class ApprovedUser:
    """Identity fields for an authenticated, approved platform user."""

    id: str
    email: str
    full_name: Optional[str] = None


def get_approved_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> ApprovedUser:
    """Validate user authentication via custom JWT (Bearer header or session cookie)

    Falls back to Supabase auth validation for backwards compatibility if needed.
    """
    token: Optional[str] = None

    # 1. Prefer Authorization: Bearer <token> header
    if credentials and credentials.scheme.lower() == "bearer" and credentials.credentials:
        token = credentials.credentials.strip()

    # 2. Fall back to HTTP-only session cookie
    if not token:
        token = request.cookies.get(AUTH_COOKIE_NAME)

    if not token:
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Please sign in.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Attempt to decode custom platform JWT token
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        email = payload.get("email")

        if not user_id or not email:
            raise HTTPException(
                status_code=401,
                detail="Invalid token payload.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Verify against database users table
        try:
            user_record = get_user_by_id(str(user_id))
        except (ProjectStoreUnavailable, ProjectStoreError) as exc:
            logger.exception("Database error retrieving user by id")
            raise HTTPException(status_code=503, detail="Authentication service is unavailable.") from exc

        if not user_record:
            raise HTTPException(
                status_code=401,
                detail="User account no longer exists.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user_record.get("is_active", True):
            raise HTTPException(
                status_code=403,
                detail="User account has been deactivated.",
            )

        return ApprovedUser(
            id=str(user_record["id"]),
            email=str(user_record["email"]).strip().lower(),
            full_name=user_record.get("full_name"),
        )

    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=401,
            detail="Session has expired. Please sign in again.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    except jwt.InvalidTokenError:
        # 4. Fallback: Check if token is a legacy Supabase GoTrue access token
        client = get_db_client()
        if client is not None:
            try:
                response = client.auth.get_user(token)
                sb_user = getattr(response, "user", None)
                sb_user_id = getattr(sb_user, "id", None)
                sb_email = getattr(sb_user, "email", None)

                if sb_user_id and sb_email:
                    if is_access_request_approved(sb_email, allow_registered=True):
                        return ApprovedUser(
                            id=str(sb_user_id),
                            email=sb_email.strip().lower(),
                        )
            except Exception:
                pass

        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
