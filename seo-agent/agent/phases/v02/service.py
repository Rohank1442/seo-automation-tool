"""Run the v0.2 site setup stages in their required dependency order."""

from pathlib import Path
from typing import Optional

from .architecture import run_v02_architecture
from .group_auditing import main as run_group_audit
from .internal_linking import main as run_internal_linking
from .keyword_grouping import run_v02_keyword_grouping
from .site_foundation import run_v02_site_foundation
from .technical_seo import main as run_technical_seo
from .url_architecture import run_v02_url_architecture
from .frontend_scaffold import run_frontend_scaffold


def run_v02_pipeline(
    outputs_root: Path,
    target_domain: Optional[str] = None,
) -> None:
    """Execute the existing v0.2 stages against one project's output directory."""
    project_outputs = Path(outputs_root)
    v02_outputs = project_outputs / "v02"

    # Each stage persists the artifact consumed by the next stage.
    run_v02_site_foundation(project_outputs)
    run_v02_keyword_grouping(project_outputs)
    run_group_audit(
        str(v02_outputs / "keyword_groups.json"),
        str(v02_outputs / "keyword_group_audit.json"),
    )
    run_v02_architecture(project_outputs)
    run_v02_url_architecture(project_outputs, target_domain or "https://example.com")
    run_internal_linking(project_outputs)
    run_technical_seo(project_outputs, target_domain)
    run_frontend_scaffold(project_outputs, target_domain)
