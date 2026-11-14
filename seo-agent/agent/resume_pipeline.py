"""Resume a project pipeline from a persisted stage artifact."""

import argparse
from pathlib import Path
from typing import Any, Callable

from core.db import get_project_record
from phases.v02.group_auditing import main as run_group_audit
from phases.v02.internal_linking_stage import main as run_internal_linking
from phases.v02.site_architecture.runner import run_v02_architecture
from phases.v02.site_foundation_stage import run_v02_site_foundation
from phases.v02.technical_seo_stage import main as run_technical_seo
from phases.v02.url_architecture_stage import run_v02_url_architecture
from phases.v02.keyword_grouping_stage import run_v02_keyword_grouping
from phases.v02.frontend_scaffold import run_frontend_scaffold
from phases.v03_content_generation import run_content_generation_phase
from phases.v03_export_frontend import (
    DEFAULT_EXPORT_DIR,
    ExportConfig,
    export_frontend_components,
    load_pages_from_directory,
)


AGENT_DIR = Path(__file__).resolve().parent
PROJECT_OUTPUTS_DIR = AGENT_DIR / "outputs" / "projects"

STAGES = (
    "v02-site-foundation",
    "v02-keyword-grouping",
    "v02-group-audit",
    "v02-architecture",
    "v02-url-architecture",
    "v02-internal-linking",
    "v02-technical-seo",
    "v02-frontend",
    "v03",
)

REQUIRED_ARTIFACTS = {
    "v02-site-foundation": ("page_opportunities.json",),
    "v02-keyword-grouping": (
        "page_opportunities.json",
        "v02/site_profile.json",
    ),
    "v02-group-audit": ("v02/keyword_groups.json",),
    "v02-architecture": (
        "page_opportunities.json",
        "v02/site_profile.json",
        "v02/keyword_groups.json",
        "v02/keyword_group_audit.json",
    ),
    "v02-url-architecture": ("v02/site_architecture.json",),
    "v02-internal-linking": (
        "v02/site_architecture.json",
        "v02/url_architecture.json",
    ),
    "v02-technical-seo": (
        "v02/site_architecture.json",
        "v02/url_architecture.json",
        "v02/internal_linking.json",
    ),
    "v02-frontend": (
        "v02/url_architecture.json",
        "v02/internal_linking.json",
        "v02/technical_seo.json",
    ),
    "v03": (
        "research_report.md",
        "v02/site_architecture.json",
        "v02/keyword_groups.json",
        "v02/keyword_group_audit.json",
        "v02/url_architecture.json",
        "v02/internal_linking.json",
        "v02/technical_seo.json",
    ),
}


def _missing_artifacts(project_outputs: Path, stage: str) -> list[Path]:
    """List the persisted inputs required to start at the selected stage."""
    return [
        project_outputs / relative_path
        for relative_path in REQUIRED_ARTIFACTS[stage]
        if not (project_outputs / relative_path).is_file()
    ]


def _build_stage_actions(
    project_outputs: Path,
    project_id: str,
    target_domain: str,
    dry_run_v03: bool,
    max_pages: int,
    export_v03_frontend: bool,
) -> dict[str, Callable[[], Any]]:
    """Bind each resumable phase to the selected project's output directory."""
    v02_dir = project_outputs / "v02"

    def run_v03() -> dict[str, Any]:
        result = run_content_generation_phase(
            dry_run=dry_run_v03,
            max_pages=max_pages,
            output_dir=project_outputs / "v03",
            pipeline_inputs_dir=project_outputs,
        )
        if export_v03_frontend:
            pages_dir = project_outputs / "v03" / "pages"
            if pages_dir.exists():
                pages = load_pages_from_directory(pages_dir)
                config = ExportConfig(
                    non_interactive=True,
                    output_dir=DEFAULT_EXPORT_DIR / project_id,
                )
                export_frontend_components(pages, config)
        return result

    return {
        "v02-site-foundation": lambda: run_v02_site_foundation(project_outputs),
        "v02-keyword-grouping": lambda: run_v02_keyword_grouping(project_outputs),
        "v02-group-audit": lambda: run_group_audit(
            v02_dir / "keyword_groups.json",
            v02_dir / "keyword_group_audit.json",
        ),
        "v02-architecture": lambda: run_v02_architecture(project_outputs),
        "v02-url-architecture": lambda: run_v02_url_architecture(
            project_outputs, target_domain
        ),
        "v02-internal-linking": lambda: run_internal_linking(project_outputs),
        "v02-technical-seo": lambda: run_technical_seo(
            project_outputs, target_domain
        ),
        "v02-frontend": lambda: run_frontend_scaffold(
            project_outputs, target_domain
        ),
        "v03": run_v03,
    }


