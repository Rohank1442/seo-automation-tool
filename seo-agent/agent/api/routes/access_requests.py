"""Public early-access request endpoint."""

from fastapi import APIRouter, HTTPException

from api.schemas import AccessRequestCreate, AccessRequestResponse
from core.db import (
    ProjectStoreError,
    ProjectStoreUnavailable,
    save_access_request,
)

router = APIRouter(prefix="/access-requests", tags=["Early Access"])


@router.post("", response_model=AccessRequestResponse, status_code=202)
def request_early_access(payload: AccessRequestCreate) -> AccessRequestResponse:
    """Store a request for manual review; this does not create a project or run the pipeline."""
    try:
        save_access_request(payload.email, payload.use_case)
    except ProjectStoreUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ProjectStoreError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return AccessRequestResponse()
