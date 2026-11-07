"""Coordinate project-scoped JSON and Markdown artifact persistence for v0.1."""

import json
from pathlib import Path
from typing import Any, Dict, Optional

from .artifact_builder import build_page_opportunities
from .logging_utils import print_separator
from .markdown_report import write_markdown_report


def write_research_artifacts(
    project_id: str,
    extraction,
    target_domain: Optional[str],
    saved_clusters,
    all_cluster_keywords,
    competitor_data,
    content_gaps,
    output_root: Path,
) -> Dict[str, Any]:
    """Save the machine-readable inputs and human-readable report for downstream use."""
    print_separator()
    print("\n[Step 9] Saving SEO research and page-planning reports...")
    print_separator()

    output_root.mkdir(parents=True, exist_ok=True)
    report_file = output_root / "research_report.md"
    opportunities_file = output_root / "page_opportunities.json"
    page_opportunities = build_page_opportunities(
        project_id=project_id,
        extraction=extraction,
        target_domain=target_domain,
        saved_clusters=saved_clusters,
        all_cluster_keywords=all_cluster_keywords,
        competitor_data=competitor_data,
        content_gaps=content_gaps,
    )

    with opportunities_file.open("w", encoding="utf-8") as output_file:
        json.dump(page_opportunities, output_file, indent=2, ensure_ascii=False)
    print(f"Page-planning data saved to: {opportunities_file}")

    write_markdown_report(
        report_path=report_file,
        extraction=extraction,
        saved_clusters=saved_clusters,
        all_cluster_keywords=all_cluster_keywords,
        competitor_data=competitor_data,
        content_gaps=content_gaps,
    )
    print(f"Human-readable report saved to: {report_file}")
    print(f"Machine-readable page opportunities saved to: {opportunities_file}")

    return {
        "report_path": report_file,
        "page_opportunities_path": opportunities_file,
        "page_opportunities": page_opportunities,
    }
