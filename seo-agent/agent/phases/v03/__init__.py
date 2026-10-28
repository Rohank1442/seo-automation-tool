"""
v0.3 Content Generation & Validation — Top-Level Facade, Wave Orchestrator & CLI.

Exports:
- `run_content_generation_phase`: Full legacy CLI/API runner with all flags.
- `generate_additional_wave`: Multi-wave expansion engine supporting Option A & Option B.
- `main()`: Full CLI runner supporting all arguments.
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from phases.v03.candidate_loader import (
    build_unified_page_candidates,
    load_all_pipeline_inputs,
    save_page_candidates,
    load_json_file,
)
from phases.v03.models import (
    FirstWaveSelectionConfig,
    FirstWaveSelectionManifest,
    GeneratedPageResult,
    LoadedArtifacts,
    NormalizedPageCandidate,
    PageCandidatesManifest,
    PageContext,
    SelectedPage,
)
from phases.v03.pipeline import (
    create_default_generation_pipeline,
    generate_all_content_briefs,
    generate_structured_content_brief,
    process_single_page_from_brief,
)
from phases.v03.selection import (
    CandidateSelectionStrategy,
    NextBestStrategy,
    SpecificClusterStrategy,
    StrategyFactory,
    save_selected_pages,
    score_page_candidate,
    select_first_wave_pages,
)
from phases.v03.validator import (
    export_content_manifest,
    export_generated_content_json,
    generate_v03_summary_report,
    perform_full_content_validation,
    validate_single_page_content,
)

logger = logging.getLogger("v03")

# Path constants
BASE_DIR = Path(__file__).resolve().parent.parent.parent
OUTPUTS_DIR = BASE_DIR / "outputs"
V03_OUTPUTS_DIR = OUTPUTS_DIR / "v03"
V03_PAGES_DIR = V03_OUTPUTS_DIR / "pages"


def configure_logging(level: int = logging.INFO) -> logging.Logger:
    """Configure structured logging."""
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [v0.3] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(level)
    return logger


def load_existing_page_slugs(pages_dir: Path) -> Set[str]:
    """Inspects outputs directory and returns set of already-generated page slugs."""
    if not pages_dir.exists():
        return set()
    return {f.stem for f in pages_dir.glob("*.json")}


def save_page_artifacts(result: GeneratedPageResult, pages_dir: Path):
    """Save markdown and JSON file for a generated page."""
    pages_dir.mkdir(parents=True, exist_ok=True)
    slug = result.slug.strip("/").replace("/", "_") or "home"
    md_file = pages_dir / f"{slug}.md"
    json_file = pages_dir / f"{slug}.json"

    with open(md_file, "w", encoding="utf-8") as f:
        f.write(result.markdown_content)

    payload = {
        "page_id": result.page_id,
        "slug": result.slug,
        "url": result.url,
        "title": result.title,
        "page_type": result.page_type,
        "cluster": result.cluster,
        "primary_keyword": result.primary_keyword,
        "secondary_keywords": result.secondary_keywords,
        "word_count": result.word_count,
        "brief": result.brief,
        "markdown_content": result.markdown_content,
        "metadata": result.metadata,
        "faq": result.faq,
        "internal_links": result.embedded_internal_links,
        "audit_result": result.audit,
        "generated_at": result.generated_at,
    }

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


def generate_additional_wave(
    strategy_name: str = "next_best",
    batch_size: int = 25,
    cluster_name: Optional[str] = None,
    dry_run: bool = False,
    output_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Executes a multi-wave page expansion batch without touching already published pages.
    Supports Strategy Pattern:
    - Option A: 'next_best'
    - Option B: 'specific_cluster'
    """
    configure_logging()
    out_dir = output_dir or V03_OUTPUTS_DIR
    pages_dir = out_dir / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting Multi-Wave Expansion: Strategy='{strategy_name}' | Batch={batch_size} | Cluster='{cluster_name}'")

    artifacts = load_all_pipeline_inputs()
    candidates_manifest = build_unified_page_candidates(artifacts)

    existing_slugs = load_existing_page_slugs(pages_dir)
    logger.info(f"Found {len(existing_slugs)} already generated pages on disk.")

    strategy: CandidateSelectionStrategy = StrategyFactory.get(strategy_name)
    selected_candidates = strategy.select(
        candidates=candidates_manifest.candidates,
        existing_slugs=existing_slugs,
        batch_size=batch_size,
        cluster_name=cluster_name or "",
    )

    if not selected_candidates:
        return {
            "status": "no_candidates",
            "message": f"No unbuilt candidates found matching strategy '{strategy_name}' (Cluster: {cluster_name}).",
            "pages_generated_count": 0,
            "generated_slugs": [],
            "total_project_pages": len(existing_slugs),
        }

    pipeline = create_default_generation_pipeline(output_dir=pages_dir)
    generated_results: List[GeneratedPageResult] = []

    for idx, cand in enumerate(selected_candidates, start=1):
        logger.info(f"[Wave Progress] Generating page {idx}/{len(selected_candidates)}: '{cand.title}' ({cand.slug})")
        res = pipeline.execute(cand, dry_run=dry_run)
        generated_results.append(res)

    generated_slugs = [r.slug for r in generated_results if r.status == "completed"]
    total_project_pages = len(existing_slugs) + len(generated_slugs)

    logger.info(f"Wave expansion completed! {len(generated_slugs)} new pages generated. Total project pages: {total_project_pages}")

    return {
        "status": "success",
        "strategy_applied": strategy_name,
        "cluster_name": cluster_name,
        "pages_generated_count": len(generated_slugs),
        "generated_slugs": generated_slugs,
        "total_project_pages": total_project_pages,
        "message": f"Successfully generated {len(generated_slugs)} new pages in Wave expansion.",
    }


