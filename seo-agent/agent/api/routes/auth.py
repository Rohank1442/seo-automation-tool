"""Authentication endpoints for custom email/password authentication and session management."""

import logging
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from api.dependencies import ApprovedUser, get_approved_user
from api.schemas import (
    AuthTokenResponse,
    UserResponse,
    UserSignInRequest,
    UserSignUpRequest,
)
from core.config import AUTH_COOKIE_NAME, JWT_ACCESS_TOKEN_EXPIRE_MINUTES
from core.db import (
    ProjectStoreError,
    ProjectStoreUnavailable,
    create_user_record,
    get_access_request_status,
    get_user_by_email,
    mark_access_request_registered,
)
from core.security import create_access_token, hash_password, verify_password

logger = logging.getLogger("api.auth")

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _set_auth_cookie(response: Response, token: str) -> None:
    """Set the JWT token in an HTTP-only secure session cookie."""
    response.set_cookie(
        key=AUTH_COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,  # Set to True in production with HTTPS
        max_age=JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )


def _clear_auth_cookie(response: Response) -> None:
    """Clear the session cookie."""
    response.delete_cookie(
        key=AUTH_COOKIE_NAME,
        path="/",
    )


@router.post(
    "/sign-up",
    response_model=AuthTokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account with approved email and password",
)
def sign_up(payload: UserSignUpRequest, response: Response):
    """Register an account for an email address that has an approved early-access request."""
    email = payload.email.strip().lower()

    # 1. Check if user already exists
    try:
        existing_user = get_user_by_email(email)
    except (ProjectStoreUnavailable, ProjectStoreError) as exc:
        logger.exception("Database error checking user existence")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service is unavailable. Please try again later.",
        ) from exc

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists. Please sign in.",
        )

    # 2. Check early-access approval status
    try:
        req_status = get_access_request_status(email)
    except (ProjectStoreUnavailable, ProjectStoreError) as exc:
        logger.exception("Database error checking access request status")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Access check service is unavailable. Please try again later.",
        ) from exc

    if req_status is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No access request found for this email. Please request access first on the website.",
        )
    if req_status == "pending":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your email is currently waiting for admin approval. You will be able to register once approved.",
        )
    if req_status == "declined":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your access request was declined.",
        )
    if req_status == "registered":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account for this email has already been registered. Please sign in.",
        )
    if req_status != "approved":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access request is not approved for signup.",
        )

    # 3. Hash password and insert user record
    hashed = hash_password(payload.password)
    try:
        user_record = create_user_record(
            email=email,
            hashed_password=hashed,
            full_name=payload.full_name,
        )
    except (ProjectStoreUnavailable, ProjectStoreError) as exc:
        logger.exception("Failed to insert user record")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not complete registration. Please try again.",
        ) from exc

    # 4. Mark access request as registered
    try:
        mark_access_request_registered(email)
    except Exception as exc:
        logger.warning("Could not mark access request as registered: %s", exc)

    # 5. Issue JWT and set cookie
    user_id = str(user_record["id"])
    token = create_access_token(user_id=user_id, email=email)
    _set_auth_cookie(response, token)

    return AuthTokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse(
            id=user_id,
            email=email,
            full_name=user_record.get("full_name"),
            created_at=str(user_record.get("created_at") or ""),
        ),
    )


@router.post(
    "/sign-in",
    response_model=AuthTokenResponse,
    summary="Sign in with email and password",
)
def sign_in(payload: UserSignInRequest, response: Response):
    """Authenticate with email and password, issuing a JWT session cookie."""
    email = payload.email.strip().lower()

    # 1. Fetch user by email
    try:
        user = get_user_by_email(email)
    except (ProjectStoreUnavailable, ProjectStoreError) as exc:
        logger.exception("Database error fetching user on sign-in")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service is unavailable. Please try again later.",
        ) from exc

    if not user:
        # Check if user has an access request to provide actionable feedback
        try:
            req_status = get_access_request_status(email)
        except Exception:
            req_status = None

        if req_status == "pending":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your email is currently waiting for admin approval.",
            )
        if req_status == "approved":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Your email has been approved! Please sign up first to set your password.",
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    # 2. Verify active status
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated.",
        )

    # 3. Verify password hash
    hashed_password = user.get("hashed_password") or ""
    if not verify_password(payload.password, hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    # 4. Issue JWT and set session cookie
    user_id = str(user["id"])
    token = create_access_token(user_id=user_id, email=email)
    _set_auth_cookie(response, token)

    return AuthTokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse(
            id=user_id,
            email=email,
            full_name=user.get("full_name"),
            created_at=str(user.get("created_at") or ""),
        ),
    )


@router.post(
    "/sign-out",
    summary="Sign out and clear session cookie",
)
def sign_out(response: Response):
    """Sign out the current user by clearing the session cookie."""
    _clear_auth_cookie(response)
    return {"message": "Successfully signed out."}


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current authenticated user profile",
)
def get_current_user_profile(user: ApprovedUser = Depends(get_approved_user)):
    """Return the profile of the currently authenticated user."""
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=getattr(user, "full_name", None),
    )


@router.get(
    "/access",
    summary="Check session approval status",
)
def get_access_status(user: ApprovedUser = Depends(get_approved_user)):
    """Return success only when the session belongs to an authenticated, approved user."""
    return {
        "approved": True,
        "user": {
            "id": user.id,
            "email": user.email,
        },
    }
