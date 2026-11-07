"""
Pages & Frontend Component API Routes.
"""

import json
import re
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, HTTPException

from api.schemas import (
    ExportFrontendRequest,
    ExportFrontendResponse,
    GenerateWaveRequest,
    GenerateWaveResponse,
    PageDetailResponse,
    PageSummaryResponse,
)
from phases.v03 import generate_additional_wave
from core.db import ProjectStoreError, ProjectStoreUnavailable, get_project_record
from phases.v03_export_frontend import (
    DEFAULT_EXPORT_DIR,
    ExportConfig,
    build_nextjs_app_router_page,
    build_nextjs_pages_router_page,
    build_react_spa_page,
    export_frontend_components,
    load_pages_from_directory,
)

router = APIRouter(prefix="/projects/{project_id}/pages", tags=["Pages & Content"])

AGENT_DIR = Path(__file__).resolve().parent.parent.parent
PROJECT_OUTPUTS_DIR = AGENT_DIR / "outputs" / "projects"


def _project_pages_dir(project_id: str) -> Path:
    """Resolve generated pages only after confirming the project exists."""
    if not re.fullmatch(r"[A-Za-z0-9_-]+", project_id):
        raise HTTPException(status_code=400, detail="Invalid project ID.")

    try:
        project = get_project_record(project_id)
    except ProjectStoreUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ProjectStoreError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if project is None:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")

    return PROJECT_OUTPUTS_DIR / project_id / "v03" / "pages"


def _project_page_json_path(pages_dir: Path, slug: str) -> Path:
    """Build a page path from a single safe slug segment."""
    if not re.fullmatch(r"[A-Za-z0-9_-]+", slug):
        raise HTTPException(status_code=400, detail="Invalid page slug.")
    return pages_dir / f"{slug}.json"


@router.get("", response_model=List[PageSummaryResponse])
def list_generated_pages(project_id: str):
    """List all generated pages for a project with health scores and metadata."""
    pages_dir = _project_pages_dir(project_id)
    if not pages_dir.exists():
        return []

    pages = load_pages_from_directory(pages_dir)
    summaries = []

    for p in pages:
        slug = p.get("slug", "untitled")
        meta = p.get("metadata", {})
        brief = p.get("brief", {})

        title = brief.get("meta_title") or meta.get("seo_title") or p.get("title", slug.replace("-", " ").title())
        h1 = brief.get("h1") or p.get("h1") or p.get("title", "")
        p_kw = p.get("primary_keyword") or (p.get("keywords", [None])[0] if p.get("keywords") else None)

        summaries.append(
            PageSummaryResponse(
                slug=slug,
                url_path=f"/{slug}/",
                title=title,
                h1=h1,
                primary_keyword=p_kw,
                secondary_keywords=p.get("secondary_keywords", []),
                cluster=p.get("cluster", "General"),
                page_type=p.get("page_type", "guide"),
                search_intent=p.get("search_intent", "informational"),
                word_count=p.get("word_count", 500),
                health_score=float(p.get("audit_result", {}).get("total_score", 100)),
                schema_type=p.get("schema_type", "Article"),
                has_jsx_component=True,
            )
        )

    return summaries


