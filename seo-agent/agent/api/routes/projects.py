"""
Projects API Routes.
"""

import uuid
from typing import List
from fastapi import APIRouter, HTTPException

from api.schemas import ProjectCreateRequest, ProjectResponse, ProjectUpdateRequest
from core.db import (
    ProjectStoreError,
    ProjectStoreUnavailable,
    create_project_record,
    get_project_record,
    list_project_records,
    update_project_record,
)

router = APIRouter(prefix="/projects", tags=["Projects"])

def _project_or_404(project_id: str) -> dict:
    try:
        project = get_project_record(project_id)
    except ProjectStoreUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ProjectStoreError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if project is None:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")
    return project


@router.post("", response_model=ProjectResponse)
def create_project(payload: ProjectCreateRequest):
    """Create a new SEO automation project from user's website idea / problem statement."""
    project_id = str(uuid.uuid4())
    name = payload.name or f"Project-{payload.raw_description[:30].strip()}..."

    project_data = {
        "id": project_id,
        "name": name,
        "raw_description": payload.raw_description,
        "target_domain": payload.target_domain or "https://example.com",
        "target_audience": payload.target_audience or "General search audience",
        "primary_goal": payload.primary_goal,
        "status": "created",
        "current_phase": "init",
    }

    try:
        return create_project_record(project_data)
    except ProjectStoreUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ProjectStoreError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("", response_model=List[ProjectResponse])
def list_projects():
    """List all projects."""
    try:
        return list_project_records()
    except ProjectStoreUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ProjectStoreError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: str):
    """Get project details and execution status."""
    return _project_or_404(project_id)


@router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(project_id: str, payload: ProjectUpdateRequest):
    """Update project details."""
    _project_or_404(project_id)
    updates = payload.model_dump(exclude_none=True)
    try:
        project = update_project_record(project_id, updates)
    except ProjectStoreUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ProjectStoreError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if project is None:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")
    return project
