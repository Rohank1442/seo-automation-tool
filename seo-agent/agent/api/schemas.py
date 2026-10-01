"""
Pydantic API Request and Response Schemas for SEO Automation Platform.
Covers:
  - Project management (problem statement submission, metadata)
  - Pipeline execution (v0.1, v0.2, v0.3, full runs, SSE events)
  - Generated pages & Next.js/React component inspection
  - v0.4 Indexing Watch & Early Signal Detection metrics & alerts
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ============================================================
# PROJECT SCHEMAS
# ============================================================

class ProjectCreateRequest(BaseModel):
    name: Optional[str] = Field(None, description="Human-readable project name (auto-generated if omitted)")
    raw_description: str = Field(..., description="User's initial website idea, niche, or problem statement")
    target_audience: Optional[str] = Field(None, description="Target customer persona / audience")
    target_domain: Optional[str] = Field("https://example.com", description="Target domain for canonical URLs")
    primary_goal: Optional[str] = Field("Rank for high-intent long-tail keywords and drive organic search traffic", description="Core SEO objective")


class ProjectUpdateRequest(BaseModel):
    name: Optional[str] = None
    target_domain: Optional[str] = None
    target_audience: Optional[str] = None
    status: Optional[str] = None


class ProjectResponse(BaseModel):
    id: str
    name: str
    raw_description: str
    target_domain: str
    target_audience: Optional[str] = None
    status: str = "created"  # created, researching, architecture, generating, completed, failed
    current_phase: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None
    clusters_count: int = 0
    keywords_count: int = 0
    pages_count: int = 0
    health_score: float = 100.0


# ============================================================
# PIPELINE EXECUTION & SSE SCHEMAS
# ============================================================

class PipelineRunRequest(BaseModel):
    phases: List[str] = Field(default=["v01", "v02", "v03"], description="List of phases to run: ['v01', 'v02', 'v03']")
    dry_run: bool = Field(default=False, description="Run in offline deterministic template mode without calling live external LLM APIs")
    min_pages: int = Field(default=10, description="Minimum pages to generate in First Wave")
    max_pages: int = Field(default=20, description="Maximum pages to generate in First Wave")
    export_frontend: bool = Field(default=True, description="Automatically export Next.js components to generated-pages/ upon completion")


class PipelineEvent(BaseModel):
    project_id: str
    phase: str  # "v01_research", "v02_architecture", "v03_content_generation", "v04_monitoring"
    step: str
    message: str
    progress_percentage: int = 0
    status: str = "in_progress"  # "in_progress", "completed", "warning", "error"
    data_preview: Optional[Dict[str, Any]] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class PipelineStatusResponse(BaseModel):
    project_id: str
    status: str
    current_phase: Optional[str] = None
    progress_percentage: int = 0
    phases_completed: List[str] = []
    artifacts_available: Dict[str, str] = {}
    last_event: Optional[PipelineEvent] = None


# ============================================================
# GENERATED PAGES SCHEMAS
# ============================================================

class FAQItemSchema(BaseModel):
    question: str
    answer: str
    target_question_keyword: Optional[str] = None


class InternalLinkItemSchema(BaseModel):
    target_slug: str
    target_url: str
    anchor_text: str
    relationship: str = "related_guide"


class PageSummaryResponse(BaseModel):
    slug: str
    url_path: str
    title: str
    h1: str
    primary_keyword: Optional[str] = None
    secondary_keywords: List[str] = []
    cluster: str
    page_type: str
    search_intent: str
    word_count: int
    health_score: float
    schema_type: str
    has_jsx_component: bool = True


class PageDetailResponse(BaseModel):
    slug: str
    url_path: str
    title: str
    h1: str
    meta_description: str
    canonical_url: str
    robots: str = "index, follow"
    schema_type: str = "Article"
    primary_keyword: Optional[str] = None
    secondary_keywords: List[str] = []
    cluster: str
    page_type: str
    search_intent: str
    word_count: int
    health_score: float
    markdown_content: str
    nextjs_jsx_code: str
    faqs: List[FAQItemSchema] = []
    internal_links: List[InternalLinkItemSchema] = []
    schema_json_ld: Dict[str, Any] = {}
    validation_issues: List[str] = []


class ExportFrontendRequest(BaseModel):
    framework: str = Field(default="next-app", description="'next-app' (App Router), 'next-pages', or 'react-spa'")
    language: str = Field(default="ts", description="'ts' (.tsx) or 'js' (.jsx)")
    styling: str = Field(default="tailwind", description="'tailwind' or 'semantic'")
    output_dir: Optional[str] = Field(None, description="Custom export path on disk")


class ExportFrontendResponse(BaseModel):
    status: str = "success"
    exported_count: int
    destination_directory: str
    framework: str
    language: str
    styling: str
    message: str


# ============================================================
# v0.4 INDEXING WATCH & MONITORING SCHEMAS
# ============================================================

class GSCMetricSyncRequest(BaseModel):
    site_url: Optional[str] = None
    days_back: int = Field(default=30, description="Number of historical days to inspect from Google Search Console")
    mock_if_no_creds: bool = Field(default=True, description="Generate realistic monitoring signals if GSC API credentials are not yet configured")


class PageIndexStatus(BaseModel):
    slug: str
    url: str
    is_indexed: bool
    index_verdict: str  # "INDEXED", "CRAWLED_NOT_INDEXED", "DISCOVERED_NOT_INDEXED", "NOT_FOUND"
    first_detected_date: Optional[str] = None
    impressions_7d: int = 0
    clicks_7d: int = 0
    avg_position: float = 0.0
    status_category: str  # "indexed_and_alive", "indexed_silent", "invisible_anomaly", "breakout_candidate"
    top_mined_queries: List[str] = []


class MonitoringAlert(BaseModel):
    id: str
    severity: str  # "info", "warning", "critical"
    alert_type: str  # "indexing_anomaly", "zero_impressions_4w", "cannibalization_risk", "breakout_query"
    page_slug: Optional[str] = None
    message: str
    recommendation: str
    created_at: str


class MonitoringDashboardResponse(BaseModel):
    project_id: str
    total_pages_monitored: int
    indexed_pages_count: int
    indexed_percentage: float
    total_impressions_7d: int
    total_clicks_7d: int
    avg_click_through_rate: float
    pages: List[PageIndexStatus]
    active_alerts: List[MonitoringAlert]
    category_breakdown: Dict[str, int]
    last_synced_at: str
    recommendations_summary: List[str]
