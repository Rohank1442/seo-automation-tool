"""v0.1 web-pipeline orchestrator; stage implementations live in focused modules."""

from pathlib import Path
from typing import Any, Dict, Optional

from core.config import validate_config
from .cluster_research import generate_project_clusters
from .competitor_research import research_competitors
from .content_gaps import analyze_content_gaps
from .project_context import extract_project_context
from .reporting import write_research_artifacts
from .summary import build_research_summary
from .keyword_research import research_cluster_keywords


def run_research_phase(
    custom_idea: str,
    project_id: str,
    output_dir: Optional[Path] = None,
    target_domain: Optional[str] = None,
) -> Dict[str, Any]:
    """Run v0.1 for an existing web project and return its artifact paths and summary."""
    print("═" * 50)
    print("      SEO AUTOMATION AGENT - PHASE v0.1 RESEARCH")
    print("═" * 50)

    idea = custom_idea.strip()
    if not idea:
        raise ValueError("v0.1 research requires a non-empty project idea.")
    if not project_id.strip():
        raise ValueError("v0.1 research requires an existing project ID.")

    validate_config()
    output_root = Path(output_dir) if output_dir else Path("outputs")
    extraction = extract_project_context(idea, project_id)
    saved_clusters = generate_project_clusters(project_id, extraction)
    keywords = research_cluster_keywords(saved_clusters, extraction)
    competitors = research_competitors(saved_clusters)
    gaps = analyze_content_gaps(saved_clusters, extraction, keywords, competitors)
    artifacts = write_research_artifacts(
        project_id=project_id,
        extraction=extraction,
        target_domain=target_domain,
        saved_clusters=saved_clusters,
        all_cluster_keywords=keywords,
        competitor_data=competitors,
        content_gaps=gaps,
        output_root=output_root,
    )
    summary = build_research_summary(saved_clusters, keywords, competitors, gaps)
    print("═" * 50)
    print(f"v0.1 complete for project {project_id}: {summary}")
    return {"status": "success", "project_id": project_id, **artifacts, "summary": summary}
