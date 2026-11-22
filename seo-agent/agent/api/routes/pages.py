"""
Pages & Frontend Component API Routes.
"""

import re
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from api.dependencies import ApprovedUser, get_approved_user
from api.schemas import (
    DownloadPagesRequest,
    ExportFrontendRequest,
    ExportFrontendResponse,
    GenerateWaveRequest,
    GenerateWaveResponse,
    PageDetailResponse,
    PageSummaryResponse,
)
from phases.v03 import generate_additional_wave
from core.db import (
    ProjectStoreError,
    ProjectStoreUnavailable,
    get_generated_page_record,
    get_project_record,
    list_generated_page_records,
    update_project_record,
)
from phases.v03_export_frontend import (
    DEFAULT_EXPORT_DIR,
    ExportConfig,
    build_nextjs_app_router_page,
    build_nextjs_pages_router_page,
    build_react_spa_page,
    compile_pages_to_zip_buffer,
    export_frontend_components,
    normalize_download_base_url,
    zip_download_filename,
)

router = APIRouter(
    prefix="/projects/{project_id}/pages",
    tags=["Pages & Content"],
    dependencies=[Depends(get_approved_user)],
)

AGENT_DIR = Path(__file__).resolve().parent.parent.parent
PROJECT_OUTPUTS_DIR = AGENT_DIR / "outputs" / "projects"


def _project_pages_dir(project_id: str, owner_id: str) -> Path:
    """Resolve generated pages only after confirming the project exists."""
    if not re.fullmatch(r"[A-Za-z0-9_-]+", project_id):
        raise HTTPException(status_code=400, detail="Invalid project ID.")

    try:
        project = get_project_record(project_id, owner_id=owner_id)
    except ProjectStoreUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ProjectStoreError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if project is None:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")

    return PROJECT_OUTPUTS_DIR / project_id / "v03" / "pages"


def _page_record_to_artifact(page: dict) -> dict:
    """Adapt a database page row to the legacy page renderer's input shape."""
    cluster_record = page.get("clusters") or {}
    if isinstance(cluster_record, list):
        cluster_record = cluster_record[0] if cluster_record else {}
    cluster_name = cluster_record.get("name") or "General"
    meta_title = page.get("meta_title") or page.get("title", "")
    return {
        "page_id": page.get("source_page_id") or str(page.get("id", "")),
        "slug": page.get("slug", ""),
        "url": page.get("url_path") or f"/{page.get('slug', '')}/",
        "title": page.get("title", ""),
        "h1": page.get("h1", ""),
        "page_type": page.get("page_type", "guide"),
        "search_intent": page.get("search_intent", "informational"),
        "cluster": cluster_name,
        "primary_keyword": page.get("primary_keyword"),
        "secondary_keywords": page.get("secondary_keywords") or [],
        "word_count": page.get("word_count", 0),
        "markdown_content": page.get("markdown_content", ""),
        "schema_type": page.get("schema_type", "Article"),
        "brief": {
            "meta_title": meta_title,
            "meta_description": page.get("meta_description", ""),
            "canonical_url": page.get("canonical_url", ""),
            "h1": page.get("h1", ""),
            "schema_type": page.get("schema_type", "Article"),
        },
        "metadata": {
            "seo_title": meta_title,
            "meta_description": page.get("meta_description", ""),
            "canonical_url": page.get("canonical_url", ""),
            "robots": page.get("robots", "index, follow"),
            "schema_type": page.get("schema_type", "Article"),
        },
        "faq": {"faq_items": page.get("faqs") or []},
        "internal_links": page.get("internal_links") or [],
        "audit_result": {
            "total_score": float(page.get("health_score", 100)),
            "issues": page.get("validation_issues") or [],
        },
    }


def _get_owned_page_records(project_id: str, owner_id: str) -> List[dict]:
    """Validate project ownership and fetch its durable generated pages."""
    _project_pages_dir(project_id, owner_id)
    try:
        return list_generated_page_records(project_id)
    except ProjectStoreUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ProjectStoreError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("", response_model=List[PageSummaryResponse])
