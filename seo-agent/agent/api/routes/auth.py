"""Authenticated session access-status endpoint used by the frontend router."""

from fastapi import APIRouter, Depends

from api.dependencies import ApprovedUser, get_approved_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get("/access")
def get_access_status(user: ApprovedUser = Depends(get_approved_user)):
    """Return success only when the bearer token belongs to an approved user."""
    return {"approved": True}