def run_content_generation_phase(
    dry_run: bool = False,
    target_slug: Optional[str] = None,
    max_pages: Optional[int] = None,
    output_dir: Optional[Path] = None,
    candidates_only: bool = False,
    select_only: bool = False,
    briefs_only: bool = False,
    validate_only: bool = False,
    selection_config: Optional[FirstWaveSelectionConfig] = None,
) -> Dict[str, Any]:
    """
    Main entry point for v0.3 Content Generation & Validation Phase.
    Supports candidate building, selection, brief generation, and validation-only workflows.
    """
    configure_logging()
    out_dir = output_dir or V03_OUTPUTS_DIR
    pages_dir = out_dir / "pages"
    out_dir.mkdir(parents=True, exist_ok=True)
    pages_dir.mkdir(parents=True, exist_ok=True)

    artifacts = load_all_pipeline_inputs()

    # 1. Validate-only mode
    if validate_only:
        gen_content_file = out_dir / "generated_content.json"
        briefs_file = out_dir / "content_briefs.json"
        if not gen_content_file.exists():
            raise FileNotFoundError(f"Cannot validate: {gen_content_file} does not exist.")
        if not briefs_file.exists():
            raise FileNotFoundError(f"Cannot validate: {briefs_file} does not exist.")

        with open(gen_content_file, "r", encoding="utf-8") as f:
            gen_data = json.load(f)
        with open(briefs_file, "r", encoding="utf-8") as f:
            b_data = json.load(f)

        val_payload, val_path = perform_full_content_validation(
            gen_data, b_data, artifacts, out_dir / "content_validation.json"
        )
        return {
            "status": "success",
            "mode": "validate_only",
            "content_validation_file": str(val_path),
            "summary": val_payload["summary"],
        }

    # 2. Build and save normalized page candidates
    candidates_manifest = build_unified_page_candidates(artifacts)
    candidates_file = save_page_candidates(candidates_manifest, out_dir / "page_candidates.json")

    if candidates_only:
        return {
            "status": "success",
            "mode": "candidates_only",
            "page_candidates_file": str(candidates_file),
            "total_candidates": len(candidates_manifest.candidates),
        }

    # 3. First-Wave Page Selection (10–20 pages)
    cfg = selection_config or FirstWaveSelectionConfig(
        max_pages=max_pages or 20,
    )
    selection_manifest = select_first_wave_pages(candidates_manifest, cfg)
    selected_file = save_selected_pages(selection_manifest, out_dir / "selected_pages.json")

    if select_only:
        return {
            "status": "success",
            "mode": "select_only",
            "page_candidates_file": str(candidates_file),
            "selected_pages_file": str(selected_file),
            "total_selected": len(selection_manifest.selected_pages),
        }

    # 4. Generate Structured Content Briefs
    briefs_manifest, briefs_file = generate_all_content_briefs(
        selected_manifest=selection_manifest,
        candidates_manifest=candidates_manifest,
        dry_run=dry_run,
        output_path=out_dir / "content_briefs.json",
    )

    if briefs_only:
        return {
            "status": "success",
            "mode": "briefs_only",
            "content_briefs_file": str(briefs_file),
            "total_briefs": len(briefs_manifest.get("briefs", [])),
        }

    # 5. Compile page contexts from selected candidates & match with briefs
    candidate_map = {c.candidate_id: c for c in candidates_manifest.candidates}
    briefs_map = {b["page_id"]: b for b in briefs_manifest.get("briefs", [])}

    page_contexts = [
        PageContext(candidate=candidate_map[p.candidate_id])
        for p in selection_manifest.selected_pages
        if p.candidate_id in candidate_map
    ]

    if target_slug:
        page_contexts = [c for c in page_contexts if c.slug == target_slug or c.slug.strip("/") == target_slug.strip("/")]

    # 6. Process and draft pages
    results: List[GeneratedPageResult] = []
    for idx, ctx in enumerate(page_contexts, start=1):
        logger.info(f"[Page {idx}/{len(page_contexts)}] Generating '{ctx.title}'...")
        matched_brief = briefs_map.get(ctx.page_id) or generate_structured_content_brief(ctx, dry_run=dry_run)
        res = process_single_page_from_brief(ctx, matched_brief, dry_run=dry_run)
        save_page_artifacts(res, pages_dir)
        results.append(res)

    # 7. Export Generated Content JSON, Manifest & Summary Report
    generated_content_path = export_generated_content_json(results, briefs_manifest, out_dir)
    manifest_path = export_content_manifest(results, out_dir)
    report_path = generate_v03_summary_report(results, out_dir)

    # 8. Run Content Validation Engine
    with open(generated_content_path, "r", encoding="utf-8") as f:
        gen_content_data = json.load(f)
    val_payload, validation_path = perform_full_content_validation(
        gen_content_data, briefs_manifest, artifacts, out_dir / "content_validation.json"
    )

    return {
        "status": "success",
        "total_processed": len(results),
        "completed": len([r for r in results if r.status == "completed"]),
        "page_candidates_file": str(candidates_file),
        "selected_pages_file": str(selected_file),
        "content_briefs_file": str(briefs_file),
        "generated_content_file": str(generated_content_path),
        "content_validation_file": str(validation_path),
        "validation_summary": val_payload["summary"],
        "manifest_path": str(manifest_path),
        "report_path": str(report_path),
        "output_directory": str(out_dir),
    }