def resume_pipeline(
    project_id: str,
    from_stage: str,
    target_domain: str | None = None,
    dry_run_v03: bool = False,
    max_pages: int = 20,
    export_v03_frontend: bool = True,
) -> None:
    """Run the selected stage and all later stages using saved project artifacts."""
    if not project_id or any(char in project_id for char in "/\\") or project_id in {".", ".."}:
        raise ValueError("Project ID must be a single safe path component.")
    if from_stage not in STAGES:
        raise ValueError(f"Unknown resume stage '{from_stage}'. Choose from: {', '.join(STAGES)}")

    project = get_project_record(project_id)
    if project is None:
        raise ValueError(f"Project '{project_id}' was not found in project storage.")

    project_outputs = PROJECT_OUTPUTS_DIR / project_id
    selected_index = STAGES.index(from_stage)
    missing = _missing_artifacts(project_outputs, from_stage)
    if missing:
        missing_list = "\n  - ".join(str(path) for path in missing)
        raise FileNotFoundError(
            f"Cannot resume from '{from_stage}'. Required artifacts are missing:\n  - {missing_list}"
        )

    effective_domain = (
        target_domain
        or project.get("target_domain")
        or "https://example.com"
    )
    actions = _build_stage_actions(
        project_outputs,
        project_id,
        effective_domain,
        dry_run_v03,
        max_pages,
        export_v03_frontend,
    )

    print(f"Resuming project {project_id} from {from_stage}.")
    for stage in STAGES[selected_index:]:
        print(f"\n=== Running {stage} ===")
        try:
            actions[stage]()
        except Exception as exc:
            print(f"Resume stopped at '{stage}': {exc}")
            print(f"After addressing the failure, rerun with --from-stage {stage}.")
            raise
        print(f"=== Completed {stage} ===")

    print(f"\nResume completed for project {project_id}.")


def main() -> None:
    """Parse CLI options and resume the selected project pipeline."""
    parser = argparse.ArgumentParser(
        description="Resume a project pipeline from a persisted v0.2 or v0.3 stage."
    )
    parser.add_argument("--project-id", required=True, help="Existing project ID from Supabase.")
    parser.add_argument(
        "--from-stage",
        required=True,
        choices=STAGES,
        help="First stage to rerun. Later stages run in order.",
    )
    parser.add_argument(
        "--target-domain",
        help="Override the project's saved target domain for the remaining stages.",
    )
    parser.add_argument(
        "--dry-run-v03",
        action="store_true",
        help="Use v0.3's dry-run generation mode after v0.2 completes.",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=20,
        help="Maximum first-wave pages for v0.3 (default: 20).",
    )
    parser.add_argument(
        "--skip-v03-frontend-export",
        action="store_true",
        help="Skip exporting generated v0.3 pages into the frontend project.",
    )
    args = parser.parse_args()

    resume_pipeline(
        project_id=args.project_id,
        from_stage=args.from_stage,
        target_domain=args.target_domain,
        dry_run_v03=args.dry_run_v03,
        max_pages=args.max_pages,
        export_v03_frontend=not args.skip_v03_frontend_export,
    )


if __name__ == "__main__":
    main()
