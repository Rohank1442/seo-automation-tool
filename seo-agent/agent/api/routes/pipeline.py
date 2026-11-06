"""
Pipeline Execution & SSE Streaming Routes.
"""

import json
from typing import Optional
from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse

from api.schemas import PipelineRunRequest, PipelineStatusResponse
from core.db import (
    ProjectStoreError,
    ProjectStoreUnavailable,
    get_project_record,
    update_project_record,
)
from services.pipeline_service import PipelineService

router = APIRouter(prefix="/pipeline", tags=["Pipeline Execution"])


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


@router.post("/{project_id}/run")
async def trigger_pipeline_run(
    project_id: str,
    payload: PipelineRunRequest,
    background_tasks: BackgroundTasks,
):
    """
    Trigger full or partial pipeline execution (v0.1 -> v0.2 -> v0.3).
    Returns immediately with run ID. Use SSE endpoint `/stream/{project_id}` for live progress.
    """
    _project_or_404(project_id)
    try:
        update_project_record(project_id, {"status": "running"})
    except ProjectStoreUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ProjectStoreError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {
        "status": "started",
        "project_id": project_id,
        "phases_queued": payload.phases,
        "dry_run": payload.dry_run,
        "sse_stream_url": f"/api/v1/pipeline/{project_id}/stream",
    }


@router.get("/{project_id}/stream")
async def stream_pipeline_progress(
    project_id: str,
    dry_run: bool = False,
    min_pages: int = 10,
    max_pages: int = 20,
):
    """
    Server-Sent Events (SSE) stream yielding real-time progress events
    for v0.1, v0.2, v0.3, and frontend compilation.
    """
    project = _project_or_404(project_id)
    user_idea = project.get("raw_description", "")

    async def event_generator():
        async for event in PipelineService.run_pipeline_stream(
            project_id=project_id,
            user_idea=user_idea,
            dry_run=dry_run,
            min_pages=min_pages,
            max_pages=max_pages,
        ):
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/{project_id}/status", response_model=PipelineStatusResponse)
def get_pipeline_status(project_id: str):
    """Poll pipeline execution status and completed artifacts."""
    _project_or_404(project_id)

    run_status = PipelineService.get_run_status(project_id)
    return PipelineStatusResponse(
        project_id=project_id,
        status=run_status.get("status", "idle"),
        current_phase=run_status.get("current_phase"),
        progress_percentage=run_status.get("progress_percentage", 0),
        phases_completed=run_status.get("phases_completed", []),
        artifacts_available={
            "v01_research": "/api/v1/pipeline/outputs/v01",
            "v02_architecture": "/api/v1/pipeline/outputs/v02",
            "v03_content": "/api/v1/pipeline/outputs/v03",
        },
    )
