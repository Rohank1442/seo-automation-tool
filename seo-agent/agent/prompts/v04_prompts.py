"""
v0.4 — Indexing Watch & Early Signal Detection Prompts & Response Schemas.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class EarlySignalAnalysis(BaseModel):
    slug: str
    headline_insight: str
    status_category: str = Field(
        ...,
        description="One of: 'indexed_and_alive', 'indexed_silent', 'invisible_anomaly', 'breakout_candidate'"
    )
    observed_queries: List[str] = Field(default_factory=list, description="Mined queries showing impressions")
    actionable_recommendation: str = Field(..., description="Specific recommendation for this page")


class AnomalyItem(BaseModel):
    severity: str = Field(..., description="'info', 'warning', or 'critical'")
    title: str
    affected_pages: List[str] = Field(default_factory=list)
    root_cause_diagnosis: str
    suggested_fix: str


class IndexingReportSummary(BaseModel):
    executive_summary: str
    total_pages_monitored: int
    indexed_count: int
    invisible_count: int
    overall_health_verdict: str
    anomalies_detected: List[AnomalyItem]
    page_analyses: List[EarlySignalAnalysis]
    strategic_next_steps: List[str]