def main():
    """Command-line interface for running the v0.3 content generation pipeline."""
    parser = argparse.ArgumentParser(description="v0.3 Content Generation & Validation Pipeline")
    parser.add_argument("--candidates-only", action="store_true", help="Build and save page_candidates.json")
    parser.add_argument("--select-only", action="store_true", help="Run First-Wave page selection only")
    parser.add_argument("--briefs-only", action="store_true", help="Generate content_briefs.json only")
    parser.add_argument("--validate-only", action="store_true", help="Run content validation on existing pages")
    parser.add_argument("--export-frontend", action="store_true", help="Export to Next.js components")
    parser.add_argument("--min-pages", type=int, default=10, help="Min pages to select in First Wave")
    parser.add_argument("--max-pages", type=int, default=20, help="Max pages to select in First Wave")
    parser.add_argument("--target-pages", type=int, default=None, help="Exact target pages")
    parser.add_argument("--dry-run", action="store_true", help="Run in dry-run template mode")
    parser.add_argument("--slug", type=str, default=None, help="Generate for specific slug")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")

    args = parser.parse_args()
    if args.verbose:
        configure_logging(logging.DEBUG)

    selection_config = FirstWaveSelectionConfig(
        min_pages=args.min_pages,
        max_pages=args.max_pages,
        target_count=args.target_pages,
    )

    try:
        outcome = run_content_generation_phase(
            dry_run=args.dry_run,
            target_slug=args.slug,
            max_pages=args.max_pages,
            candidates_only=args.candidates_only,
            select_only=args.select_only,
            briefs_only=args.briefs_only,
            validate_only=args.validate_only,
            selection_config=selection_config,
        )

        if args.export_frontend:
            from phases.v03_export_frontend import ExportConfig, export_frontend_components, load_pages_from_directory
            pages_dir = Path(__file__).resolve().parent.parent / "outputs" / "v03" / "pages"
            pages = load_pages_from_directory(pages_dir)
            cfg = ExportConfig(non_interactive=True)
            export_frontend_components(pages, cfg)
    except Exception as e:
        logger.error(f"Pipeline execution aborted: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