def list_generated_pages(project_id: str, user: ApprovedUser = Depends(get_approved_user)):
    """List the durable page records for a project owned by the signed-in user."""
    pages = _get_owned_page_records(project_id, user.id)

    summaries = []
    for row in pages:
        page = _page_record_to_artifact(row)
        brief = page["brief"]
        summaries.append(
            PageSummaryResponse(
                slug=page["slug"],
                url_path=page["url"],
                title=brief.get("meta_title") or page["title"],
                h1=page["h1"],
                primary_keyword=page["primary_keyword"],
                secondary_keywords=page["secondary_keywords"],
                cluster=page["cluster"],
                page_type=page["page_type"],
                search_intent=page["search_intent"],
                word_count=page["word_count"],
                health_score=page["audit_result"]["total_score"],
                schema_type=page["schema_type"],
                has_jsx_component=True,
            )
        )
    return summaries


@router.get("/{slug}", response_model=PageDetailResponse)
def get_page_detail(
    project_id: str,
    slug: str,
    user: ApprovedUser = Depends(get_approved_user),
):
    """Get full details of a specific page: markdown content, FAQ items, and pre-rendered Next.js JSX."""
    _project_pages_dir(project_id, user.id)  # validates the ID and project ownership
    if not re.fullmatch(r"[A-Za-z0-9_-]+", slug):
        raise HTTPException(status_code=400, detail="Invalid page slug.")
    try:
        record = get_generated_page_record(project_id, slug)
    except ProjectStoreUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ProjectStoreError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    if record is None:
        raise HTTPException(status_code=404, detail=f"Page with slug '{slug}' not found.")

    p = _page_record_to_artifact(record)

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
def export_pages_to_frontend(
    project_id: str,
    payload: ExportFrontendRequest,
    user: ApprovedUser = Depends(get_approved_user),
):
    """Compile and export all pages to drop-in Next.js or React components."""
    page_records = _get_owned_page_records(project_id, user.id)
    if not page_records:
        raise HTTPException(status_code=400, detail="No generated pages found. Run v0.3 first.")

    pages = [_page_record_to_artifact(row) for row in page_records]
    project_export_root = (DEFAULT_EXPORT_DIR / project_id).resolve()
    out_dir = Path(payload.output_dir).resolve() if payload.output_dir else project_export_root
    try:
        out_dir.relative_to(project_export_root)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail="Export output must stay within this project's export directory.",
        ) from exc

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


@router.post("/download")
def download_pages_zip(
    project_id: str,
    payload: DownloadPagesRequest,
    user: ApprovedUser = Depends(get_approved_user),
):
    """Compile generated pages into a Next.js ZIP and return it as a file download."""
    page_records = _get_owned_page_records(project_id, user.id)
    if not page_records:
        raise HTTPException(status_code=400, detail="No generated pages found. Run v0.3 first.")

    base_url = normalize_download_base_url(payload.base_url)
    if not base_url:
        raise HTTPException(status_code=400, detail="Enter a base URL.")

    try:
        project = get_project_record(project_id, owner_id=user.id)
    except ProjectStoreUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ProjectStoreError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if project is None:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")

    stored_domain = normalize_download_base_url(project.get("target_domain") or "")
    if base_url != stored_domain:
        try:
            updated = update_project_record(
                project_id,
                {"target_domain": base_url},
                owner_id=user.id,
            )
        except ProjectStoreUnavailable as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except ProjectStoreError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        if updated is None:
            raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")

    try:
        pages = [_page_record_to_artifact(row) for row in page_records]
        zip_bytes, _count = compile_pages_to_zip_buffer(pages, base_url)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    filename = zip_download_filename(project.get("name") or "project")
    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/generate-wave", response_model=GenerateWaveResponse)
def trigger_additional_wave(
    project_id: str,
    payload: GenerateWaveRequest,
    user: ApprovedUser = Depends(get_approved_user),
):
    """
    Generate an additional wave of pages without overwriting existing content.
    Supports:
      - Option A: 'next_best' (Top unbuilt candidates ranked across all clusters)
      - Option B: 'specific_cluster' (Candidates for a selected topical cluster)
    """
    try:
        pages_dir = _project_pages_dir(project_id, user.id)
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

