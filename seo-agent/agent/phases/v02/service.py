"""Run the v0.2 site setup stages in their required dependency order."""

from pathlib import Path
from typing import Any, Optional

from .architecture import run_v02_architecture
from .group_auditing import main as run_group_audit
from .internal_linking_stage import main as run_internal_linking
from .keyword_grouping_stage import run_v02_keyword_grouping
from .site_foundation_stage import run_v02_site_foundation
from .technical_seo_stage import main as run_technical_seo
from .url_architecture_stage import run_v02_url_architecture
from .frontend_scaffold import run_frontend_scaffold


def run_v02_pipeline(
    outputs_root: Path,
    target_domain: Optional[str] = None,
) -> dict[str, Any]:
    """Execute v0.2 for one project and return a compact stage summary."""
    project_outputs = Path(outputs_root)
    v02_outputs = project_outputs / "v02"
    effective_domain = target_domain or "https://example.com"

    # Each stage persists the artifact consumed by the next stage.
    site_profile = run_v02_site_foundation(project_outputs)
    keyword_groups = run_v02_keyword_grouping(project_outputs)
    group_audit = run_group_audit(
        str(v02_outputs / "keyword_groups.json"),
        str(v02_outputs / "keyword_group_audit.json"),
    )
    architecture = run_v02_architecture(project_outputs)
    url_architecture = run_v02_url_architecture(project_outputs, effective_domain)
    internal_linking = run_internal_linking(project_outputs)
    technical_seo = run_technical_seo(project_outputs, effective_domain)
    frontend = run_frontend_scaffold(project_outputs, effective_domain)

    grouped_count = sum(
        len(cluster.get("groups", []))
        for cluster in keyword_groups.get("clusters", [])
    )
    return {
        "version": "0.2",
        "status": "completed",
        "summary": {
            "cluster_count": site_profile.get("cluster_count", 0),
            "keyword_groups": grouped_count,
            "audited_groups": group_audit.get("summary", {}).get("total_groups", 0),
            "architecture_pages": architecture.get("page_count", 0),
            "url_count": url_architecture.get("summary", {}).get("total_urls", 0),
            "links_mapped": internal_linking.get("summary", {}).get("total_links", 0),
            "technical_seo_status": technical_seo.get("summary", {}).get("validation_status", "unknown"),
            "frontend_pages": frontend.get("summary", {}).get("generated_pages", 0),
        },
    }
