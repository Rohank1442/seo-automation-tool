"""
v0.3 Content Generation & Validation — Top-Level Facade & Public API.

Re-exports core functions and domain models so existing CLI scripts and API routes
continue to work without breaking changes:
- `run_content_generation_phase`: First-wave 10-20 page generation.
- `generate_additional_wave`: Multi-wave expansion engine supporting Option A and Option B.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from phases.v03.candidate_loader import (
    build_unified_page_candidates,
    load_all_pipeline_inputs,
    save_page_candidates,
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
from phases.v03.pipeline import create_default_generation_pipeline
from phases.v03.selection import (
    CandidateSelectionStrategy,
    NextBestStrategy,
    SpecificClusterStrategy,
    StrategyFactory,
    score_page_candidate,
)
from phases.v03.validator import (
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


def generate_additional_wave(
    strategy_name: str = "next_best",
    batch_size: int = 25,
    cluster_name: Optional[str] = None,
    dry_run: bool = False,
    output_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Executes a multi-wave page expansion batch (e.g. 25-50 pages) without touching
    already published pages. Supports Strategy Pattern:
    - Option A: 'next_best'
    - Option B: 'specific_cluster'
    """
    configure_logging()
    out_dir = output_dir or V03_OUTPUTS_DIR
    pages_dir = out_dir / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting Multi-Wave Expansion: Strategy='{strategy_name}' | Batch={batch_size} | Cluster='{cluster_name}'")

    # 1. Load artifacts and unified candidates
    artifacts = load_all_pipeline_inputs()
    candidates_manifest = build_unified_page_candidates(artifacts)

    # 2. Identify already generated pages to prevent duplicates
    existing_slugs = load_existing_page_slugs(pages_dir)
    logger.info(f"Found {len(existing_slugs)} already generated pages on disk.")

    # 3. Strategy Pattern: Select the candidates for this wave
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

    # 4. Pipeline Pattern: Execute generation on each candidate
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
    **kwargs,
) -> Dict[str, Any]:
    """
    Main legacy entry point for First-Wave content generation.
    Generates the initial 10-20 pages and sets up base outputs.
    """
    configure_logging()
    out_dir = output_dir or V03_OUTPUTS_DIR
    pages_dir = out_dir / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)

    artifacts = load_all_pipeline_inputs()
    candidates_manifest = build_unified_page_candidates(artifacts)
    save_page_candidates(candidates_manifest, out_dir / "page_candidates.json")

    existing_slugs = set() if not target_slug else load_existing_page_slugs(pages_dir) - {target_slug}

    strategy = NextBestStrategy()
    batch = max_pages or 10
    selected = strategy.select(candidates_manifest.candidates, existing_slugs=existing_slugs, batch_size=batch)

    if target_slug:
        selected = [c for c in candidates_manifest.candidates if c.slug == target_slug]

    pipeline = create_default_generation_pipeline(output_dir=pages_dir)
    results = [pipeline.execute(cand, dry_run=dry_run) for cand in selected]

    return {
        "status": "success",
        "total_processed": len(results),
        "completed": len([r for r in results if r.status == "completed"]),
        "pages_saved_in": str(pages_dir),
    }
