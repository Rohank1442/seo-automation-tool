"""
v0.4 Indexing Watch & Monitoring API Routes.
"""

from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import ApprovedUser, get_approved_user
from api.schemas import GSCMetricSyncRequest, MonitoringDashboardResponse
from core.db import ProjectStoreError, ProjectStoreUnavailable, get_project_record
from phases.v04_monitoring import run_v04_monitoring

router = APIRouter(
    prefix="/monitoring",
    tags=["v0.4 Indexing Watch"],
    dependencies=[Depends(get_approved_user)],
)

AGENT_DIR = Path(__file__).resolve().parent.parent.parent


def _owned_report_path(project_id: str, owner_id: str) -> Path:
    """Return a project report path only after confirming the caller owns it."""
    try:
        project = get_project_record(project_id, owner_id=owner_id)
    except ProjectStoreUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ProjectStoreError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if project is None:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")
    return AGENT_DIR / "outputs" / "projects" / project_id / "v04" / "indexing_report.json"


@router.get("/{project_id}/dashboard", response_model=MonitoringDashboardResponse)
def get_monitoring_dashboard(
    project_id: str,
    user: ApprovedUser = Depends(get_approved_user),
):
    """
    Get current v0.4 Indexing Watch & Early Signal Detection dashboard:
    Indexation rate, impressions, clicks, status categories, anomalies, and recommendations.
    """
    report_json_path = _owned_report_path(project_id, user.id)
    if not report_json_path.exists():
        # Automatically run initial monitoring analysis if report does not yet exist
        report_data = run_v04_monitoring(days_back=30, project_id=project_id)
    else:
        import json
        with open(report_json_path, "r", encoding="utf-8") as f:
            report_data = json.load(f)

    summary = report_data.get("summary", {})
    pages = report_data.get("pages", [])
    alerts = report_data.get("alerts", [])
    recommendations = report_data.get("strategic_recommendations", [])

    return MonitoringDashboardResponse(
        project_id=project_id,
        total_pages_monitored=summary.get("total_pages_monitored", len(pages)),
        indexed_pages_count=summary.get("indexed_pages_count", 0),
        indexed_percentage=summary.get("indexed_percentage", 0.0),
        total_impressions_7d=summary.get("total_impressions_7d", 0),
        total_clicks_7d=summary.get("total_clicks_7d", 0),
        avg_click_through_rate=summary.get("avg_click_through_rate", 0.0),
        pages=pages,
        active_alerts=alerts,
        category_breakdown=summary.get("category_breakdown", {}),
        last_synced_at=report_data.get("generated_at", ""),
        recommendations_summary=recommendations,
    )


@router.post("/{project_id}/sync", response_model=MonitoringDashboardResponse)
def sync_monitoring_metrics(
    project_id: str,
    payload: GSCMetricSyncRequest,
    user: ApprovedUser = Depends(get_approved_user),
):
    """
    Trigger a fresh sync of Google Search Console indexation & query impression metrics.
    """
    _owned_report_path(project_id, user.id)
    run_v04_monitoring(days_back=payload.days_back, project_id=project_id)
    return get_monitoring_dashboard(project_id, user)