@router.get("/{slug}", response_model=PageDetailResponse)
def get_page_detail(project_id: str, slug: str):
    """Get full details of a specific page: markdown content, FAQ items, and pre-rendered Next.js JSX."""
    pages_dir = _project_pages_dir(project_id)
    json_path = _project_page_json_path(pages_dir, slug)
    if not json_path.exists():
        raise HTTPException(status_code=404, detail=f"Page with slug '{slug}' not found.")

    with open(json_path, "r", encoding="utf-8") as f:
        p = json.load(f)

    meta = p.get("metadata", {})
    brief = p.get("brief", {})
    title = brief.get("meta_title") or meta.get("seo_title") or p.get("title", "")
    h1 = brief.get("h1") or p.get("h1") or p.get("title", "")
    description = brief.get("meta_description") or meta.get("meta_description", "")
    canonical = p.get("canonical_url") or meta.get("canonical_url", f"https://example.com/{slug}/")

    # Generate Next.js App Router JSX
    cfg = ExportConfig(framework="next-app", language="ts", styling="tailwind")
    nextjs_code = build_nextjs_app_router_page(p, cfg)

    faqs = p.get("faq", {}).get("faq_items", []) or p.get("faq_items", [])
    raw_links = p.get("internal_links", [])
    clean_links = [
        {
            "target_slug": l.get("target_url", "").strip("/"),
            "target_url": l.get("target_url", ""),
            "anchor_text": l.get("anchor_text", ""),
            "relationship": l.get("relationship", "related_guide"),
        }
        for l in raw_links
    ]

    return PageDetailResponse(
        slug=slug,
        url_path=f"/{slug}/",
        title=title,
        h1=h1,
        meta_description=description,
        canonical_url=canonical,
        robots=meta.get("robots", "index, follow"),
        schema_type=p.get("schema_type", "Article"),
        primary_keyword=p.get("primary_keyword"),
        secondary_keywords=p.get("secondary_keywords", []),
        cluster=p.get("cluster", "General"),
        page_type=p.get("page_type", "guide"),
        search_intent=p.get("search_intent", "informational"),
        word_count=p.get("word_count", 500),
        health_score=float(p.get("audit_result", {}).get("total_score", 100)),
        markdown_content=p.get("markdown_content", ""),
        nextjs_jsx_code=nextjs_code,
        faqs=faqs,
        internal_links=clean_links,
        schema_json_ld={
            "@context": "https://schema.org",
            "@type": p.get("schema_type", "Article"),
            "headline": h1,
            "description": description,
        },
        validation_issues=p.get("audit_result", {}).get("issues", []),
    )


@router.post("/export", response_model=ExportFrontendResponse)
def export_pages_to_frontend(project_id: str, payload: ExportFrontendRequest):
    """Compile and export all pages to drop-in Next.js or React components."""
    pages_dir = _project_pages_dir(project_id)
    if not pages_dir.exists():
        raise HTTPException(status_code=400, detail="No generated pages found. Run v0.3 first.")

    pages = load_pages_from_directory(pages_dir)
    out_dir = Path(payload.output_dir).resolve() if payload.output_dir else DEFAULT_EXPORT_DIR / project_id

    cfg = ExportConfig(
        framework=payload.framework,
        language=payload.language,
        styling=payload.styling,
        output_dir=out_dir,
        non_interactive=True,
    )

    count, dest = export_frontend_components(pages, cfg)

    return ExportFrontendResponse(
        status="success",
        exported_count=count,
        destination_directory=str(dest),
        framework=payload.framework,
        language=payload.language,
        styling=payload.styling,
        message=f"Exported {count} components to {dest}. Ready for copy-paste into your site.",
    )


@router.post("/generate-wave", response_model=GenerateWaveResponse)
def trigger_additional_wave(project_id: str, payload: GenerateWaveRequest):
    """
    Generate an additional wave of pages without overwriting existing content.
    Supports:
      - Option A: 'next_best' (Top unbuilt candidates ranked across all clusters)
      - Option B: 'specific_cluster' (Candidates for a selected topical cluster)
    """
    try:
        pages_dir = _project_pages_dir(project_id)
        project_outputs_dir = pages_dir.parents[1]
        result = generate_additional_wave(
            strategy_name=payload.strategy,
            batch_size=payload.batch_size,
            cluster_name=payload.cluster_name,
            dry_run=payload.dry_run,
            output_dir=project_outputs_dir / "v03",
            pipeline_inputs_dir=project_outputs_dir,
        )
        return GenerateWaveResponse(
            status=result["status"],
            strategy_applied=result.get("strategy_applied", payload.strategy),
            cluster_name=result.get("cluster_name"),
            pages_generated_count=result.get("pages_generated_count", 0),
            generated_slugs=result.get("generated_slugs", []),
            total_project_pages=result.get("total_project_pages", 0),
            message=result.get("message", "Wave completed successfully."),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Wave generation failed: {str(e)}")

