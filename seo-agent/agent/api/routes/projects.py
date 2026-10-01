"""
Projects API Routes.
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException

from api.schemas import ProjectCreateRequest, ProjectResponse, ProjectUpdateRequest

router = APIRouter(prefix="/projects", tags=["Projects"])

# In-memory store for projects (mirrors DB / local file state)
PROJECTS_STORE: Dict[str, Dict] = {
    "default-project": {
        "id": "default-project",
        "name": "Virtual Try-On Fashion SEO",
        "raw_description": "A programmatic fashion tech website providing virtual try-on tools, clothing design apps, and shopping guides for online fashion enthusiasts.",
        "target_domain": "https://example.com",
        "target_audience": "Online shoppers, fashion designers, e-commerce brand owners",
        "status": "completed",
        "current_phase": "v03_content_generation",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "clusters_count": 3,
        "keywords_count": 140,
        "pages_count": 10,
        "health_score": 100.0,
    }
}


@router.post("", response_model=ProjectResponse)
def create_project(payload: ProjectCreateRequest):
    """Create a new SEO automation project from user's website idea / problem statement."""
    project_id = str(uuid.uuid4())[:8]
    name = payload.name or f"Project-{payload.raw_description[:30].strip()}..."

    project_data = {
        "id": project_id,
        "name": name,
        "raw_description": payload.raw_description,
        "target_domain": payload.target_domain or "https://example.com",
        "target_audience": payload.target_audience or "General search audience",
        "status": "created",
        "current_phase": "init",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "clusters_count": 0,
        "keywords_count": 0,
        "pages_count": 0,
        "health_score": 100.0,
    }

    PROJECTS_STORE[project_id] = project_data
    return project_data


@router.get("", response_model=List[ProjectResponse])
def list_projects():
    """List all projects."""
    return list(PROJECTS_STORE.values())


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: str):
    """Get project details and execution status."""
    if project_id not in PROJECTS_STORE:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")
    return PROJECTS_STORE[project_id]


@router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(project_id: str, payload: ProjectUpdateRequest):
    """Update project details."""
    if project_id not in PROJECTS_STORE:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")

    p = PROJECTS_STORE[project_id]
    if payload.name is not None:
        p["name"] = payload.name
    if payload.target_domain is not None:
        p["target_domain"] = payload.target_domain
    if payload.target_audience is not None:
        p["target_audience"] = payload.target_audience
    if payload.status is not None:
        p["status"] = payload.status

    p["updated_at"] = datetime.now(timezone.utc).isoformat()
    return p
